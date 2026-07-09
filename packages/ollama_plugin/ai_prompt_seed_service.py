"""Seed AI prompt documents and built-in action bindings."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path

from .ai_prompt_repository import PromptRepository

logger = logging.getLogger(__name__)

VARIABLE_PATTERN = re.compile(r"\{\{([A-Z_]+)\}\}")


@dataclass(frozen=True)
class SeedPromptSpec:
    prompt_doc_id: str
    title: str
    description: str
    source_file: str
    required_variables: tuple[str, ...]
    sort_order: int
    source_type: str = "default"
    readonly: int = 0


class PromptSeedService:
    """Seeds default prompts and built-in actions into the AI prompt database."""

    DB_FILENAME = "ai_prompts.db"
    DB_VERSION = "1"

    _seeded_paths: set[str] = set()
    _seed_lock = threading.Lock()
    _default_settings_service = None

    DEFAULT_PROMPTS: tuple[SeedPromptSpec, ...] = ()

    DEFAULT_ACTIONS: tuple[dict, ...] = ()

    @classmethod
    def set_default_settings_service(cls, settings_service) -> None:
        cls._default_settings_service = settings_service

    def __init__(self, app_data_dir: Path, prompt_package_dir: Path | None = None, settings_service=None):
        self._app_data_dir = Path(app_data_dir)
        self._prompt_dir = self._app_data_dir / "ai"
        self._db_path = self._prompt_dir / self.DB_FILENAME
        self._package_prompt_dir = prompt_package_dir or Path(__file__).parent / "prompts"
        self._repo = PromptRepository(self._db_path)
        self._settings_service = settings_service if settings_service is not None else self._default_settings_service

    @property
    def repository(self) -> PromptRepository:
        return self._repo

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _is_db_missing_or_empty(self) -> bool:
        """Check if DB is missing or has no data."""
        if not self._db_path.exists():
            return True
        action_ids = self._repo.get_action_ids()
        prompt_ids = self._repo.get_prompt_doc_ids()
        return len(action_ids) == 0 and len(prompt_ids) == 0

    def _try_json_bootstrap(self) -> tuple[bool, list[str]]:
        """Try JSON bootstrap. Returns (success, category_list)."""
        from .ai_prompt_bootstrap_service import PromptBootstrapService

        bootstrap = PromptBootstrapService()
        data = bootstrap.load_json_pack()
        if data is None:
            return False, []

        actions = data.get("actions", [])
        prompts = data.get("prompts", [])

        # Extract unique categories from actions (always extract for category reset)
        categories = sorted(set(action.get("category", "") for action in actions if action.get("category")))
        categories = [c for c in categories if c]  # Remove empty strings

        if not actions and not prompts:
            logger.info("[PromptBootstrap] JSON prompt pack has no actions/prompts. Use built-in seed fallback.")
            return False, categories

        error = bootstrap.validate_pack(data)
        if error:
            logger.warning(f"[PromptBootstrap] Failed JSON bootstrap: {error}. Use built-in seed fallback.")
            return False, categories

        try:
            self._repo.ensure_schema()
            with self._repo._connect() as conn:
                for prompt in prompts:
                    record = bootstrap.convert_prompt(prompt)
                    self._repo.upsert_prompt_document(record)

                for action in actions:
                    record = bootstrap.convert_action(action)
                    self._repo.upsert_action(record)

                bindings = bootstrap.get_bindings(actions, prompts)
                for action_id, prompt_doc_id in bindings:
                    self._repo.set_binding(action_id, prompt_doc_id)

            logger.info(
                f"[PromptBootstrap] Completed JSON bootstrap: actions={len(actions)}, prompts={len(prompts)}, bindings={len(bindings)}, categories={len(categories)}"
            )
            return True, categories
        except Exception as e:
            logger.warning(f"[PromptBootstrap] Failed JSON bootstrap: {e}. Use built-in seed fallback.")
            return False, categories

    def ensure_seeded(self) -> PromptRepository:
        normalized_path = str(self._app_data_dir.resolve())

        with self._seed_lock:
            if normalized_path in self._seeded_paths:
                logger.info(f"[PromptSeedService] Seed already completed for app_data_dir={normalized_path}, skip repeated seed")
                return self._repo

            try:
                self._repo.ensure_schema()

                if self._is_db_missing_or_empty():
                    logger.info("[PromptBootstrap] Prompt DB missing or empty. Start JSON prompt pack bootstrap.")
                    success, categories = self._try_json_bootstrap()
                    # Always reset AI category list when DB is empty (replace existing categories)
                    if self._settings_service:
                        self._settings_service.set_ai_category_list(categories)
                        logger.info(f"[PromptSeedService] Reset AI category list: {categories}")
                    if success:
                        self._seeded_paths.add(normalized_path)
                        return self._repo

                for action in self.DEFAULT_ACTIONS:
                    self._repo.upsert_action(action)
                self._seed_prompt_documents()
                self._seed_bindings()
                logger.info(
                    f"[PromptSeedService] Seed import completed: "
                    f"default_actions={len(self.DEFAULT_ACTIONS)}, "
                    f"default_prompts={len(self.DEFAULT_PROMPTS)}"
                )
                self._validate_seed_integrity()
                self._seeded_paths.add(normalized_path)
            except Exception:
                raise

        return self._repo

    def _validate_seed_integrity(self) -> dict[str, Any]:
        """Validate that all default actions, prompts, and bindings exist in DB.

        Returns a dict with validation results:
        - ok: bool - True if all checks pass
        - missing_actions: list - action_ids missing from DB
        - missing_prompts: list - prompt_doc_ids missing from DB
        - missing_bindings: list - action_ids missing bindings
        - broken_bindings: list - action_ids where binding points to non-existent prompt
        - default_actions_count: int
        - default_prompts_count: int
        - warnings: list
        """
        result: dict[str, Any] = {
            "ok": True,
            "missing_actions": [],
            "missing_prompts": [],
            "missing_bindings": [],
            "broken_bindings": [],
            "default_actions_count": len(self.DEFAULT_ACTIONS),
            "default_prompts_count": len(self.DEFAULT_PROMPTS),
            "warnings": [],
        }

        db_action_ids = set(self._repo.get_action_ids())
        db_prompt_ids = set(self._repo.get_prompt_doc_ids())
        binding_map = self._repo.get_binding_map()

        expected_action_ids = {action["action_id"] for action in self.DEFAULT_ACTIONS}
        expected_prompt_ids = {prompt.prompt_doc_id for prompt in self.DEFAULT_PROMPTS}

        missing_actions = expected_action_ids - db_action_ids
        if missing_actions:
            result["ok"] = False
            result["missing_actions"] = sorted(missing_actions)
            result["warnings"].append(f"Missing actions: {sorted(missing_actions)}")

        # Only check for missing prompts if DEFAULT_PROMPTS is not empty
        if expected_prompt_ids:
            missing_prompts = expected_prompt_ids - db_prompt_ids
            if missing_prompts:
                result["ok"] = False
                result["missing_prompts"] = sorted(missing_prompts)
                result["warnings"].append(f"Missing prompts: {sorted(missing_prompts)}")

        for action_id in expected_action_ids:
            if action_id not in binding_map:
                result["ok"] = False
                result["missing_bindings"].append(action_id)
            elif binding_map.get(action_id) not in db_prompt_ids:
                result["ok"] = False
                result["broken_bindings"].append(action_id)

        if result["missing_bindings"]:
            result["warnings"].append(f"Missing bindings: {result['missing_bindings']}")
        if result["broken_bindings"]:
            result["warnings"].append(f"Broken bindings: {result['broken_bindings']}")

        if result["ok"]:
            logger.info(
                f"[PromptSeedService] Seed integrity OK: "
                f"actions={len(self.DEFAULT_ACTIONS)}, "
                f"prompts={len(expected_prompt_ids)}, "
                f"bindings={len(expected_action_ids)}"
            )
        else:
            logger.warning(
                f"[PromptSeedService] Seed integrity warning: "
                f"missing_actions={result['missing_actions']}, "
                f"missing_prompts={result['missing_prompts']}, "
                f"missing_bindings={result['missing_bindings']}, "
                f"broken_bindings={result['broken_bindings']}"
            )

        return result

    def _seed_bindings(self) -> None:
        """Seed bindings with user protection."""
        # Skip if no default prompts
        if not self.DEFAULT_PROMPTS:
            logger.info("[PromptSeedService] Skip binding seed: no default prompts")
            return

        for action in self.DEFAULT_ACTIONS:
            action_id = action["action_id"]
            existing_binding = self._repo.get_binding(action_id)

            # Check if existing binding points to user-created prompt
            if existing_binding:
                bound_prompt_id = existing_binding.get("prompt_doc_id")
                if bound_prompt_id:
                    prompt = self._repo.get_prompt_document(bound_prompt_id)
                    # Protect user prompts
                    if prompt and prompt.get("source_type") == "user":
                        logger.info(
                            f"[PromptSeedService] Skip user binding: action_id={action_id}, "
                            f"prompt_doc_id={bound_prompt_id}, source_type=user"
                        )
                        continue
                    # Protect valid existing bindings (even if pointing to different default prompt)
                    # User may have intentionally selected a different default prompt
                    if prompt:
                        logger.info(
                            f"[PromptSeedService] Preserve existing binding: action_id={action_id}, "
                            f"prompt_doc_id={bound_prompt_id}"
                        )
                        continue

            # Only reset binding if there's no existing binding or target prompt is missing
            self._repo.reset_binding(action_id)
            logger.info(f"[PromptSeedService] Reset default binding: action_id={action_id}")

    def _seed_prompt_documents(self) -> None:
        for prompt in self.DEFAULT_PROMPTS:
            source_path = self._package_prompt_dir / prompt.source_file
            if not source_path.exists():
                logger.warning(f"[PromptSeedService] Missing default prompt file: {source_path}")
                continue

            content_md = source_path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(content_md.encode("utf-8")).hexdigest()
            variables = sorted(set(VARIABLE_PATTERN.findall(content_md)))
            existing = self._repo.get_prompt_document(prompt.prompt_doc_id)

            # Check content_hash to skip unnecessary updates
            if existing and existing.get("content_hash") == content_hash:
                logger.info(
                    f"[PromptSeedService] Skip unchanged prompt: prompt_doc_id={prompt.prompt_doc_id}, "
                    f"content_hash_unchanged=True"
                )
                continue

            # Log operation
            is_new = existing is None
            if is_new:
                logger.info(f"[PromptSeedService] Insert default prompt: prompt_doc_id={prompt.prompt_doc_id}")
            else:
                logger.info(
                    f"[PromptSeedService] Update default prompt: prompt_doc_id={prompt.prompt_doc_id}, "
                    f"content_hash_changed=True"
                )

            # archived is not set here - repository will preserve existing value via COALESCE
            self._repo.upsert_prompt_document({
                "prompt_doc_id": prompt.prompt_doc_id,
                "title": prompt.title,
                "description": prompt.description,
                "content_md": content_md,
                "source_type": prompt.source_type,
                "readonly": prompt.readonly,
                "archived": None,  # Let repository preserve existing value
                "variables_json": json.dumps(variables, ensure_ascii=False),
                "content_hash": content_hash,
            })

    def seed_from_package_files(self) -> PromptRepository:
        return self.ensure_seeded()
