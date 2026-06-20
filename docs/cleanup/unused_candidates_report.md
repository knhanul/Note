# 누니노트 미사용 코드/리소스 후보 분석 보고서

## 1. 분석 개요

- 분석 일시
  - 2026-06-20
- 분석 대상 루트
  - `E:\Pjt\Note`
- 주요 진입점
  - `apps/work_ai_editor/main.py`
  - `apps/work_ai_editor/main_posid.py`
  - `main.py`
  - 보조 엔트리포인트로 문서/테스트에 남아 있는 `apps/markdown_editor/main.py`, `apps/special_editor/main.py`
- 분석 방식
  - 프로젝트 루트 파일 트리 확인
  - 진입점 및 `app_bootstrap.py` 기준 Python import / contextProperty 확인
  - QML 컴포넌트명, 리소스 파일명, JSON/프롬프트 파일명 참조 검색
  - 동적 로딩 가능성이 있는 영역(`contextProperty`, prompt loader, spec datas, QML module/qmldir`)은 보수적으로 판단
  - `build/`, `dist/`, `__pycache__/`, 로컬 점검 스크립트 등 산출물/임시물 분리
- 주의사항
  - 본 보고서는 **삭제 후보 리스트**이며 실제 삭제 작업이 아님
  - QML Loader/문자열 경로/동적 속성 연결 가능성이 있는 항목은 `검토 필요` 또는 `삭제 후보 중간`으로 분류
  - 문서에만 남아 있는 항목과 런타임에서 실제 사용하는 항목을 구분해 기록

## 2. 요약

| 분류 | 개수 | 설명 |
| -- | --: | -- |
| 삭제 후보 높음 | 21 | 백업/임시/구버전 파일, 참조 0인 QML/리소스, 생성 산출물 |
| 삭제 후보 중간 | 7 | 직접 참조는 거의 없지만 호환성/공용 모듈 가능성이 남아 있는 항목 |
| 검토 필요 | 4 | 동적 연결 또는 공개 API/계약 흔적이 있어 바로 삭제 판단하기 어려운 항목 |
| 삭제 금지 확인 | 16 | 진입점, 핵심 QML, AI/RAG, export/import, 프롬프트 로더 등 핵심 경로 |

## 3. 삭제 후보 높음

| 유형 | 경로 | 근거 | 위험도 | 비고 |
| -- | -- | -- | -- | -- |
| QML 백업 | `qml/Main_backup.qml` | 현재 진입점은 `qml/Main.qml`만 사용. 소스 검색상 런타임 참조 없음. `check_backup.py`만 이 파일을 읽음. PyInstaller datas로 통째로 포함되어 번들만 비대화됨. | 낮음 | 삭제 전 `build_posid.spec` 번들 산출물만 확인 |
| QML 백업 | `qml/components/AIAssistantPanel.qml.backup_20260613_1336` | 현재 `AIAssistantPanel.qml`이 사용되며 백업 파일명 자체로 참조 없음. build TOC에는 데이터로 포함됨. | 낮음 | 단순 백업본으로 판단 |
| 임시 diff | `qml/components/AIAssistantPanel.qml.pre_restore.diff` | QML module/qmldir에 등록되지 않았고 참조 검색 없음. build TOC에 데이터로 포함됨. | 낮음 | 복구 메모용 산출물로 보임 |
| 점검 스크립트 | `check_4398.py` | 참조 검색 0. 경로도 `E:\Pjt\Note2\qml\Main.qml`을 가리켜 현재 프로젝트와 불일치. | 낮음 | 과거 수동 디버깅 스크립트 |
| 점검 스크립트 | `check_backup.py` | 참조 검색 0. `qml/Main_backup.qml` 인코딩 확인용 단발성 스크립트. | 낮음 | 백업 파일 검사용 |
| 점검 스크립트 | `check_braces.py` | 참조 검색 0. 루트 단독 스크립트. | 낮음 | 수동 문법 점검용 추정 |
| 점검 스크립트 | `check_current.py` | 참조 검색 0. 루트 단독 스크립트. | 낮음 | 수동 점검용 추정 |
| 점검 스크립트 | `check_depth.py` | 참조 검색 0. 루트 단독 스크립트. | 낮음 | 수동 점검용 추정 |
| 점검 스크립트 | `check_start_depth.py` | 참조 검색 0. 루트 단독 스크립트. | 낮음 | 수동 점검용 추정 |
| 점검 스크립트 | `depth_check.py` | 참조 검색 0. 루트 단독 스크립트. | 낮음 | 수동 점검용 추정 |
| 수동 테스트 스크립트 | `test_ai_action.py` | `tests/` 아래 정식 테스트가 아니고 참조 0. 임시 temp dir를 직접 생성하는 수동 점검 스크립트. | 낮음 | pytest/unittest 체계 밖 |
| 수동 테스트 스크립트 | `test_ai_action2.py` | 위와 동일. 참조 0, 루트 단독 실행 스크립트. | 낮음 | 수동 DB 확인용 |
| QML 컴포넌트 | `qml/components/PromptManagementPanel.qml` | 전체 검색에서 컴포넌트명/파일명 참조 0. `qmldir`에도 미등록. 현재 AI 프롬프트 관리 UI는 `AISettingsDialog.qml` + `AIActionManagementPanel.qml` + 메인 에디터 흐름으로 보임. | 중간 | 문서 설계안(`docs/ai_prompt_management_ui_design.md`)과 비교 확인 후 삭제 검토 |
| QML 컴포넌트 | `qml/components/FallbackWebNoteEditor.qml` | 전체 검색에서 파일명/컴포넌트명 참조 0. `qmldir` 미등록. 현재 편집기는 `WebNoteEditor.qml` 사용. | 낮음 | 과거 fallback 설계 잔재 가능성 높음 |
| 아이콘 리소스 | `qml/assets/icons/app_settings.svg` | 소스/QML/문서 검색 0. 현재 설정 버튼은 `AppHeader` 시그널로 처리되며 이 아이콘명은 참조되지 않음. | 낮음 | 동적 경로 조합 흔적도 미발견 |
| 아이콘 리소스 | `qml/assets/icons/file_call.png` | 소스/QML/문서 검색 0. | 낮음 | 이미지 자산 후보 |
| 아이콘 리소스 | `qml/assets/icons/sync.svg` | 소스/QML/문서 검색 0. | 낮음 | 이미지 자산 후보 |
| 생성 산출물 | `build/` | PyInstaller 분석 산출물(`*.toc` 등). 소스가 아니라 빌드 결과물. | 낮음 | 로컬 정리 대상 |
| 생성 산출물 | `dist/` | 패키징 출력물 및 런타임 DB/로그 포함 가능. 소스가 아니라 결과물. | 중간 | 배포 검증 후 정리 |
| 생성 산출물 | `**/__pycache__/` | Python 캐시 산출물. 소스 아님. | 낮음 | 일괄 정리 가능 |
| 로컬 환경 | `.venv/` | 로컬 가상환경. 소스 아님. | 중간 | 사용자 로컬 개발환경 여부 확인 후 정리 |

각 항목 공통 확인 포인트:
- 검색된 참조 수 0이어도 build/spec 전체 폴더 포함 때문에 패키징에 섞일 수 있음
- 삭제 전 `python apps/work_ai_editor/main.py`, `python main.py`, PyInstaller 빌드 결과를 재확인 권장

## 4. 삭제 후보 중간

| 유형 | 경로 | 근거 | 위험도 | 확인 필요 사항 |
| -- | -- | -- | -- | -- |
| 레거시 Python 모듈 | `packages/ollama_plugin/prompt_controller.py` | 파일 자체에 deprecated 표기. 현재 런타임은 `ai_prompt_controller.py` 경로를 사용. legacy 모듈 내부 상호참조만 존재. | 중간 | 외부 스크립트/플러그인에서 구 import 경로를 쓰는지 확인 |
| 레거시 Python 모듈 | `packages/ollama_plugin/prompt_service.py` | 파일 자체 deprecated. 현재 표준 경로는 `ai_prompt_service.py`. legacy 체인 내부에서만 사용 흔적. | 중간 | 루트 수동 스크립트 외 외부 호출 여부 확인 |
| 레거시 Python 모듈 | `packages/ollama_plugin/prompt_repository.py` | deprecated. 현재 `ai_prompt_repository.py`가 표준. | 중간 | DB 마이그레이션/외부 도구 구경로 확인 |
| 레거시 Python 모듈 | `packages/ollama_plugin/prompt_seed_service.py` | deprecated. 현재 `ai_prompt_seed_service.py` 사용. | 중간 | 외부 bootstrap 경로 확인 |
| 레거시 Python 모듈 | `packages/ollama_plugin/prompt_manager.py` | `PromptManager` 직접 생성 참조 검색 0. 문서/`__init__.py`에만 남아 있음. 과거 markdown prompt 기반 관리 흔적. | 중간 | 과거 사용자 프롬프트 `.md` 호환성 유지 필요 여부 확인 |
| QML 컴포넌트 | `qml/components/NotebookItem.qml` | 런타임 참조 검색 없음. 다만 `qmldir`에 등록되어 있고 공용 UI 후보 문서에 반복 언급됨. | 중간 | 다른 브랜치/향후 앱(shell)에서 재사용 예정인지 확인 |
| QML 컴포넌트 | `qml/components/SidebarSection.qml` | 런타임 참조 검색 없음. 다만 `qmldir` 등록 + 공용 UI 문서에서 재사용 후보로 분류. | 중간 | 마이그레이션 예정 공용 컴포넌트인지 확인 |

## 5. 검토 필요

| 유형 | 경로 | 애매한 이유 | 확인 방법 |
| -- | -- | -- | -- |
| contextProperty | `app_bootstrap.py`의 `appBrand` | QML 런타임 참조는 찾지 못했지만 문서와 bootstrap contract에 공개 API로 남아 있음. | QML에서 브랜드 분기 추가 계획 여부 및 외부 shell 참조 여부 확인 |
| contextProperty | `app_bootstrap.py`의 `folderControllerReady` | 현재 QML 참조 없음. 다만 문서/테스트에 컨텍스트 계약으로 남아 있음. | 과거 startup race 회피용이었는지 확인 후 제거 여부 결정 |
| contextProperty | `app_bootstrap.py`의 `webEngineAvailable` | 주입은 되지만 현재 QML 소비 흔적 없음. 다만 WebEngine fallback 분기용 설계였을 수 있음. | `WebNoteEditor` 비가용 환경 fallback 계획 존재 여부 확인 |
| 패키지 공개 API | `packages/ollama_plugin/__init__.py`의 legacy re-export 맥락 | 현재 표준 경로는 `ai_prompt_*`지만 패키지 루트에서 일부 legacy/compat 심볼을 계속 공개. 외부 import 사용 여부를 소스 내 검색만으로 확정하기 어려움. | 외부 사용자 스크립트, 배포 문서, 이전 버전 호환성 요구 확인 |

## 6. 삭제 금지 또는 유지 권장

| 유형 | 경로 | 유지 이유 |
| -- | -- | -- |
| 실행 진입점 | `apps/work_ai_editor/main.py` | 현재 주요 실행 진입점 |
| 브랜드 엔트리포인트 | `apps/work_ai_editor/main_posid.py` | `build_posid.spec`가 직접 사용 |
| 패키징 설정 | `apps/work_ai_editor/build_posid.spec` | 현재 PyInstaller 빌드 진입점 |
| 호환 엔트리포인트 | `main.py` | 문서/README/manual regression에 명시된 지원 실행 경로 |
| 앱 부트스트랩 | `app_bootstrap.py` | 모든 앱 공통 contextProperty/QML 초기화 핵심 |
| 메인 QML | `qml/Main.qml` | 실제 UI 루트 |
| 핵심 QML | `qml/components/AIAssistantPanel.qml` | work_ai_editor AI/RAG 핵심 패널 |
| 핵심 QML | `qml/components/AISettingsDialog.qml` | 현재 AI 설정/액션 관리 UI에서 사용 |
| 핵심 QML | `qml/components/AppHeader.qml` | Main.qml에서 사용 |
| 핵심 QML | `qml/components/WebNoteEditor.qml` | 현재 에디터 브리지 핵심 |
| 핵심 QML | `qml/components/NoteEditor.qml` | Main.qml에서 사용 |
| 컨트롤러 | `controllers/tool_controller.py` | `Main.qml`의 HWP 변환 도구/모델 도구 버튼과 연결 |
| 서비스 | `services/hwp_converter.py` | `folder_import_service.py`, `packages/import_export/*`에서 사용 |
| 프롬프트 JSON | `packages/ollama_plugin/default_ai_prompts.json` | `ai_prompt_bootstrap_service.py`에서 직접 로드 |
| RAG 프롬프트 JSON | `packages/ollama_plugin/prompts/rag_answer_prompts.json` | `services/rag_answer_prompt_loader.py`에서 직접 로드 |
| AI 프롬프트 서비스군 | `packages/ollama_plugin/ai_prompt_*.py` | 현재 work_ai_editor prompt/action runtime 핵심 경로 |

## 7. 중복/구버전/백업 파일 후보

| 경로 | 유사 파일 | 판단 근거 | 권장 조치 |
| -- | -- | -- | -- |
| `qml/Main_backup.qml` | `qml/Main.qml` | 백업명, 현재 루트 QML은 `Main.qml`만 사용 | 사람 검토 후 우선 삭제 후보 |
| `qml/components/AIAssistantPanel.qml.backup_20260613_1336` | `qml/components/AIAssistantPanel.qml` | 날짜가 붙은 백업본, 참조 없음 | 우선 삭제 후보 |
| `qml/components/AIAssistantPanel.qml.pre_restore.diff` | `qml/components/AIAssistantPanel.qml` | 임시 diff 파일, QML 모듈 아님 | 우선 삭제 후보 |
| `packages/ollama_plugin/prompt_*.py` | `packages/ollama_plugin/ai_prompt_*.py` | 파일 내부 deprecated 선언 + 현재 표준 경로가 별도 존재 | 바로 삭제보다 호환성 확인 후 정리 |
| `check_*.py`, `depth_check.py` | 없음 | 루트 수동 점검 스크립트 | 우선 삭제 후보 |
| `test_ai_action.py`, `test_ai_action2.py` | `tests/` 정식 테스트군 | 테스트 디렉토리 밖 수동 실행 스크립트 | 우선 삭제 후보 |

## 8. 미사용 리소스 후보

| 리소스 경로 | 참조 검색 결과 | 판단 | 비고 |
| -- | -- | -- | -- |
| `qml/assets/icons/app_settings.svg` | 0 | 삭제 후보 높음 | 현재 설정 UI는 다른 버튼/시그널 경로 사용 |
| `qml/assets/icons/file_call.png` | 0 | 삭제 후보 높음 | 동적 경로 조합 흔적도 미발견 |
| `qml/assets/icons/sync.svg` | 0 | 삭제 후보 높음 | 사용처 미발견 |

참고 유지 권장 리소스:
- `assets/images/nuni/*`, `assets/images/posid/*`: `app_config.py`에서 로고/아이콘으로 사용
- `assets/editor/index.html`: `qml/components/WebNoteEditor.qml`에서 사용
- `qml/assets/icons/print.svg`, `export.svg`, `import.svg`, `note_*`, `editor_mode_*`, `folder_properties.svg` 등: `Main.qml` 또는 `AppHeader.qml`에서 참조 확인

## 9. 미사용 QML 후보

| QML 파일/컴포넌트 | 참조 위치 | 판단 | 비고 |
| -- | -- | -- | -- |
| `qml/components/PromptManagementPanel.qml` | 참조 검색 0 | 삭제 후보 높음 | `qmldir` 미등록, 현재 UI 흐름과 연결점 없음 |
| `qml/components/FallbackWebNoteEditor.qml` | 참조 검색 0 | 삭제 후보 높음 | fallback 설계 잔재로 보임 |
| `qml/components/NotebookItem.qml` | 런타임 참조 없음, 문서만 존재 | 삭제 후보 중간 | 공용 UI 후보로 문서화되어 있어 보수적 판단 필요 |
| `qml/components/SidebarSection.qml` | 런타임 참조 없음, 문서만 존재 | 삭제 후보 중간 | 공용 UI 문서상 재사용 후보 |

추가 메모:
- `AIActionManagementPanel.qml`은 `AISettingsDialog.qml`에서 참조되므로 삭제 후보 아님
- `SaveStatusChip.qml`, `EditorToolbar.qml`, `GlassCard.qml`, `NoteListItem.qml`은 실제 참조 확인됨

## 10. 미사용 Python 후보

| 파일/클래스/함수 | 참조 위치 | 판단 | 비고 |
| -- | -- | -- | -- |
| `check_4398.py` | 참조 0 | 삭제 후보 높음 | 다른 프로젝트 경로(`Note2`)를 읽는 임시 스크립트 |
| `check_backup.py` | 참조 0 | 삭제 후보 높음 | `Main_backup.qml` 확인용 |
| `check_braces.py` | 참조 0 | 삭제 후보 높음 | 수동 점검 스크립트 |
| `check_current.py` | 참조 0 | 삭제 후보 높음 | 수동 점검 스크립트 |
| `check_depth.py` | 참조 0 | 삭제 후보 높음 | 수동 점검 스크립트 |
| `check_start_depth.py` | 참조 0 | 삭제 후보 높음 | 수동 점검 스크립트 |
| `depth_check.py` | 참조 0 | 삭제 후보 높음 | 수동 점검 스크립트 |
| `test_ai_action.py` | 참조 0 | 삭제 후보 높음 | 정식 테스트 체계 밖 수동 테스트 |
| `test_ai_action2.py` | 참조 0 | 삭제 후보 높음 | 정식 테스트 체계 밖 수동 테스트 |
| `packages/ollama_plugin/prompt_controller.py::PromptController` | legacy 내부만 | 삭제 후보 중간 | deprecated 표기, 현재는 `ai_prompt_controller.py` 경로 사용 |
| `packages/ollama_plugin/prompt_service.py::PromptService` | legacy 내부 + 수동 스크립트 | 삭제 후보 중간 | deprecated 표기 |
| `packages/ollama_plugin/prompt_repository.py::PromptRepository` | legacy 내부만 | 삭제 후보 중간 | deprecated 표기 |
| `packages/ollama_plugin/prompt_seed_service.py::PromptSeedService` | legacy 내부만 | 삭제 후보 중간 | deprecated 표기 |
| `packages/ollama_plugin/prompt_manager.py::PromptManager` | 문서/`__init__`만 | 삭제 후보 중간 | 과거 markdown prompt 관리 경로 |

## 11. 삭제 전 권장 확인 절차

- 앱 실행 테스트
  - `python main.py`
  - `python apps/work_ai_editor/main.py`
  - `python apps/markdown_editor/main.py`
  - `python apps/special_editor/main.py`
- 주요 화면 진입 테스트
  - 메인 노트 목록
  - 폴더/템플릿 관련 화면
- 노트 저장/불러오기 테스트
- AI 업무비서 테스트
- 현재문서AI 테스트
- 참고문서AI/RAG 테스트
- 설정 팝업 테스트
- 출력/PDF 관련 테스트
- 문서/HWPX/Excel 입력 테스트
- 패키징/dist 실행 테스트
  - `build_posid.spec`로 빌드 후 실행
  - backup/diff 제거 시 bundle 내 QML 로딩 이상 유무 확인

## 12. 다음 단계 제안

- 1차 삭제 대상
  - QML 백업/임시 파일
  - 루트 점검 스크립트 `check_*`, `depth_check.py`
  - 루트 수동 테스트 스크립트 `test_ai_action*.py`
  - 참조 0 아이콘 3종
  - `PromptManagementPanel.qml`, `FallbackWebNoteEditor.qml`
  - 생성 산출물 `build/`, `dist/`, `__pycache__/`, `.venv/`(로컬 정책 확인 후)
- 보류 대상
  - legacy `prompt_*` 모듈
  - `NotebookItem.qml`, `SidebarSection.qml`
  - `appBrand`, `folderControllerReady`, `webEngineAvailable` contextProperty
- 추가 분석 대상
  - 외부 스크립트/배포 문서에서 legacy prompt API를 사용하는지
  - 향후 `editor_ui` 마이그레이션 계획에서 `NotebookItem.qml`, `SidebarSection.qml`을 사용할 예정인지
  - build spec에서 전체 폴더 수집 대신 whitelist 수집으로 전환 가능한지
- 삭제 전 백업 방법
  - Git branch 분리
  - 삭제 후보만 별도 commit
  - PyInstaller 빌드/수동 회귀 확인 후 단계별 merge

---

## 결과 요약 수치

- 보고서 파일 경로
  - `docs/cleanup/unused_candidates_report.md`
- 삭제 후보 높음 개수
  - 21
- 삭제 후보 중간 개수
  - 7
- 검토 필요 개수
  - 4
- 미사용 리소스 후보 개수
  - 3
- 미사용 QML 후보 개수
  - 4
- 미사용 Python 후보 개수
  - 14
- 삭제하면 위험한 항목
  - `apps/work_ai_editor/main.py`
  - `apps/work_ai_editor/main_posid.py`
  - `apps/work_ai_editor/build_posid.spec`
  - `app_bootstrap.py`
  - `qml/Main.qml`
  - `qml/components/AIAssistantPanel.qml`
  - `qml/components/AISettingsDialog.qml`
  - `qml/components/WebNoteEditor.qml`
  - `packages/ollama_plugin/default_ai_prompts.json`
  - `packages/ollama_plugin/prompts/rag_answer_prompts.json`
  - `packages/ollama_plugin/ai_prompt_*.py`
  - `services/hwp_converter.py`
  - `controllers/tool_controller.py`
- 다음 단계에서 안전하게 삭제하기 위한 순서
  1. backup/diff/점검 스크립트 제거
  2. 참조 0 아이콘 제거
  3. `PromptManagementPanel.qml`, `FallbackWebNoteEditor.qml` 제거
  4. build/dist/__pycache__/로컬 산출물 정리
  5. legacy `prompt_*` 모듈은 별도 브랜치에서 삭제 후 전체 AI 프롬프트/액션 흐름 회귀 테스트
  6. `NotebookItem.qml`, `SidebarSection.qml`, bootstrap contextProperty는 마지막 단계에서 사람 검토 후 결정
