# AI 성능 튜닝 가이드

이 문서는 Note2 AI 기능의 성능 최적화를 위한 모델별 권장 사항과 테스트 절차를 안내합니다.

## 답변 생성 화면과 스트리밍 처리

- 모델 예열 요청에 실제 생성과 같은 컨텍스트 크기와 CPU 옵션을 전달합니다. 서로 다른 설정으로 모델 실행기를 다시 준비하는 일을 줄이기 위한 변경입니다.
- 작업 신호를 모두 연결한 다음 AI 요청을 시작하여, 빠르게 도착하는 첫 답변이나 완료 신호가 누락되지 않게 합니다.
- 첫 답변은 즉시 표시하고 이후에는 기존처럼 200~400ms 단위로 화면을 갱신합니다. 매번 문서를 Markdown과 JSON으로 다시 직렬화하지 않으며, Markdown 모드에서는 화면에 사용하지 않는 서식 문서 파싱도 생략합니다.
- 에디터 위에서 준비/생성 상태, 경과 시간, 실제 수신 글자 수를 확인할 수 있습니다. 첫 답변이 오기 전에는 임의의 진행률을 표시하지 않습니다.
- 긴 답변은 실제 편집 영역의 스크롤을 끝까지 따라갑니다. 앞부분을 읽으려면 **자동 스크롤**을 끄고, 다시 켜면 최신 내용으로 이동합니다.
- 생성 중 패널을 덮던 대기 화면은 제거했습니다. 입력칸과 실행/중지 버튼은 전체 너비를 사용하고, 프롬프트 미리보기는 필요할 때 펼칠 수 있습니다.
- 최종 답변을 적용한 후 저장하며, 같은 내용의 중복 갱신은 생략합니다. 오류나 중지로 끝난 부분 답변을 성공으로 처리하지 않습니다.

### 검증 방법

1. 긴 답변을 생성하면서 첫 답변 표시, 경과 시간, 수신 글자 수를 확인합니다.
2. 서식 편집과 Markdown 모드 모두에서 답변이 화면 아래로 넘어갈 때 마지막 줄을 따라가는지 확인합니다.
3. 자동 스크롤을 끄고 앞부분을 읽은 뒤, 다시 켜서 마지막 줄로 이동하는지 확인합니다.
4. 완료 후 결과 노트를 다시 열어 마지막 문장까지 저장되었는지 확인합니다. 중지/오류가 발생하면 부분 답변과 중단 상태가 남아야 합니다.

2026-10-17 로컬 Chromium 검증에서 100개 문단으로 구성한 동일 입력을 반복 갱신했을 때, 화면 갱신 호출의 평균 처리 시간은 기존 5.93ms에서 3.83ms로 줄었습니다(예열 2회 제외, 10회 평균). 이는 **앱의 표시 처리 비용**에 대한 측정이며 모델의 추론 속도나 첫 응답 시간 개선율을 뜻하지 않습니다. 두 편집 모드의 자동 스크롤과 다른 노트에 대한 스트리밍 갱신 거부도 확인했습니다.

## 모델별 권장 사항

### Q8 모델 (예: gemma4-2b-q8)
- **특징**: 최고 품질, 큰 모델 크기
- **단점**: CPU 사무용 PC에서 매우 느림
- **권장 대상**: GPU가 있는 환경, 품질이 중요한 경우
- **주의사항**: 첫 토큰이 145초 이상 걸릴 수 있음

### Q4 모델 (예: gemma4-2b-q4)
- **특징**: 품질과 속도의 균형
- **권장 대상**: 일반 사무용 PC
- **장점**: Q8 대비 훨씬 빠름, 합리적인 품질

### 경량 모델 (1.5B~2B)
- **특징**: 속도 우선, 매우 빠름
- **권장 대상**: 저사양 PC, 빠른 응답이 필요한 경우
- **장점**: 첫 토큰이 몇 초 내에 도착

## 현재 기본 설정

### low 모드 (기본)
- `num_predict`: 128
- `num_ctx`: 2048
- `temperature`: 0.2
- `keep_alive`: "5m"
- `timeout`: 300s

### normal 모드
- `num_predict`: 256
- `num_ctx`: 2048
- `temperature`: 0.2
- `keep_alive`: "10m"
- `timeout`: 300s

### high 모드
- `num_predict`: 512
- `num_ctx`: 4096
- `temperature`: 0.2
- `keep_alive`: "30m"
- `timeout`: 600s

## 테스트 절차

### 1. 기존 설정으로 기준 측정

**설정**: gemma4-2b-q8, num_predict=512, num_ctx=4096

**단계**:
1. 앱 재시작
2. 간단한 MD 노트 열기 (1-2단락)
3. AI Assistant Panel에서 "요약" 클릭
4. 로그에서 다음 값 기록:
   - `first_token` 시간
   - `load_duration` 시간
   - `total_duration` 시간
5. 동일 노트로 2회 반복

**예상 로그**:
```
[AIWorker] Starting task: action_id=summarize_note, model=gemma4-2b-q8:latest, ...
[AIWorker] Q8 model detected: gemma4-2b-q8:latest. Q8 models prioritize quality but are very slow on CPU office PCs. Consider using Q4 or smaller models (1.5B-2B) for better performance.
[AIWorker] First token received: 145.23s, action_id=summarize_note
[AIWorker] Stream complete: total=167.45s, first_token=145.23s, load_duration=179.12s, total_duration=216.04s, action_id=summarize_note
```

### 2. 가벼운 설정으로 측정

**설정**: gemma4-2b-q8, num_predict=256, num_ctx=2048

**단계**:
1. `app_data/ai/ai_settings.json` 수정:
   ```json
   {
     "num_predict": 256,
     "num_ctx": 2048
   }
   ```
2. 앱 재시작
3. 동일 노트로 "요약" 2회 실행
4. 로그 값 기록

**예상 로그**:
```
[AIWorker] Starting task: action_id=summarize_note, model=gemma4-2b-q8:latest, prompt_len=4123, options={'num_predict': 256, 'num_ctx': 2048, ...}
[AIWorker] First token received: 45.12s, action_id=summarize_note
[AIWorker] Stream complete: total=67.34s, first_token=45.12s, load_duration=179.12s, total_duration=216.04s, action_id=summarize_note
```

### 3. 가벼운 모델로 측정

**설정**: gemma4-2b-q4 또는 더 가벼운 모델

**단계**:
1. Ollama에서 가벼운 모델 다운로드:
   ```bash
   ollama pull gemma4-2b-q4:latest
   ```
2. `app_data/ai/ai_settings.json` 수정:
   ```json
   {
     "chat_model": "gemma4-2b-q4:latest",
     "num_predict": 256,
     "num_ctx": 2048
   }
   ```
3. 앱 재시작
4. 동일 노트로 "요약" 2회 실행
5. 로그 값 기록

**예상 로그**:
```
[AIWorker] Starting task: action_id=summarize_note, model=gemma4-2b-q4:latest, ...
[AIWorker] First token received: 12.34s, action_id=summarize_note
[AIWorker] Stream complete: total=25.67s, first_token=12.34s, load_duration=45.23s, total_duration=67.89s, action_id=summarize_note
```

## 결과 비교

| 설정/모델 | first_token | load_duration | total_duration | 비고 |
|----------|-------------|---------------|----------------|------|
| Q8 (512/4096) | ~145s | ~179s | ~216s | 매우 느림 |
| Q8 (256/2048) | ~45s | ~179s | ~216s | 개선됨 |
| Q4 (256/2048) | ~12s | ~45s | ~67s | 빠름 |

## 로그 해석

- **first_token**: 첫 토큰이 도착하기까지 걸린 시간 (앱 관점)
- **load_duration**: Ollama가 모델을 로드하는 데 걸린 시간 (Ollama 관점)
- **total_duration**: 전체 요청 처리 시간 (Ollama 관점)
- **total (앱)**: 앱이 요청부터 완료까지 걸린 시간 (앱 관점)

## 권장 설정

### 저사양 PC
- 모델: Q4 또는 1.5B~2B 경량 모델
- Performance mode: low
- `num_predict`: 128
- `num_ctx`: 2048

### 일반 사무용 PC
- 모델: Q4
- Performance mode: normal
- `num_predict`: 256
- `num_ctx`: 2048

### GPU 환경
- 모델: Q8
- Performance mode: high
- `num_predict`: 512
- `num_ctx`: 4096
