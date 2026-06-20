import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class RagAnswerPrompt:
    id: str
    name: str
    description: str
    recommended_for: list[str]
    system_prompt: str
    user_prompt_template: str


class RagAnswerPromptLoader:
    """Loads and manages RAG answer prompts from JSON file."""
    
    def __init__(self, json_path: Optional[Path] = None):
        self._json_path = json_path or self._get_default_json_path()
        self._prompts: Dict[str, RagAnswerPrompt] = {}
        self._default_prompt_id = "default_answer"
        self._loaded = False
        
    def _get_default_json_path(self) -> Path:
        """Get default path to rag_answer_prompts.json."""
        # Try to find the file relative to this module
        module_dir = Path(__file__).parent
        json_path = module_dir.parent / "packages" / "ollama_plugin" / "prompts" / "rag_answer_prompts.json"
        if json_path.exists():
            return json_path
        
        # Fallback to current directory
        return Path(__file__).parent / "rag_answer_prompts.json"
    
    def load(self) -> bool:
        """Load prompts from JSON file."""
        if self._loaded:
            return True
            
        try:
            if not self._json_path.exists():
                logger.error(f"[RagAnswerPromptLoader] JSON file not found: {self._json_path}")
                return False
                
            with open(self._json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self._default_prompt_id = data.get("default_prompt_id", "default_answer")
            prompts_data = data.get("prompts", [])
            
            for prompt_data in prompts_data:
                prompt = RagAnswerPrompt(
                    id=prompt_data["id"],
                    name=prompt_data["name"],
                    description=prompt_data["description"],
                    recommended_for=prompt_data.get("recommended_for", []),
                    system_prompt=prompt_data["system_prompt"],
                    user_prompt_template=prompt_data["user_prompt_template"]
                )
                self._prompts[prompt.id] = prompt
                
            self._loaded = True
            logger.info(f"[RagAnswerPromptLoader] Loaded {len(self._prompts)} prompts from {self._json_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"[RagAnswerPromptLoader] JSON parsing error: {e}")
            return False
        except Exception as e:
            logger.error(f"[RagAnswerPromptLoader] Failed to load prompts: {e}")
            return False
    
    def get_prompt(self, prompt_id: str) -> Optional[RagAnswerPrompt]:
        """Get prompt by ID. Returns default if not found."""
        if not self._loaded:
            self.load()
            
        prompt = self._prompts.get(prompt_id)
        if prompt is None:
            logger.warning(f"[RagAnswerPromptLoader] Prompt not found: {prompt_id}, using default: {self._default_prompt_id}")
            prompt = self._prompts.get(self._default_prompt_id)
            
        return prompt
    
    def get_default_prompt(self) -> Optional[RagAnswerPrompt]:
        """Get default prompt."""
        if not self._loaded:
            self.load()
        return self._prompts.get(self._default_prompt_id)
    
    def list_prompts(self) -> list[RagAnswerPrompt]:
        """List all available prompts."""
        if not self._loaded:
            self.load()
        return list(self._prompts.values())
    
    def get_prompt_ids(self) -> list[str]:
        """Get all prompt IDs."""
        if not self._loaded:
            self.load()
        return list(self._prompts.keys())
    
    def build_user_prompt(
        self, 
        prompt_id: str, 
        user_input: str, 
        rag_context: str, 
        rag_sources: str
    ) -> tuple[str, str]:
        """
        Build system and user prompts with variable substitution.
        
        Returns:
            (system_prompt, user_prompt) tuple
        """
        prompt = self.get_prompt(prompt_id)
        if prompt is None:
            # Fallback to basic prompt
            logger.error(f"[RagAnswerPromptLoader] No prompt available for {prompt_id}, using fallback")
            return self._build_fallback_prompts(user_input, rag_context, rag_sources)
        
        user_prompt = prompt.user_prompt_template
        user_prompt = user_prompt.replace("{{USER_INPUT}}", user_input)
        user_prompt = user_prompt.replace("{{RAG_CONTEXT}}", rag_context)
        user_prompt = user_prompt.replace("{{RAG_SOURCES}}", rag_sources)
        
        return prompt.system_prompt, user_prompt
    
    def _build_fallback_prompts(
        self, 
        user_input: str, 
        rag_context: str, 
        rag_sources: str
    ) -> tuple[str, str]:
        """Build fallback prompts when JSON loading fails."""
        system_prompt = "당신은 제공된 참고문서를 바탕으로 답변하는 AI 어시스턴트입니다. 참고문서에 없는 내용은 추측하지 말고 \"참고문서에서 확인되지 않습니다\"라고 답하세요. 가능한 경우 핵심 문장 끝에 [S1], [S2]처럼 출처를 표시하고, 문장에 넣기 어렵다면 마지막에 \"참고 출처\" 섹션을 추가하세요. 검색된 참고문서를 먼저 요약하고, 필요하면 마지막에 추가 질문을 제안하세요."
        
        user_prompt = f"""## 사용자 질문

{user_input}

## 참고문서 검색 결과

{rag_context}

## 참고문서 출처

{rag_sources}

## 답변 지시

위 참고문서 내용을 바탕으로 사용자 질문에 답변하세요. 가능하면 핵심 문장 끝에 [S1] 형식의 출처를 붙이고, 출처를 문장에 넣기 어렵다면 마지막에 "참고 출처" 섹션을 반드시 포함하세요."""
        
        return system_prompt, user_prompt
    
    def is_loaded(self) -> bool:
        """Check if prompts are loaded."""
        return self._loaded
