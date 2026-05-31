# [구현 지시서] Task 2: ADL 전처리 및 AttentionRNN 시계열 예측 엔진 구현

본 문서는 예방적 돌봄 AI 에이전트 시스템의 **Task 2: 결측치 보강 전처리 파이프라인 및 PyTorch AttentionRNN 예측 엔진**을 구현 중 환각 없이 완벽하게 개발하기 위한 상세 코딩 지시서입니다.

---

## 1. 아키텍처적 목적 및 맥락 격리

* **수정/신규 대상 파일**:
  - [NEW] `src/usecases/preprocess_adl_data.py` (결측 가중평균 보강 및 15일 윈도우 텐서 가공 유스케이스)
  - [NEW] `src/infrastructure/models/attention_rnn.py` (PyTorch AttentionRNN 모델 레이어 설계)
  - [NEW] `src/infrastructure/models/train_pipeline.py` (신경망 모델 학습 및 파라미터 저장 파이프라인)
  - [NEW] `tests/test_models.py` (BDD Scenario 2 검증 하네스)
* **금지 사항 (하드 리미트)**:
  - 분석 윈도우 크기는 정확히 **과거 15일**로 고정합니다. 임의로 7일, 30일 등으로 유동 변경하는 추상 옵션을 설계하지 마십시오.
  - 예측의 입력 활동 변수 피처 수는 41개(ADL 41개) 차원으로 엄격 통제합니다.

---

## 2. 기술 제약 및 입력/출력 규격

### 2.1. 데이터 결측치 보강 (Imputation) 규칙
* **보강 공식**: 
  - 특정 날짜 $t$의 특정 활동 점유율 값이 `Null` 또는 유실된 경우, 최근 3일간의 동일 활동 실측치의 가중평균값으로 데이터를 안전 복구합니다.
  - 가중치 비중: $t-1$일 가중치 $0.5$, $t-2$일 가중치 $0.25$, $t-3$일 가중치 $0.25$.
  - 만일 3일 내내 연속 유실이 발생한 경우, 최근 15일 정상일의 전체 평균값으로 대체(Fallback) 보강합니다.

### 2.2. AttentionRNN 모델 스펙
* **네트워크 규격 (PyTorch)**:
  - 입력 텐서 윈도우 형상 (Input Shape): `(Batch, 15, 41)`
  - 출력 예측 텐서 형상 (Output Shape): `(Batch, 41)`
  - Self-Attention 레이어 탑재: RNN(GRU/LSTM)의 시점별(15일 시점) Hidden State에 가중치를 연산하여 어텐션 맵 `(Batch, 15)`을 추출하는 인터페이스 필수 제공.

---

## 3. 에러 처리 및 Fallback 규칙

* **수치 유실 예외**: 결측 보강 수행 후 데이터 형상이 맞지 않거나, 윈도우 길이가 15일 미만으로 부족한 데이터 인입 시, `ValueError` 예외를 즉각 발생시키고 분석 프로세스를 다운타임 없이 안전 격리 차단합니다.
* **GPU/CPU 장치 대조**: 학습 및 추론 실행 시 시스템 텐서가 서로 다른 디바이스(CPU/CUDA)에 올라가지 않도록 모델 레이어 상에서 장치 대조(`.to(device)`)를 강제 검증합니다.

---

## 4. BDD 기반 수용 기준 및 테스트 코드 구조

### [BDD Scenario 2]
* **Given**: 데이터 파이프라인 상에 특정 노인의 15일간의 정상적인 일간 시간 점유율(Shape: `(1, 15, 41)`) 데이터셋이 구비되어 있고, AttentionRNN 예측 모듈이 구동 준비 완료 상태일 때
* **When**: 해당 15일간의 다변량 윈도우 데이터를 모델에 주입하여 추론을 실행했을 때
* **Then**: 16일 차의 41개 활동 예측치 텐서(Shape: `(1, 41)`)와 각 15일에 대한 가중치를 매핑하는 Self-Attention 기여도 가중치 행렬(Shape: `(1, 15)`)이 에러 없이 동시 출력되어야 합니다.

### [실행 가능 테스트 코드 스켈레톤]
```python
# tests/test_models.py
import torch
import pytest
from src.infrastructure.models.attention_rnn import AttentionRNN

def test_attention_rnn_dimensions():
    # Given
    batch_size = 1
    window_size = 15
    features = 41
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = AttentionRNN(input_dim=features, hidden_dim=64).to(device)
    dummy_input = torch.randn(batch_size, window_size, features).to(device)
    
    # When
    predictions, attention_weights = model(dummy_input)
    
    # Then
    assert predictions.shape == (batch_size, features), f"Expected predictions shape {(batch_size, features)}, got {predictions.shape}"
    assert attention_weights.shape == (batch_size, window_size), f"Expected attention weights shape {(batch_size, window_size)}, got {attention_weights.shape}"
```
