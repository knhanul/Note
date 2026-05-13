# Nuni Note 프로젝트 아키텍처 및 소스 구성 문서

## 프로젝트 개요

**프로젝트 이름**: Nuni Note  
**버전**: 1.0.0  
**개발 목표**: 프리미엄 데스크탑 노트 작성 애플리케이션  
**기술 스택**: PyQt6/QML, Python 3.10+  
**디자인 철학**: Notion + iOS + Financial App

### 디자인 철학
- **신뢰**: 금융 앱 영감의 파란색 팔레트
- **미학**: iOS 레벨의 부드러움과 정교함
- **생산성**: 명확한 정보 아키텍처

### 주요 특징
- 글래스 모피즘 UI와 블러 효과
- 부드러운 호버/프레스 애니메이션
- iOS 영감의 둥근 모서리 (24px+)
- 부드러운 그림자
- 3-창 레이아웃 (사이드바 → 노트 목록 → 에디터)
- 파란색 그라디언트 선택 상태
- 필 스타일 에디터 툴바

---

## 현재 프로젝트 구조

```
Note/
├── main.py                          # 호환성 엔트리포인트
├── app_bootstrap.py                 # 앱 부트스트랩 및 서비스 생성
├── app_config.py                   # 앱 설정 구성
├── requirements.txt                # Python 의존성
├── nuni_note.db                    # SQLite 데이터베이스
├── nuni_note_settings.json         # 설정 파일
├── apps/                           # 애플리케이션 엔트리포인트
│   ├── markdown_editor/           # 순수 마크다운 에디터 앱
│   │   ├── main.py
│   │   └── README.md
│   ├── work_ai_editor/            # 미래 Ollama/SLLM 업무 비서
│   │   ├── main.py
│   │   └── README.md
│   └── special_editor/            # 미래 특수 목적 에디터
│       ├── main.py
│       └── README.md
├── packages/                       # 공유 패키지 (모듈형 경계)
│   ├── storage/                   # 스토리지 호환성 래퍼
│   │   ├── database.py
│   │   ├── note_repository.py
│   │   ├── folder_repository.py
│   │   ├── library_repository.py
│   │   └── settings_repository.py
│   ├── import_export/             # 임포트/익스포트 호환성 래퍼
│   ├── markdown_engine/           # 마크다운 엔진 경계 (문서화)
│   ├── editor_ui/                 # QML/UI 경계 (문서화)
│   ├── editor_core/               # 코어 조정 경계 (문서화 + 플레이스홀더)
│   ├── plugin_api/                # 플러그인 API 레지스트리
│   │   ├── registry.py
│   │   ├── plugin.py
│   │   ├── context.py
│   │   ├── command.py
│   │   ├── actions.py
│   │   └── example_plugin.py
│   └── ollama_plugin/             # Ollama 플러그인 스텁 (네트워크 없음)
├── controllers/                   # QML 컨트롤러 (기존 런타임)
│   ├── note_controller.py         # 노트 관리 컨트롤러
│   ├── folder_controller.py       # 폴더 관리 컨트롤러
│   ├── template_controller.py    # 템플릿 컨트롤러
│   ├── current_export_controller.py
│   └── folder_import_controller.py
├── services/                      # 서비스 레이어 (기존 런타임)
│   ├── database.py                # SQLite 데이터베이스
│   ├── note_service.py            # 노트 서비스
│   ├── folder_service.py          # 폴더 서비스
│   ├── library_service.py         # 라이브러리 서비스
│   ├── settings_service.py        # 설정 서비스
│   ├── template_service.py        # 템플릿 서비스
│   ├── image_service.py           # 이미지 서비스
│   ├── hwp_converter.py           # HWP 변환기
│   ├── hwpx_importer.py           # HWPX 임포터
│   ├── folder_export_service.py   # 폴더 익스포트
│   ├── current_note_export_service.py
│   └── folder_import_service.py   # 폴더 임포트
├── qml/                           # QML UI 파일
│   ├── Main.qml                   # 루트 윈도우
│   ├── components/                # 재사용 가능한 UI 컴포넌트
│   │   ├── GlassCard.qml
│   │   ├── AppHeader.qml
│   │   ├── SidebarSection.qml
│   │   ├── NotebookItem.qml
│   │   ├── NoteListItem.qml
│   │   ├── EditorToolbar.qml
│   │   └── TagChip.qml
│   ├── theme/                     # 디자인 시스템
│   │   ├── Colors.qml
│   │   ├── Typography.qml
│   │   └── Metrics.qml
│   └── assets/                    # 이미지 및 리소스
├── editor-src/                     # React/Tiptap 에디터
├── assets/                        # 이미지 및 리소스
├── tests/                         # 테스트 파일
├── scripts/                       # 스크립트
└── docs/                          # 문서
    └── architecture.md            # 아키텍처 문서
```

---

## 애플리케이션 구조

### 현재 앱 엔트리포인트

```bash
python main.py                    # 호환성 엔트리포인트
python apps/markdown_editor/main.py  # 순수 마크다운 에디터
python apps/work_ai_editor/main.py   # 미래 업무 AI 에디터
python apps/special_editor/main.py   # 미래 특수 목적 에디터
```

### 앱 관계

- **root main.py**: 호환성 엔트리포인트, 기존 런타임 재사용
- **apps/markdown_editor**: 순수 마크다운 에디터 앱, 기존 런타임 재사용
- **apps/work_ai_editor**: 미래 Ollama/SLLM 업무 비서, 현재 스켈레톤
- **apps/special_editor**: 미래 특수 목적 에디터, 현재 스켈레톤

모든 앱은 현재 동일한 `app_config.py`, `app_bootstrap.py`, `qml/Main.qml`, `controllers/`, `services/`를 재사용합니다.

---

## 패키지 경계 및 역할

### 1. packages/storage

**역할**: 스토리지 호환성 래퍼  
**목적**: 향후 앱이 동일한 스토리지 동작을 복사하지 않고 재사용할 수 있도록 지속성 관련 코드 수집

**구성**:
- `database.Database`: `services.database.Database` 재내보내기
- `note_repository.NoteRepository`: `services.note_service.NoteService` 별칭
- `folder_repository.FolderRepository`: `services.folder_service.FolderService` 별칭
- `library_repository.LibraryRepository`: `services.library_service.LibraryService` 별칭
- `settings_repository.SettingsRepository`: `services.settings_service.SettingsService` 별칭

**현재 단계**: 호환성 래퍼 단계, 기존 `services` 파일이 여전히 소스

### 2. packages/import_export

**역할**: 임포트/익스포트 호환성 래퍼  
**목적**: 임포트/익스포트 서비스 재사용 가능한 경계

**현재 단계**: 문서화 단계

### 3. packages/markdown_engine

**역할**: 마크다운 엔진 경계  
**목적**: 향후 마크다운 엔진 분리를 위한 문서화 및 플레이스홀더

**현재 단계**: 문서화 단계

### 4. packages/editor_ui

**역할**: QML/UI 경계  
**목적**: QML/UI 구성 요소 경계 문서화

**현재 단계**: 문서화 단계

### 5. packages/editor_core

**역할**: 코어 조정 경계  
**목적**: UI 어댑터와 지속성/임포트/익스포트 서비스 사이의 에디터 도메인 조정 분리

**향후 책임**:
- 노트 선택 상태
- 더티 상태 관리
- 저장 시퀀싱
- 이미지 토큰 처리
- 필터링 및 페이지네이션
- 템플릿
- 문서 명령

**현재 단계**: 문서화/경계 단계, 실제 구현은 여전히 `controllers/` 및 `services/`에 있음

**비목표**:
- Ollama/SLLM 통합
- 앱 브랜딩
- 특수 비즈니스 워크플로우 패널
- QML 시각적 컴포넌트
- 앱 특정 UI 정책

### 6. packages/plugin_api

**역할**: 플러그인 API 레지스트리  
**목적**: 미래 Note2 앱 변형 및 플러그인을 위한 최소 확장 API 제공

**확장 포인트**:
- `Command`: 명령
- `MenuAction`: 메뉴 액션
- `DocumentAction`: 문서 액션
- `SidebarPanel`: 사이드바 패널

**향후 후보**:
- 설정 페이지
- 익스포트/임포트 제공자
- AI 어시스턴트 제공자
- 에디터 명령 제공자
- 문서 분석 제공자
- 워크스페이스/사이드바 제공자

**현재 단계**: 최소 레지스트리 단계
- QML 연결 없음
- WebEngine 연결 없음
- 앱 부트스트랩 연결 없음
- 데이터베이스 액세스 없음
- 외부 의존성 없음
- 플러그인 자동 발견 없음

### 7. packages/ollama_plugin

**역할**: Ollama 플러그인 스텁  
**목적**: 네트워크 없는 Ollama 플러그인 스텁

**현재 단계**: 스켈레톤 단계

---

## 컨트롤러 레이어

### note_controller.py
- 노트 관리 로직
- 저장 시퀀싱
- 필터링 및 페이지네이션
- 태그 필터링
- 이미지 토큰화/수화
- QML 신호/슬롯

### folder_controller.py
- 폴더 관리 로직
- 폴더 트리 관리
- 스마트 폴더 (전체 노트, 즐겨 찾기)
- QML 신호/슬롯

### template_controller.py
- 템플릿 관리

### current_export_controller.py
- 현재 노트 익스포트

### folder_import_controller.py
- 폴더 임포트 (HWP/HWPX 포함)

---

## 서비스 레이어

### note_service.py
- 노트 CRUD 작업
- 태그 필터링
- 페이지네이션
- 데이터베이스 액세스

### folder_service.py
- 폴더 CRUD 작업
- 폴더 계층 구조 관리

### library_service.py
- 라이브러리 관리

### settings_service.py
- 설정 관리

### template_service.py
- 템플릿 관리

### image_service.py
- 이미지 관리

### database.py
- SQLite 데이터베이스 연결

### hwp_converter.py
- HWP 변환기 (COM 기반)

### hwpx_importer.py
- HWPX 구조화 임포터

### folder_export_service.py
- 폴더 익스포트

### current_note_export_service.py
- 현재 노트 익스포트

### folder_import_service.py
- 폴더 임포트 (HWP/HWPX 포함)

---

## QML UI 구조

### Main.qml
- 루트 윈도우
- 3-창 레이아웃 (사이드바 → 노트 목록 → 에디터)
- 글래스 모피즘 카드
- 애니메이션 상태

### components/
- GlassCard.qml: 글래스 카드 컴포넌트
- AppHeader.qml: 앱 헤더
- SidebarSection.qml: 사이드바 섹션
- NotebookItem.qml: 노트북 아이템
- NoteListItem.qml: 노트 목록 아이템
- EditorToolbar.qml: 에디터 툴바
- TagChip.qml: 태그 칩

### theme/
- Colors.qml: 색상 시스템
- Typography.qml: 타이포그래피 시스템
- Metrics.qml: 메트릭 시스템

---

## 에디터 구조

### editor-src/
- React/Tiptap 기반 WYSIWYG 에디터
- 마크다운 모드 지원
- WebEngine을 통한 QML 통합

---

## 현재 리팩토링 단계

이것은 **첫 번째 구조적 분리 단계**입니다:

- 컨트롤러/서비스에서 패키지로 실제 로직 이동 없음
- QML 변경 없음
- DB 스키마 변경 없음
- 런타임 어댑터 또는 플러그인 연결 없음
- 스켈레톤 앱, 래퍼 패키지, 문서화, 테스트 베이스라인에 집중

### 안정성 우선

리팩토링은 기존 안정성 보존을 우선합니다:

- 오토세이브 로직 변경 없음
- 이미지 토큰화/수화 변경 없음
- QML 컨텍스트 속성 이름 변경 없음
- DB 경로 및 스키마 변경 없음
- 모든 기존 앱 계속 이전과 동일하게 실행

---

## 의존성

### Python 패키지
- PyQt6>=6.5.0
- PyQt6-Qt6>=6.5.0
- PyQt6-WebEngine>=6.5.0
- python-docx>=1.1.0
- python-hwpx>=2.9.0
- pywin32>=306
- md2hwpx>=0.1.5
- gethwp>=1.1.1

### 시스템 요구사항
- Python 3.10+
- Qt 6.5+ (PyQt6에 포함)
- Windows (pywin32 필요)

---

## 향후 방향

### 모듈형 빌드 시스템 목표

1. **순수 마크다운 에디터 빌드**: 기본 에디터 기능만 포함
2. **확장 기능 포함 빌드**: 선택된 확장 기능 포함
3. **다중 확장 지원**: 여러 확장 기능을 독립적으로 활성화 가능

### 첫 번째 확장: PC용 SLLM 업무비서

- 기술: PC용 SLLM (Small Language Model)
- 목적: 업무 비서 기능 제공
- 통합: plugin_api를 통한 확장
- 격리: 순수 마크다운 에디터와 독립적

### 확장 아키텍처

```
Base Editor (순수 마크다운 에디터)
├── Extension 1: SLLM 업무비서
├── Extension 2: [미래 확장]
└── Extension 3: [미래 확장]
```

---

## 데이터베이스 스키마

### 현재 스키마
- notes 테이블
- folders 테이블
- settings 테이블
- note_images 테이블

### 데이터 위치
- `nuni_note.db`: SQLite 데이터베이스
- `nuni_note_settings.json`: 설정 파일
- `app_data/`: 앱 데이터 디렉토리
- `libraries/`: 라이브러리 디렉토리

---

## 설정

### 브랜딩
- **기본**: 누니노트 (nuni)
- **대안**: 포시드노트 (posid)

### 설정 구성 (app_config.py)
- base_dir: 프로젝트 루트 디렉토리
- brand: 브랜드 이름
- app_name: 애플리케이션 이름
- icon_path: 아이콘 경로
- logo_path: 로고 경로
- qml_dir: QML 디렉토리
- main_qml_path: 메인 QML 경로
- qml_import_path: QML 임포트 경로
- app_data_dir: 앱 데이터 디렉토리
- organization_name: 조직 이름
- app_version: 앱 버전

---

## 부트스트랩 프로세스

### app_bootstrap.py

1. **서비스 생성**:
   - settings_service
   - library_service
   - folder_controller
   - note_controller
   - template_controller
   - current_export_controller
   - folder_import_controller

2. **QML 엔진 구성**:
   - QML 임포트 경로 추가
   - 컨텍스트 속성 설정
   - 브랜드, 앱 이름, 로고 경로 설정
   - UI 스케일 설정

3. **메인 QML 로드**:
   - Main.qml 로드
   - 루트 객체 확인

---

## 테스트

### 회귀 테스트
```bash
python scripts/run_regression_checks.py
```

### 테스트 디렉토리 구조
- tests/ 디렉토리에 테스트 파일 포함

---

## 디자인 시스템

### 색상
- **Primary**: 파란색 계열 (#3B82F6, #2563EB) - 신뢰
- **Accent**: 주황/장미색 (#F97316, #FB7185) - 하이라이트만
- **Background**: 쿨 그레이 (#FAFBFC, #F1F5F9)
- **Surface**: 반투명 흰색 (70-90% 불투명도)

### 타이포그래피
- **폰트**: Inter (시스템 폴백: Segoe UI → Helvetica → Arial)
- **웨이트**: 400 Regular, 500 Medium, 600 Semibold, 700 Bold
- **크기**: 12-28px 스케일

### 간격 및 반경
- **간격**: 4, 8, 12, 16, 24, 32, 48px 스케일
- **반경**: 최소 16px, 주요 카드 24-30px
- **그림자**: 낮은 불투명도 (5-10%), 높은 블러 (8-24px)

### 애니메이션
- **지속 시간**: 120-180ms 상호작용
- **이징**: 자연스러운 모션을 위한 베지어 곡선
- **효과**: 프레스 시 스케일, 호버 시 Y-변환

---

## HWP/HWPX 임포트 플로우

### 진입점
- `FolderImportService._hwp_to_markdown()`

### 임포트 모드
- `fast_text`: 레거시 `gethwp` 텍스트 추출만
- `structured`: `hwpx_importer` 경로만
- `auto` (기본값): structured 우선, `fast_text` 폴백

### 구조화 경로
- `.hwpx` → `services.hwpx_importer.hwpx_to_markdown()`
- `.hwp` → `services.hwp_converter.convert_hwp_to_hwpx_via_com()` → `hwpx_importer`

### 폴백 경로
- 구조화 실패 시 모드가 허용하면 `gethwp`로 폴백
- 임포트 실패 시 빈 마크다운 안전 반환 (앱 크래시 방지)

---

## 향후 개발 로드맵

### 단계 1: 구조적 분리 (현재 단계)
- 스켈레톤 앱 생성
- 래퍼 패키지 생성
- 문서화
- 테스트 베이스라인

### 단계 2: 로직 이동
- 컨트롤러/서비스에서 패키지로 로직 이동
- 역호환성 유지

### 단계 3: 플러그인 통합
- plugin_api를 통한 플러그인 등록
- QML/WebEngine 연결
- 앱 부트스트랩 연결

### 단계 4: SLLM 업무비서 개발
- PC용 SLLM 통합
- 업무 비서 기능 구현
- plugin_api를 통한 확장

### 단계 5: 모듈형 빌드 시스템
- 빌드 옵션 구현
- 확장 기능 선택적 포함
- 배포 패키징

---

## 요약

Nuni Note는 현재 구조적 분리 단계에 있으며, 순수 마크다운 에디터와 확장 기능을 추가한 앱을 모두 지원하는 모듈형 아키텍처로 진화 중입니다. 현재 단계에서는 실제 로직 이동 없이 스켈레톤 앱, 래퍼 패키지, 문서화에 집중하고 있으며, 향후 SLLM 업무비서를 첫 번째 확장 기능으로 개발할 계획입니다.
