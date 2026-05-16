# AI 프롬프트 관리 UI 설계 문서

## 1. 프로젝트 개요

### 1.1 목표
AI 기능별 프롬프트를 마크다운 파일로 관리하고 사용자가 쉽게 수정할 수 있는 UI를 구축합니다.

### 1.2 현재 상황
- 프롬프트는 `packages/ollama_plugin/prompts/` 디렉토리에 마크다운 파일로 저장
- 사용자 오버라이드는 `app_data/ai/prompts/` 디렉토리에 저장
- 프롬프트 관리자(PromptManager)가 기본 프롬프트와 사용자 프롬프트를 관리
- 현재는 프로그래머만 프롬프트를 수정 가능

## 2. 현재 시스템 구조

### 2.1 프롬프트 관리 시스템

#### PromptManager 클래스
```python
# packages/ollama_plugin/prompt_manager.py

class PromptManager:
    DEFAULT_PROMPTS_DIR = Path(__file__).parent / "prompts"
    
    def __init__(self, user_prompts_dir: Path | None = None, app_data_dir: Path | None = None):
        # 사용자 프롬프트 디렉토리: app_data/ai/prompts
        # 기본 프롬프트 디렉토리: packages/ollama_plugin/prompts
    
    def get_prompt(self, prompt_name: str) -> str:
        # 사용자 프롬프트 우선, 없으면 기본 프롬프트 사용
    
    def save_user_prompt(self, prompt_name: str, content: str) -> bool:
        # 사용자 프롬프트 저장
    
    def list_available_prompts(self) -> list[str]:
        # 사용 가능한 프롬프트 목록
    
    def has_user_override(self, prompt_name: str) -> bool:
        # 사용자 오버라이드 존재 여부 확인
    
    def reset_to_default(self, prompt_name: str) -> bool:
        # 기본 프롬프트로 리셋
```

### 2.2 현재 프롬프트 파일 목록

```
packages/ollama_plugin/prompts/
├── current_note_qa.md       # 현재 문서 질문
├── extract_todo.md          # 할 일 추출
├── polish_selection.md      # 선택 문장 다듬기
├── suggest_title_tags.md    # 제목/태그 추천
└── summarize_note.md        # 문서 요약
```

### 2.3 프롬프트 파일 구조 예시

```markdown
# 문서 요약 프롬프트

다음 문서를 간략하게 요약해주세요.
요약은 3-5문장 정도로 작성하고, 핵심 내용만 포함해주세요.

## 문서 내용

{{CONTENT}}

## 요약
```

### 2.4 AI 에디터 현재 구조

#### AIAssistantPanel (qml/components/AIAssistantPanel.qml)
- 빠른 실행 버튼: 요약, 다듬기, 할 일 추출, 제목/태그 추천
- 현재 문서 질문 기능
- 결과 미리보기
- 연결 상태 표시
- 모델 설정 버튼

#### AISettingsDialog (qml/components/AISettingsDialog.qml)
- 모델 선택 (LLM, Embedding)
- 성능 모드 선택
- 프롬프트 관리 탭 (현재 비어있음)

## 3. 제안하는 UI 구조

### 3.1 프롬프트 관리 다이얼로그

#### 메인 레이아웃
```
┌─────────────────────────────────────────┐
│  프롬프트 관리                    [닫기]  │
├─────────────────────────────────────────┤
│  ┌─────┬─────────────────────────────┐  │
│  │ 목록│  프롬프트 편집기            │  │
│  │     │                             │  │
│  │ • 요약│  # 문서 요약 프롬프트      │  │
│  │   ✓  │                             │  │
│  │ • 다듬기│  다음 문서를 간략하게...  │  │
│  │   ✓  │                             │  │
│  │ • 할 일│  ## 문서 내용             │  │
│  │       │                             │  │
│  │ • 질문│  {{CONTENT}}              │  │
│  │   ✓  │                             │  │
│  │ • 태그│  ## 요약                   │  │
│  │       │                             │  │
│  │      │  [변수 미리보기]            │  │
│  │      │  • {{CONTENT}}: 문서 내용  │  │
│  │      │  • {{SELECTION}}: 선택 텍 │  │
│  │      │    스트                     │  │
│  │      │                             │  │
│  │      │  [기본으로 복원] [저장]    │  │
│  └─────┴─────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 3.2 프롬프트 목록 패널

#### 기능
- 프롬프트 목록 표시
- 사용자 오버라이드 여부 표시 (✓ 마크)
- 선택 시 편집기에 로드
- 검색/필터링 기능

#### UI 요소
```qml
ListView {
    model: promptListModel
    
    delegate: Rectangle {
        RowLayout {
            Text { text: model.name }
            Rectangle { 
                visible: model.hasOverride
                Text { text: "✓" }
            }
        }
        onClicked: loadPrompt(model.name)
    }
}
```

### 3.3 프롬프트 편집기

#### 기능
- 마크다운 편집
- 구문 강조 (Markdown)
- 라인 번호
- 실시간 미리보기
- 변수 자동완성

#### UI 요소
```qml
SplitView {
    TextArea {
        id: editor
        text: currentPromptContent
        onTextChanged: hasChanges = true
    }
    
    Rectangle {
        // 미리보기
        Text {
            text: renderMarkdown(editor.text)
        }
    }
}
```

### 3.4 변수 미리보기 패널

#### 기능
- 사용 가능한 변수 목록 표시
- 변수 설명
- 클릭 시 에디터에 삽입

#### UI 요소
```qml
Column {
    Text { text: "사용 가능한 변수" }
    
    Repeater {
        model: availableVariables
        
        Rectangle {
            RowLayout {
                Text { text: "{{" + model.name + "}}" }
                Text { text: model.description }
            }
            onClicked: insertVariable(model.name)
        }
    }
}
```

## 4. 기술적 고려사항

### 4.1 백엔드 구현

#### PromptController 추가
```python
class PromptController(QObject):
    promptListChanged = pyqtSignal(list)
    promptContentChanged = pyqtSignal(str)
    hasOverrideChanged = pyqtSignal(bool)
    
    def __init__(self, prompt_manager: PromptManager):
        self._prompt_manager = prompt_manager
    
    @pyqtProperty(list, notify=promptListChanged)
    def promptList(self):
        return self._prompt_manager.list_available_prompts()
    
    @pyqtSlot(str)
    def loadPrompt(self, prompt_name: str):
        self._current_prompt = prompt_name
        self._content = self._prompt_manager.get_prompt(prompt_name)
        self._has_override = self._prompt_manager.has_user_override(prompt_name)
        self.promptContentChanged.emit(self._content)
        self.hasOverrideChanged.emit(self._has_override)
    
    @pyqtSlot(str)
    def savePrompt(self, content: str):
        self._prompt_manager.save_user_prompt(self._current_prompt, content)
        self._has_override = True
        self.hasOverrideChanged.emit(True)
    
    @pyqtSlot()
    def resetToDefault(self):
        self._prompt_manager.reset_to_default(self._current_prompt)
        self._content = self._prompt_manager.get_prompt(self._current_prompt)
        self._has_override = False
        self.promptContentChanged.emit(self._content)
        self.hasOverrideChanged.emit(False)
```

### 4.2 변수 시스템

#### 변수 정의
```python
VARIABLE_DEFINITIONS = {
    "CONTENT": {
        "description": "문서 전체 내용",
        "actions": ["summarize_note", "extract_todo", "polish_selection"]
    },
    "SELECTION": {
        "description": "사용자가 선택한 텍스트",
        "actions": ["polish_selection"]
    },
    "QUESTION": {
        "description": "사용자의 질문",
        "actions": ["current_note_qa"]
    }
}
```

### 4.3 QML 통합

#### Main.qml에 PromptController 등록
```python
# main.py
prompt_controller = PromptController(prompt_manager)
engine.rootContext().setContextProperty("promptController", prompt_controller)
```

#### AISettingsDialog에 프롬프트 관리 탭 추가
```qml
TabBar {
    TabButton { text: "모델 설정" }
    TabButton { text: "프롬프트 관리" }
}

StackLayout {
    // 모델 설정 탭
    ModelSettingsPanel {}
    
    // 프롬프트 관리 탭
    PromptManagementPanel {
        promptController: promptController
    }
}
```

## 5. 사용자 경험

### 5.1 사용 시나리오

#### 시나리오 1: 기존 프롬프트 수정
1. AI 설정 다이얼로그 열기
2. "프롬프트 관리" 탭 선택
3. 목록에서 "문서 요약" 선택
4. 편집기에서 프롬프트 수정
5. "저장" 클릭
6. 사용자 오버라이드 생성됨

#### 시나리오 2: 새 프롬프트 생성
1. 프롬프트 관리 다이얼로그에서 "새 프롬프트" 클릭
2. 이름 입력
3. 템플릿 선택 또는 빈 편집기 시작
4. 프롬프트 작성
5. 변수 삽입 (변수 패널에서 클릭)
6. 미리보기 확인
7. 저장

#### 시나리오 3: 기본 프롬프트로 복원
1. 프롬프트 목록에서 수정된 프롬프트 선택
2. "기본으로 복원" 클릭
3. 확인 다이얼로그 표시
4. 확인 시 사용자 오버라이드 삭제

### 5.2 접근성

#### 키보드 단축키
- Ctrl+S: 저장
- Ctrl+Z: 실행 취소
- Ctrl+Y: 다시 실행
- Ctrl+F: 검색
- Ctrl+/: 주석 처리

#### 다크 모드 지원
- 에디터 테마 지원
- 구문 강조 색상 조정

## 6. 향후 확장성

### 6.1 프롬프트 템플릿 공유
- 프롬프트 내보내기/가져오기
- 커뮤니티 프롬프트 라이브러리
- 프롬프트 버전 관리

### 6.2 고급 기능
- 프롬프트 A/B 테스트
- 프롬프트 성능 메트릭
- 변수 타입 검증
- 프롬프트 조건문 지원

### 6.3 AI 기능 확장
- 사용자 정의 AI 액션 추가
- 프롬프트 체이닝
- 멀티모달 프롬프트 (이미지, 오디오)

## 7. 구현 우선순위

### 단계 1: 기본 UI 구현
- 프롬프트 관리 다이얼로그 기본 레이아웃
- 프롬프트 목록 표시
- 기본 편집기 구현
- 저장/복원 기능

### 단계 2: 편집기 기능 강화
- 마크다운 구문 강조
- 미리보기 기능
- 변수 자동완성
- 실행 취소/다시 실행

### 단계 3: 고급 기능
- 검색/필터링
- 프롬프트 템플릿
- 내보내기/가져오기
- 버전 관리

## 8. ChatGPT와 논의할 질문

### UI/UX 관련
1. 프롬프트 관리를 AI 설정 다이얼로그 내에 포함할까요, 별도 다이얼로그로 만들까요?
2. 프롬프트 목록과 편집기를 분할 화면으로 표시할까요, 탭으로 분리할까요?
3. 마크다운 편집기에 어떤 기능이 필수적일까요? (구문 강조, 미리보기, 라인 번호 등)
4. 변수 삽입 방식으로 어떤 것을 선호하나요? (드래그 앤 드롭, 클릭, 자동완성)

### 기술적 관련
1. 마크다운 렌더링을 위해 어떤 라이브러리를 사용할까요? (Qt原生, 외부 라이브러리)
2. 프롬프트 변경 사항을 실시간으로 적용할까요, 앱 재시작 후 적용할까요?
3. 프롬프트 버전 관리는 어떻게 구현할까요? (Git, 간단한 버전 번호)
4. 프롬프트 검증을 어떻게 수행할까요? (변수 존재 확인, 구문 검사)

### 기능 관련
1. 사용자 정의 AI 액션을 어떻게 추가할까요? (UI에서, 코드에서)
2. 프롬프트 템플릿 시스템이 필요할까요?
3. 프롬프트 공유 기능이 필요할까요?
4. 프롬프트 성능 메트릭을 추적할까요?
