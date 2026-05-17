# AI 성능 튜닝 가이드

이 문서는 Note2 AI 기능의 성능 최적화를 위한 모델별 권장 사항과 테스트 절차를 안내합니다.

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
