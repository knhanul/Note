# HWPX Test Fixtures

이 경로에는 HWPX 변환 품질 테스트를 위한 비민감 fixture만 둘 수 있습니다.

## 정책

- 실제 회사 문서, 고객 정보, 업무 문서, 계약서, 내부 표준 문서 추가 금지
- 가능하면 바이너리 `.hwpx` 파일을 직접 커밋하지 않고, 테스트에서 synthetic HWPX를 생성하는 방식优先
- 고정 fixture가 꼭 필요한 경우에도 더미 텍스트만 사용

## 권장 fixture 유형

- `minimal_paragraph.hwpx` - 최소 문단
- `heading_paragraph.hwpx` - 제목/소제목 포함
- `basic_table.hwpx` - 기본 표
- `basic_list.hwpx` - 목록/번호목록
- `image_reference.hwpx` - 이미지 참조

## 생성 도구

synthetic HWPX는 `tests/helpers/hwpx_fixture_builder.py`를 사용해 테스트 내에서 생성하세요.
