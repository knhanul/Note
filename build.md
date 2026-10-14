# PosidNote 빌드 방법

PyInstaller를 사용해 `PosidNote.exe` 단일 파일(one-file)을 빌드합니다.

## 1. 사전 준비

```powershell
# 가상환경 생성 및 활성화
python -m venv .venv
./.venv/Scripts/activate

# 의존성 설치
pip install -r requirements.txt
pip install pyinstaller
```

> 이미 전역 Python에 PyInstaller가 설치되어 있다면 활성화 없이 `pyinstaller` 명령을 바로 사용해도 됩니다.

## 2. 빌드 실행

```powershell
pyinstaller apps/work_ai_editor/build_posid_onefile.spec
```

빌드가 시작되면 다음 정보를 입력받습니다.

| 입력 항목 | 기본값 | 용도 |
|---|---|---|
| 버전 | `1.0.0` | About 팝업 버전, exe 파일 버전 리소스 |
| 빌드일자 | 오늘 날짜 (`yyyy-MM-dd`) | About 팝업 빌드일자 |

```
버전 [1.0.0]: 1.2.0
빌드일자(yyyy-MM-dd) [2026-10-14]:
```

엔터만 누르면 기본값이 적용됩니다.

입력된 값은 `build_info.json`에 기록되어 실행 파일에 함께 포함되며,
프로그램의 정보(About) 팝업에서 버전과 빌드일자로 표시됩니다.

## 3. 비대화형 빌드 (자동화)

프롬프트 없이 빌드하려면 환경변수로 지정합니다.

```powershell
$env:POSID_VERSION="1.2.0"
$env:POSID_BUILD_DATE="2026-10-14"
pyinstaller apps/work_ai_editor/build_posid_onefile.spec --noconfirm
```

## 4. 빌드 결과

- 실행 파일: `dist/PosidNote.exe`
- 작업 중간 산출물: `build/PosidNote/` (삭제 가능)
- 생성/갱신되는 파일: `build_info.json` (About 팝업에서 읽는 버전·빌드일자 메타데이터)

## 5. 참고

- `apps/work_ai_editor/build_posid_onefile.spec` — one-file 빌드 spec (버전/빌드일자 입력 포함)
- `apps/work_ai_editor/build_posid.spec` — 기존 빌드 spec (버전 입력 없음)
- 첫 빌드는 PyQt6, ChromaDB 등 용량이 커서 시간이 걸릴 수 있습니다.
- 빌드된 실행 파일은 처음 실행 시 임시 폴더에 압축을 풀고 실행되므로, 스크립트 실행보다 시작이 다소 느릴 수 있습니다. 시작 중에는 `assets/images/posid_signature.svg` 스플래시가 먼저 표시됩니다.
