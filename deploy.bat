@echo off
:: 한글 깨짐 방지를 위해 인코딩을 UTF-8로 설정
chcp 65001 > nul

echo [Git 상태 확인]
git status
echo.

:: 커밋 메시지 입력 받기
set /p COMMIT_MSG="커밋 메시지를 입력하세요: "

echo.
echo [변경사항 커밋 및 푸시 진행]
git add .
git commit -m "%COMMIT_MSG%"
git push -u origin feature/ollama

echo.
echo [main 브랜치 병합 진행]
git checkout main
git pull origin main
git merge feature/ollama-connection

echo.
echo [회귀 테스트 실행 중...]
python scripts/run_regression_checks.py

:: python 스크립트의 종료 코드를 확인 (0이면 정상, 그 외는 에러)
if %errorlevel% neq 0 (
    echo.
    echo ❌ [오류] run_regression_checks.py 테스트를 통과하지 못했습니다.
    echo ❌ main 브랜치 푸시를 중단합니다.
    pause
    exit /b %errorlevel%
)

echo.
echo ✅ [성공] 테스트를 무사히 통과했습니다. main 브랜치에 푸시합니다.
git push origin main

echo.
echo 모든 작업이 완료되었습니다.
pause