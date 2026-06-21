# AI업무비서 HWPX 문서 처리 분석

## 개요

AI업무비서 앱에서 HWPX 문서는 두 가지 경로로 처리됩니다:

1. **현재문서AI** — HWPX 파일을 Markdown으로 변환하여 LLM prompt에 직접 주입
2. **참고문서AI** — HWPX 파일을 Markdown으로 변환 후 청크로 분할하여 색인 DB에 저장

두 경로 모두 동일한 HWPX 파서(`hwpx_to_markdown()`)를 사용합니다.

---

## 1. 현재문서AI: HWPX → LLM Content 전달

### 처리 흐름

```
QML (파일 선택)
  → assistantController.loadExternalDocumentJson(file_path)
  → DocumentLoader.load(path)
  → _load_hwpx(path)
  → convert_hwpx_to_markdown_text(path)
  → hwpx_to_markdown(hwpx_path)
  → _build_hwp_context() 로 구조화된 텍스트 생성
  → JSON 반환 (content 필드)
  → QML에서 {{CONTENT}} 변수로 주입
  → PromptRenderer로 프롬프트 렌더링
  → AIWorker → Ollama /api/generate 호출
```

### 관련 파일

- **入口**: `packages/ollama_plugin/assistant_controller.py` — `loadExternalDocumentJson()`
- **로더**: `services/document_loader.py` — `DocumentLoader._load_hwpx()`
- **변환 서비스**: `packages/import_export/hwpx_import_service.py` — `convert_hwpx_to_markdown_text()`
- **파서**: `services/hwpx_importer.py` — `hwpx_to_markdown()`

### 변환 상세

`convert_hwpx_to_markdown_text()` 함수 (`packages/import_export/hwpx_import_service.py:35-73`):

1. `hwpx_to_markdown()` 시도 (ZIP → XML 파싱)
2. 실패 또는 빈 결과 시 `gethwp` 라이브러리 fallback 시도
3. 둘 다 실패하면 빈 문자열 + 경고 반환

`hwpx_to_markdown()` 함수 (`services/hwpx_importer.py:79-111`):

1. HWPX 파일을 ZIP으로 열어 `Contents/*section*.xml` 파일들을 찾음
2. XML을 파싱하여 블록으로 분해:
   - `ParagraphBlock` — 일반 문단
   - `HeadingBlock` — 제목 (`#`, `##` 등)
   - `ListItemBlock` — 리스트 항목
   - `TableBlock` — 표 (Markdown table로 변환)
   - `ImageBlock` — 이미지 (`![](path)` 참조)
3. 각 블록을 Markdown으로 렌더링
4. 각주/미주는 본문 끝에 `## 각주`, `## 미주` 섹션으로 추가
5. 머리말/꼬리말은 무시 (경고만 로그)

### Content 구조

`_load_hwpx()`가 생성하는 content 텍스트 구조:

```
[문서 파일 정보]
파일명: example.hwpx
파일 유형: HWPX
추출 방식: HWPX XML 구조 분석
문단 수: N
표 수: N
주요 섹션 수: N

[문서 구조]
(마크다운 본문)

[표 내용]
(표 마크다운)

[추출 경고]
- 경고 메시지 (있는 경우)
```

### 길이 제한

| 구분 | 제한 | 변수 |
|------|------|------|
| 단일 파일 | 4,000자 | `MAX_CONTENT_LENGTH` |
| 폴더 로드 | 50,000자 | `MAX_EXTERNAL_FOLDER_CONTENT_LENGTH` |

초과 시 truncation 및 안내 메시지 추가.

---

## 2. 참고문서AI: HWPX → 색인 DB 전달

### 처리 흐름

```
QML (참고문서 색인 요청)
  → aiRagController.indexExternalFiles(file_paths)
  → AiRagApplicationService.index_external_files()
  → 확장자별 분기 (.hwpx)
  → AiDocumentIndexService.index_hwpx_file()
  → import_hwpx_as_markdown_document(path)
  → convert_hwpx_to_markdown_text(path)
  → hwpx_to_markdown(hwpx_path)
  → MarkdownDocument 반환
  → index_markdown_document()
    ├── build_indexed_document() → repo.upsert_document() (문서 메타데이터 저장)
    └── chunk_markdown_document() → repo.replace_chunks() (청크 분할 및 저장)
  → SQLite ai_index.db에 저장
```

### 관련 파일

- **入口**: `controllers/ai_rag_controller.py` — `indexExternalFiles()`
- **애플리케이션 서비스**: `services/ai_rag_application_service.py` — `index_external_files()`
- **인덱스 서비스**: `services/ai_document_index_service.py` — `index_hwpx_file()`
- **변환 서비스**: `packages/import_export/hwpx_import_service.py` — `import_hwpx_as_markdown_document()`
- **파서**: `services/hwpx_importer.py` — `hwpx_to_markdown()` (현재문서AI와 동일)

### 색인 상세

`index_hwpx_file()` (`services/ai_document_index_service.py:165-184`):

1. `import_hwpx_as_markdown_document(path)` 호출 → `MarkdownDocument` 반환
2. `document_id` 자동 생성: `file:hwpx_file:<sha256_16자>`
3. `index_markdown_document()` 호출:
   - **문서 메타데이터**: `build_indexed_document()` → `repo.upsert_document()`
   - **청크 분할**: `chunk_markdown_document()` → `repo.replace_chunks()`
4. 청크는 SQLite DB (`app_data/ai/ai_index.db`)의 `ai_document_chunks` 테이블에 저장

### 폴더 색인

`AiRagApplicationService.index_external_folder()` (`services/ai_rag_application_service.py:260-291`):

- 지원 확장자: `.md`, `.markdown`, `.txt`, `.html`, `.htm`, `.docx`, `.hwpx`, `.hwp`
- 폴더 내 `.hwpx` 파일 자동 포함
- `rglob("*")`로 재귀 탐색

### 검색 방식

현재 검색은 **키워드 기반 LIKE 검색**입니다 (`AiSearchService.search_keyword()`).
벡터 유사도 검색이 아닌 키워드 매칭으로 청크를 검색합니다.

---

## 3. HWPX 변환 파서 상세

### 핵심 파일

`services/hwpx_importer.py` (863줄)

### 변환 과정

```
HWPX 파일 (ZIP)
  ├── Contents/section*.xml  →  XML 파싱
  │   ├── <p> 태그           →  ParagraphBlock / HeadingBlock / ListItemBlock
  │   ├── <tbl> 태그         →  TableBlock (Markdown table)
  │   └── <pic> 태그         →  ImageBlock (![](path))
  ├── bindata/*.png 등       →  이미지 추출 ({stem}_assets/ 폴더)
  ├── footnote XML           →  각주 추출 (## 각주)
  ├── endnote XML            →  미주 추출 (## 미주)
  └── header/footer XML      →  무시 (경고 로그만)
```

### 블록 타입

| 블록 | XML 태그 | Markdown 출력 |
|------|---------|--------------|
| `ParagraphBlock` | `<p>` | 일반 텍스트 |
| `HeadingBlock` | `<p>` (스타일 기반) | `#`, `##`, `###` |
| `ListItemBlock` | `<p>` (리스트 컨텍스트) | `- 항목` 또는 `1. 항목` |
| `TableBlock` | `<tbl>` | Markdown table (`| ... |`) |
| `ImageBlock` | `<pic>` | `![alt](image_path)` |
| `UnknownBlock` | 기타 | raw 텍스트 |

### 인코딩 처리

`_read_xml()` 함수 (`services/hwpx_importer.py:329-346`):

- 시도 순서: `utf-8` → `utf-16` → `cp949` → `euc-kr`
- 모두 실패 시 `utf-8` with `errors="ignore"`

### Fallback 메커니즘

`packages/import_export/hwpx_import_service.py:76-84`:

1. **1차**: `hwpx_to_markdown()` — ZIP/XML 파싱
2. **2차**: `gethwp.read_hwpx()` — 외부 라이브러리 (설치 시)
3. **최종**: 빈 문자열 + `[HWPX_IMPORT_FAILED]` 경고

### 경고 코드

| 코드 | 의미 |
|------|------|
| `HWPX_FILE_NOT_FOUND` | 파일을 찾을 수 없음 |
| `HWPX_INVALID_EXTENSION` | .hwpx가 아닌 파일 |
| `HWPX_BROKEN_ZIP` | ZIP 형식이 아님 |
| `HWPX_SECTION_NOT_FOUND` | 섹션 XML 없음 |
| `HWPX_XML_PARSE_FAILED` | XML 파싱 실패 |
| `HWPX_CONVERSION_EMPTY` | 변환 결과가 비어 있음 |
| `HWPX_CONVERSION_FAILED` | 변환 중 예외 발생 |
| `HWPX_FALLBACK_USED` | gethwp fallback 사용 |
| `HWPX_IMPORT_FAILED` | 전체 실패 |
| `HEADER_FOOTER_IGNORED` | 머리말/꼬리말 무시 |

---

## 4. 두 경로 비교

| 구분 | 현재문서AI | 참고문서AI |
|------|-----------|-----------|
| **변환 함수** | `convert_hwpx_to_markdown_text()` | `convert_hwpx_to_markdown_text()` (동일) |
| **HWPX 파서** | `hwpx_to_markdown()` + `gethwp` fallback | 동일 |
| **출력 형식** | 구조화된 context 텍스트 (메타정보 + 본문) | `MarkdownDocument` (body_markdown) |
| **길이 제한** | 4,000자 (단일), 50,000자 (폴더) | 제한 없음 (전체 문서 색인) |
| **청크 분할** | 없음 (전체를 prompt에 주입) | `chunk_markdown_document()`로 청크 분할 후 DB 저장 |
| **이미지 추출** | 추출하되 content에는 markdown 참조만 포함 | 동일 (마크다운 참조만 저장) |
| **표 처리** | Markdown table + 별도 `[표 내용]` 섹션 | Markdown table만 body_markdown에 포함 |
| **각주/미주** | 본문 끝에 `## 각주`, `## 미주` 추가 | 동일 |
| **DB 저장** | 없음 | SQLite `ai_index.db`에 문서 + 청크 저장 |
| **검색 방식** | 해당 없음 | 키워드 기반 LIKE 검색 |

---

## 5. 데이터 흐름도

```
                    HWPX 파일
                       │
                       ▼
              ┌─────────────────────┐
              │ hwpx_to_markdown()  │  (services/hwpx_importer.py)
              │   ZIP → XML → MD    │
              └────────┬────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
    [현재문서AI]              [참고문서AI]
           │                       │
           ▼                       ▼
  DocumentLoader            AiDocumentIndexService
  ._load_hwpx()             .index_hwpx_file()
           │                       │
           ▼                       ▼
  _build_hwp_context()      import_hwpx_as_markdown_document()
  (메타정보 + 본문)          (MarkdownDocument)
           │                       │
           ▼                       ▼
  JSON (content)            chunk_markdown_document()
  → QML {{CONTENT}}         (청크 분할)
           │                       │
           ▼                       ▼
  PromptRenderer            repo.replace_chunks()
  → AIWorker                → SQLite ai_index.db
  → Ollama /api/generate           │
                                  ▼
                          AiSearchService
                          .search_keyword()
                          (LIKE 기반 검색)
                                  │
                                  ▼
                          AiRagService
                          .answer_question()
                          → Ollama /api/generate
```
