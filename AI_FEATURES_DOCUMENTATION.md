# Note2 AI 기능 및 프롬프트 시스템 문서

## 개요

Note2 프로젝트는 Ollama 기반의 AI 어시스턴트 기능을 제공하며, 사용자가 커스터마이즈 가능한 프롬프트 시스템을 통해 다양한 AI 작업을 수행할 수 있습니다.

## Phase 6 최신 운영 가이드 (권장)

아래 내용은 현재 기준의 최신 동작 규칙입니다. 기존 섹션과 충돌할 경우 이 섹션을 우선 참고하세요.

### AI 기능 vs AI 프롬프트 노트
- AI 기능: 실행 단위(`ai_actions`)로, 이름/정렬/활성화/input_mode/프롬프트 매핑을 관리합니다.
- AI 프롬프트 노트: 실제 프롬프트 본문(`ai_prompt_documents`)을 관리합니다.
- 매핑: `ai_action_prompt_bindings`를 통해 기능과 프롬프트를 연결합니다.

### 관리 위치
- AI 기능 관리: `AI 설정 > AI 기능 관리` 탭
- 프롬프트 연결: `AI 설정 > 프롬프트 연결` 탭
- AI 프롬프트 노트 편집: 메인 화면의 AI 프롬프트 가상 서재(`ai_prompts` 모드)

### input_mode
- `auto`: 프롬프트 변수 분석 결과로 실행 입력 유형을 추론
- `chat_only`: 노트 없이 사용자 입력만으로 실행
- `note_required`: 현재 노트가 있어야 실행
- `note_and_chat`: 현재 노트 + 사용자 입력이 모두 필요
- `selection_required`: 선택 문장이 필요 (미연동 시 안내 메시지 표시)

### 지원 변수
- `CONTENT`
- `SELECTION`
- `QUESTION`
- `USER_INPUT`
- `CHAT_MESSAGE`
- `CHAT_HISTORY`
- `TITLE`
- `TAGS`
- `CONTEXT`

### 보호 정책
- 기본 기능(`source_type=default` 또는 `readonly=1`)은 삭제할 수 없습니다.
- 사용자 기능 삭제는 hard delete가 아니라 archive(`archived=1`) 처리입니다.
- 기본 프롬프트는 직접 수정/삭제하지 않고 `복사해서 수정`으로만 편집합니다.

### 성능 및 모델 권장
- 기본 권장값
  - `timeout=300`, `first_token_timeout=180`, `idle_timeout=60`
  - `num_predict=256~512`, `num_ctx=2048~4096`, `temperature=0.2`, `keep_alive=10m`
- 저사양 권장값
  - `num_predict=256`, `num_ctx=2048`, `keep_alive=5m`
- Q8 모델은 CPU 환경에서 느릴 수 있으므로 Q4 또는 소형 모델(1.5B~2B) 권장

### 오류 메시지 가이드
- 현재 노트를 선택한 뒤 실행해주세요.
- 이 기능은 입력창에 질문이 필요합니다.
- 이 기능은 선택한 문장이 필요합니다.
- 연결된 프롬프트를 찾을 수 없습니다.
- AI 응답 시간이 초과되었습니다. 더 가벼운 모델을 선택하거나 입력 길이를 줄여 다시 시도해보세요.
- 연결 실패: Ollama가 실행 중인지 확인하세요.

### 수동 테스트 체크리스트
- `AI_PHASE6_SMOKE_CHECKLIST.md` 문서를 참고하세요.

## 시스템 아키텍처

### 주요 컴포넌트

```
work_ai_editor (메인 애플리케이션)
├── OllamaAssistantPlugin (플러그인)
│   ├── AssistantController (AI 작업 실행)
│   ├── ActionRegistry (액션 등록 및 관리)
│   ├── AIWorkerManager (백그라운드 작업 관리)
│   └── AISettingsManager (AI 설정 관리)
├── PromptService (프롬프트 비즈니스 로직)
│   ├── PromptRepository (데이터베이스 접근)
│   ├── PromptSeedService (기본 프롬프트 시딩)
│   └── PromptRenderer (프롬프트 렌더링)
├── AIPromptDocumentController (프롬프트 문서 UI 컨트롤러)
└── PromptController (프롬프트 바인딩 UI 컨트롤러)
```

### 데이터베이스 스키마

AI 프롬프트 데이터는 `app_data/ai/ai_prompts.db` SQLite 데이터베이스에 저장됩니다.

#### 테이블 구조

**ai_prompt_documents**
- `prompt_doc_id` (TEXT PRIMARY KEY): 프롬프트 문서 ID
- `title` (TEXT): 프롬프트 제목
- `description` (TEXT): 프롬프트 설명
- `content_md` (TEXT): 프롬프트 내용 (Markdown)
- `source_type` (TEXT): 소스 타입 ("default" 또는 "user")
- `readonly` (INTEGER): 읽기 전용 여부 (0/1)
- `archived` (INTEGER): 아카이브 여부 (0/1)
- `variables_json` (TEXT): 변수 목록 (JSON 배열)
- `content_hash` (TEXT): 내용 해시
- `created_at` (TEXT): 생성 시간
- `updated_at` (TEXT): 수정 시간

**ai_actions**
- `action_id` (TEXT PRIMARY KEY): 액션 ID
- `name` (TEXT): 액션 이름
- `description` (TEXT): 액션 설명
- `category` (TEXT): 카테고리
- `required_variables_json` (TEXT): 필수 변수 목록 (JSON 배열)
- `enabled` (INTEGER): 활성화 여부 (0/1)
- `sort_order` (INTEGER): 정렬 순서

**ai_action_prompt_bindings**
- `action_id` (TEXT): 액션 ID
- `prompt_doc_id` (TEXT): 프롬프트 문서 ID
- `updated_at` (TEXT): 수정 시간
- PRIMARY KEY (action_id, prompt_doc_id)

**ai_prompt_history**
- `history_id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `prompt_doc_id` (TEXT): 프롬프트 문서 ID
- `content_md` (TEXT): 프롬프트 내용
- `created_at` (TEXT): 생성 시간

## 현재 구현된 AI 액션/프롬프트

### 1. current_note_qa (현재 문서 질문)

**목적**: 현재 문서의 내용을 바탕으로 사용자의 질문에 답변

**필수 변수**: `CONTEXT`, `QUESTION`

**프롬프트 내용**:
```markdown
# 현재 문서 질문 프롬프트

다음은 현재 문서에서 관련된 문단들입니다. 이 문단들을 참고하여 사용자의 질문에 답변해주세요.

## 참고 문단

{{CONTEXT}}

## 질문

{{QUESTION}}

## 답변 가이드

- 참고 문단에 있는 정보만 사용하여 답변해주세요.
- 문서에 없는 내용은 "문서에 해당 정보가 없습니다"라고 답변해주세요.
- 가능한 한 간결하고 명확하게 답변해주세요.
- 필요하다면 참고 문단의 번호를 언급해주세요.

## 답변
```

### 2. extract_todo (할 일 추출)

**목적**: 문서에서 수행해야 할 작업이나 할 일 추출

**필수 변수**: `CONTENT`

**프롬프트 내용**:
```markdown
# 할 일 추출 프롬프트

다음 문서에서 수행해야 할 작업이나 할 일을 추출해주세요.
각 할 일은 간단하게 1-2문장으로 작성해주세요.

## 문서 내용

{{CONTENT}}

## 할 일 목록
```

### 3. polish_selection (문장 다듬기)

**목적**: 선택한 텍스트를 읽기 쉽고 자연스럽게 다듬기

**필수 변수**: `CONTENT`

**프롬프트 내용**:
```markdown
# 문장 다듬기 프롬프트

다음 텍스트를 더 읽기 쉽고 자연스럽게 다듬어주세요.
문법 오류가 있으면 수정하고, 불필요한 표현은 제거해주세요.

## 원본 텍스트

{{CONTENT}}

## 다듬은 결과
```

### 4. suggest_title_tags (제목/태그 추천)

**목적**: 문서 내용을 분석하여 적절한 제목과 태그 추천

**필수 변수**: `CONTENT`

**프롬프트 내용**:
```markdown
# 제목/태그 추천 프롬프트

다음 문서의 내용을 분석하여 적절한 제목과 태그를 추천해주세요.

## 문서 내용

{{CONTENT}}

## 추천 제목 (1개)

## 추천 태그 (3-5개)
```

### 5. summarize_note (문서 요약)

**목적**: 문서를 간결하게 요약

**필수 변수**: `CONTENT`

**프롬프트 내용**:
```markdown
# 문서 요약 프롬프트

다음 문서를简要하게 요약해주세요.
요약은 3-5문장 정도로 작성하고, 핵심 내용만 포함해주세요.

## 문서 내용

{{CONTENT}}

## 요약
```

## 프롬프트 변수 시스템

### 지원되는 변수

- `{{CONTENT}}`: 전체 문서 내용
- `{{SELECTION}}`: 사용자가 선택한 텍스트
- `{{QUESTION}}`: 사용자 질문
- `{{TITLE}}`: 문서 제목
- `{{TAGS}}`: 문서 태그
- `{{CONTEXT}}`: 검색된 관련 문단 (RAG)

### 변수 치환

프롬프트 렌더링 시 `{{VARIABLE_NAME}}` 패턴이 실제 값으로 치환됩니다. 필수 변수가 누락된 경우 경고가 표시됩니다.

## 컨트롤러 및 서비스

### AssistantController

AI 작업 실행을 담당하는 메인 컨트롤러입니다.

**주요 기능**:
- AI 작업 실행 및 관리
- 토큰 스트리밍 처리
- RAG (Retrieval-Augmented Generation) 지원
- 설정 관리

**주요 메서드**:
- `runTask(action_id, context)`: 특정 액션 실행
- `cancelTask()`: 실행 중인 작업 취소
- `setNoteController(controller)`: 노트 컨트롤러 설정

### PromptService

프롬프트 문서 및 액션 바인딩의 비즈니스 로직을 담당합니다.

**주요 기능**:
- 프롬프트 문서 CRUD
- 액션-프롬프트 바인딩 관리
- 프롬프트 렌더링
- 변수 유효성 검증

**주요 메서드**:
- `list_actions()`: 모든 액션 목록 반환
- `list_prompt_documents()`: 프롬프트 문서 목록 반환
- `get_effective_prompt(action_id)`: 액션에 대한 유효한 프롬프트 반환
- `render_prompt(action_id, context)`: 프롬프트 렌더링
- `set_binding(action_id, prompt_doc_id)`: 액션-프롬프트 바인딩 설정
- `validate_prompt_for_action(action_id, prompt_doc_id)`: 프롬프트 유효성 검증

### AIPromptDocumentController

메인 에디터 워크스페이스에서 프롬프트 문서 관리를 담당합니다.

**주요 기능**:
- 프롬프트 문서 목록 표시
- 프롬프트 문서 선택 및 로드
- 프롬프트 문서 편집 및 저장
- 프롬프트 문서 복제

**주요 메서드**:
- `loadPromptDocuments()`: 프롬프트 문서 목록 로드
- `selectPromptDocument(prompt_doc_id)`: 프롬프트 문서 선택
- `savePromptDocument(prompt_doc_id, title, content_md)`: 프롬프트 문서 저장
- `duplicatePromptDocument(prompt_doc_id)`: 프롬프트 문서 복제

### PromptController

AI 설정 다이얼로그에서 프롬프트 바인딩 관리를 담당합니다.

**주요 기능**:
- 액션 목록 표시
- 액션-프롬프트 바인딩 관리
- 프롬프트 유효성 검증

## UI 컴포넌트

### Main.qml

메인 에디터 UI입니다.

**주요 컴포넌트**:
- `activeContentMode`: 현재 콘텐츠 모드 ("notes" 또는 "ai_prompts")
- `promptDocumentController`: 프롬프트 문서 컨트롤러
- `notesListView`: 노트/프롬프트 목록 뷰
- AI 프롬프트 서재 전환 기능

### AIAssistantPanel.qml

AI 어시스턴트 패널입니다.

**주요 기능**:
- AI 작업 버튼 표시
- 작업 실행 및 결과 표시
- 토큰 스트리밍

### PromptBindingPanel.qml

프롬프트 바인딩 관리 패널입니다.

**주요 기능**:
- 액션 목록 표시
- 액션-프롬프트 바인딩 설정
- 프롬프트 유효성 검증 표시
- 기본 프롬프트로 복원

## 실행 흐름

### 1. AI 작업 실행

```
사용자가 AI 작업 버튼 클릭
  ↓
AssistantController.runTask(action_id, context)
  ↓
ActionRegistry에서 액션 정보 조회
  ↓
PromptService.get_effective_prompt(action_id)
  ↓
PromptService.render_prompt(action_id, context)
  ↓
AIWorkerManager로 작업 전송
  ↓
Ollama API 호출 및 토큰 스트리밍
  ↓
결과 표시
```

### 2. 프롬프트 관리

```
사용자가 AI 프롬프트 서재 선택
  ↓
Main.qml에서 activeContentMode 변경
  ↓
AIPromptDocumentController.loadPromptDocuments()
  ↓
PromptService.list_prompt_documents()
  ↓
프롬프트 목록 표시
  ↓
사용자가 프롬프트 선택
  ↓
AIPromptDocumentController.selectPromptDocument()
  ↓
메인 에디터에 프롬프트 내용 로드
  ↓
사용자가 프롬프트 편집 후 저장
  ↓
AIPromptDocumentController.savePromptDocument()
  ↓
PromptService.save_prompt_document()
  ↓
데이터베이스 업데이트
```

### 3. 액션-프롬프트 바인딩

```
사용자가 AI 설정 다이얼로그 열기
  ↓
PromptController.loadActions()
  ↓
액션 목록 표시
  ↓
사용자가 액션 선택
  ↓
PromptController.loadBinding(action_id)
  ↓
현재 바인딩된 프롬프트 표시
  ↓
사용자가 다른 프롬프트 선택
  ↓
PromptController.setBinding(action_id, prompt_doc_id)
  ↓
데이터베이스 업데이트
  ↓
바인딩 유효성 검증
```

## 현재 기능

### 1. 프롬프트 관리
- 기본 프롬프트 시딩 (packages/ollama_plugin/prompts/*.md)
- 사용자 프롬프트 생성 및 편집
- 프롬프트 복제
- 프롬프트 아카이빙
- 프롬프트 버전 히스토리

### 2. 액션-프롬프트 바인딩
- 액션별 프롬프트 커스터마이징
- 기본 프롬프트로 복원
- 프롬프트 유효성 검증 (필수 변수 확인)

### 3. AI 작업 실행
- 5가지 기본 AI 작업
- 토큰 스트리밍
- RAG 지원 (문서 검색)
- 작업 취소 기능

### 4. UI
- 메인 에디터에서 프롬프트 편집
- AI 프롬프트 전용 서재
- AI 설정 다이얼로그
- 프롬프트 바인딩 패널

## 제한사항

### 1. 프롬프트 변수
- 현재 6개의 표준 변수만 지원
- 사용자 정의 변수는 지원하지 않음
- 변수 중첩은 지원하지 않음

### 2. 프롬프트 버전 관리
- 히스토리는 저장되지만 UI에서 복구 기능 없음
- 비교 기능 없음

### 3. 프롬프트 공유
- 프롬프트 내보내기/가져오기 기능 없음
- 템플릿 공유 기능 없음

### 4. AI 모델
- Ollama 모델만 지원
- OpenAI API 등 다른 모델은 지원하지 않음

### 5. RAG
- 단순한 키워드 기반 검색만 지원
- 벡터 임베딩 기반 검색은 제한적

## 향후 개선사항

### 1. 프롬프트 기능 향상
- 프롬프트 템플릿 시스템
- 프롬프트 버전 비교 및 복구
- 프롬프트 내보내기/가져오기 (JSON/Markdown)
- 프롬프트 카테고리 및 태깅
- 프롬프트 검색 기능

### 2. 변수 시스템 확장
- 사용자 정의 변수 지원
- 변수 기본값 설정
- 변수 타입 검증
- 변수 설명 및 가이드

### 3. AI 작업 확장
- 더 많은 기본 액션 추가
- 사용자 정의 액션 생성
- 액션 체이닝 (여러 작업 순차 실행)
- 작업 예약

### 4. RAG 향상
- 벡터 임베딩 기반 검색 개선
- 하이브리드 검색 (키워드 + 벡터)
- 검색 결과 재랭킹
- 검색 결과 필터링

### 5. UI/UX 개선
- 프롬프트 편집기 개선 (문법 하이라이팅)
- 프롬프트 미리보기 기능
- 프롬프트 테스트 기능
- 더 나은 에러 메시지

### 6. 멀티모달 지원
- 이미지 처리
- PDF 문서 처리
- 오디오 트랜스크립션

## 기술 스택

- **언어**: Python 3.x
- **UI 프레임워크**: PyQt6, QML
- **AI 백엔드**: Ollama
- **데이터베이스**: SQLite
- **임베딩**: gemma-embed-300m (Ollama)

## 파일 구조

```
packages/ollama_plugin/
├── __init__.py
├── assistant_controller.py
├── action_registry.py
├── ai_controller.py
├── ai_prompt_document_controller.py
├── ai_prompt_repository.py
├── ai_prompt_service.py
├── ai_prompt_seed_service.py
├── ai_settings.py
├── ai_worker.py
├── ai_worker_manager.py
├── model_manager.py
├── plugin.py
├── prompt_renderer.py
├── simple_chunker.py
├── simple_retriever.py
└── prompts/
    ├── current_note_qa.md
    ├── extract_todo.md
    ├── polish_selection.md
    ├── suggest_title_tags.md
    └── summarize_note.md

qml/
├── Main.qml
├── components/
│   ├── AIAssistantPanel.qml
│   └── PromptBindingPanel.qml

app_data/ai/
├── ai_prompts.db
└── ai_settings.json
```

## 참고

- 이 문서는 현재 구현된 기능을 기반으로 작성되었습니다.
- AI 기능은 계속 개선 중입니다.
- 추가적인 기능 요청은 이슈 트래커에 등록해주세요.
