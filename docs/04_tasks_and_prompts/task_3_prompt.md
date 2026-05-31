# [구현 지시서] Task 3: Double-step 분류기 및 LLM XAI 리포팅 엔진 연동

본 문서는 예방적 돌봄 AI 에이전트 시스템의 **Task 3: Z-score + Boxplot IQR Double-step 분류기와 LLM XAI 한글 돌봄 리포팅 에이전트**를 완벽하게 연동 구현하기 위한 상세 코딩 지시서입니다.

---

## 1. 아키텍처적 목적 및 맥락 격리

* **수정/신규 대상 파일**:
  - [NEW] `src/infrastructure/scorers/double_step_scorer.py` (Z-score & Boxplot IQR 검증 어댑터 구현)
  - [NEW] `src/infrastructure/llm/xai_report_generator.py` (OpenAI/로컬 API XAI 리포트 구성 어댑터)
  - [NEW] `src/usecases/run_anomaly_detection.py` (이중 판정 및 보고서 생성 통합 오케스트레이션 유스케이스)
  - [NEW] `tests/test_usecases.py` (BDD Scenario 3 검증 하네스)
* **금지 사항 (하드 리미트)**:
  - 생성되는 XAI 리포트 텍스트 내에 피돌봄 노인의 이름, 실제 주소 등 어떠한 개인식별정보(PII)의 직접 기재를 강력히 금지합니다. 모든 대상 정보는 UUID(식별자) 매핑 상태를 유지해야 합니다.
  - 임상적으로 질병을 최종 확정 짓는 문장 표현(예: "본 노인은 우울증 환자로 진단됩니다.")을 절대 사용할 수 없게 템플릿 수준에서 통제합니다.

---

## 2. 기술 제약 및 입력/출력 규격

### 2.1. Double-step 이상치 검증 스펙
* **1단계 (Z-score 판정)**: 16일 차 예측치와 실측치 MAE 오차를 역사적 통계 평균 MAE($\mu$) 및 표준편차($\sigma$)와 대조하여 오차 Z-score 계산. $Z > 2.5$일 시 고위험으로 규정.
  $$Z = \frac{MAE - \mu_{MAE}}{\sigma_{MAE}}$$
* **2단계 (Boxplot IQR 판정)**: Z-score 경고 돌파 시, 41개 개별 활동 점유율이 개별 역사적 박스플롯 범위(Q1 - 1.5*IQR 미만, Q3 + 1.5*IQR 초과)를 이탈하는지 대조해 극단 아웃라이어 항목 식별.
* **출력 등급**: 정상(Normal - 0), 주의(Warning - 1), 고위험(Danger - 2).

### 2.2. LLM XAI 리포트 경고 필터 및 규격
* **의료적 보조지표 강제 문구**: 자동 완성 보고서 최상단 첫 줄에 반드시 다음 문구를 **하드코딩(Hard-coding)**하여 무조건 인쇄 출력되게 설계해야 합니다.
  > `[의사결정 보조지표] 본 문서는 의료진의 최종 임상적 진단을 대체할 수 없으며, 예방 및 모니터링 보조 목적으로만 활용해야 합니다.`
* **입력 컨텍스트 (Context Packet)**: `resident_id` (UUID), `status` (위험 등급), `z_score`, `violations` (Boxplot 이탈 목록), `attention_weights` (최대 기여 가중치 일자).

---

## 3. 에러 처리 및 Fallback 규칙

* **LLM API 연동 장애 Fallback**: OpenAI API 통신 장애 또는 API 타임아웃 지연 발생 시, 시스템 대시보드가 지연 없이 복구되도록 규칙 기반(Rule-based)의 Fallback 문구(예: "[경고] 최근 수면 활동의 편차가 Z-score 2.7로 감지되었습니다. XAI 보고서 생성 API 장애로 정밀 텍스트 분석은 생략됩니다.")를 즉시 자동 발급하고 에러 로그를 기록합니다.

---

## 4. BDD 기반 수용 기준 및 테스트 코드 구조

### [BDD Scenario 3]
* **Given**: 예측 오차의 Z-score가 $2.5$를 초과하고(고위험 기준), 2단계 Boxplot 검증 결과 "수면(Sleep)" 활동의 시간 점유율이 역사적 임계 범위인 IQR 아웃라이어를 크게 하회하는 수치 편차를 보였을 때
* **When**: Double-step 분류기가 이 진단 결과 패킷(위험 등급: 2, Z-score: 2.7, 이상 활동: Sleep)을 구성하여 LLM XAI 리포트 추론기에 컨텍스트로 전달하고 구성을 지시했을 때
* **Then**: 생성된 한글 보고서 내에 "위험도 등급: 고위험", "수면 감소"에 대한 구체적 텍스트 설명이 정상 포함되어야 하며, 문서 최상단에 "의료적 최종 진단 대체 불가" 경고문이 정확히 포함된 문서가 최종 출력되어야 합니다.

### [실행 가능 테스트 코드 스켈레톤]
```python
# tests/test_usecases.py
import pytest
from src.usecases.run_anomaly_detection import RunAnomalyDetectionUseCase

def test_anomaly_xai_fallback_integration():
    # Given
    usecase = RunAnomalyDetectionUseCase()
    anomaly_packet = {
        "resident_id": "test-uuid-9999",
        "z_score": 2.7,
        "status": "Danger",
        "violations": [{"activity": "Sleep", "outlier": "Low"}],
        "attention_weights": [0.1] * 15
    }
    
    # When
    report = usecase.execute_xai_reporting(anomaly_packet, mock_api_fail=True)
    
    # Then
    assert "[의사결정 보조지표]" in report, "Warning header is missing!"
    assert "Danger" in report or "고위험" in report
    assert "Sleep" in report or "수면" in report
```
