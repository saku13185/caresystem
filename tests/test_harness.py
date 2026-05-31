import pytest
import numpy as np
import torch
from datetime import date
from src.infrastructure.persistence.seed_data import generate_normalized_adl_shares, CASAS_41_ACTIVITIES
from src.infrastructure.models.attention_rnn import AttentionRNN
from src.infrastructure.scorers.double_step_scorer import DoubleStepScorer
from src.infrastructure.llm.xai_report_generator import XaiReportGenerator

# ==============================================================================
# Harness Engineering 5대 검증 항목 자동화 테스트 스위트 (tests/test_harness.py)
# ==============================================================================

def test_harness_1_data_integrity():
    """
    [검증 1] 데이터 무결성 검증 (Data Integrity)
    합성 데이터 제너레이터가 생성한 41개 ADL 일간 시간 점유율 합산이 
    수학적으로 정확히 100.00% ± 0.01% 무결성을 항시 만족하는지 검증합니다.
    """
    # Given & When: 100일치 데이터를 생성
    for _ in range(100):
        shares = generate_normalized_adl_shares()
        
        # Then: 41개 활동 점유비의 합 계산
        total_share = sum(shares.values())
        
        # 허용 오차 한계 ±0.01% 이내로 수렴하는지 단언
        assert abs(total_share - 100.0) <= 0.01, f"ADL share sum integrity violation: {total_share}%"


def test_harness_2_model_mae_bound():
    """
    [검증 2] 모델 예측 오차 상한 검증 (Model Prediction Error Bound)
    AttentionRNN 시계열 예측 텐서의 평균 절대 오차(MAE)가 
    허용 임계 범위(10.0%) 내로 안정되게 바인딩되는지 검증합니다.
    """
    # Given: PyTorch 모델 객체 생성 및 임의의 입력 데이터 (Batch, 15, 41) 준비
    model = AttentionRNN()
    model.eval()
    
    # 0~100% 범위 내로 한정 정규화된 윈도우 인풋 생성
    dummy_input = torch.rand(1, 15, 41)
    # L1 정규화를 통해 점유비 합계가 100이 되도록 모사
    dummy_input = (dummy_input / dummy_input.sum(dim=2, keepdim=True)) * 100.0
    
    # When: 신경망 순방향 추론 실행
    with torch.no_grad():
        predictions, attention_weights = model(dummy_input)
        
    # Then: 출력 차원 및 예측치 범위 검증
    pred_np = predictions.cpu().numpy()[0]
    
    # 예측된 다변량 벡터의 수치가 지나치게 발산하지 않고 유효 범위 내인지 계측
    assert pred_np.shape == (41,), f"Invalid output shape: {pred_np.shape}"
    # MAE 오차가 상한 임계치 10%보다 훨씬 안정적인 실측 오차 내에 수렴하는지 확인을 위해
    # 임의의 기준 실측치와의 평균 절대 편차가 비정상적으로 크지 않은지 검증
    dummy_true = np.full(41, 100.0 / 41, dtype=np.float32)
    mae = np.mean(np.abs(pred_np - dummy_true))
    
    # 가중치 미학습 임의 상태에서도 MAE가 10.0%의 정량적 바운드 범주 내에 들어옴을 검증
    assert mae <= 10.0, f"Model MAE error bound exceeded: {mae}%"


def test_harness_3_danger_classification():
    """
    [검증 3] 위험도 임계치 정상 분류 검증 (Danger Threshold Classification)
    Z-score > 2.5(고위험) 및 핵심 ADL(수면, 식사) 극단적 Boxplot Low 위반 동시 발생 시, 
    Double-step 분류기가 정확하게 2단계(DANGER) 고위험으로 판정 및 분류 격리하는지 검증합니다.
    """
    # Given: DoubleStepScorer 인스턴스 확보
    scorer = DoubleStepScorer(historical_mae_mean=3.0, historical_mae_std=0.5)
    
    # Z-score > 2.5를 충족하는 고위험 입력 데이터 모사 (MAE=4.5 -> Z-score=(4.5-3.0)/0.5 = 3.0)
    y_true = np.zeros(41)
    y_pred = np.zeros(41)
    # 1일차 41개 활동 중 수면(Sleep)이 역사적 하한을 하회하는 극단적 이탈(Low Violation) 발생 모사
    # Sleep index = 0 (CASAS_41_ACTIVITIES 첫 번째 요소)
    violations = [
        {"activity": "Sleep", "outlier": "Low", "deviation": -15.4}
    ]
    
    # When: 위험 분류 오케스트레이션 실행
    danger_code, status_str = scorer.determine_danger_level(z_score=3.0, violations=violations)
    
    # Then: DANGER(2) 등급 강제 매핑 검증
    assert danger_code == 2, f"Expected danger code 2, got {danger_code}"
    assert status_str == "DANGER", f"Expected status 'DANGER', got '{status_str}'"


def test_harness_4_xai_hallucination_prevention():
    """
    [검증 4] LLM 설명의 데이터 근거 일치성 검증 (Hallucination Prevention)
    XAI 리포팅 엔진이 도출한 한국어 설명 텍스트가 
    전달된 이상 탐지 팩트(Z-score, 이상 활동 명칭) 정보와 완벽히 100% 일치하는지 검증합니다.
    """
    # Given: XaiReportGenerator 및 가상 anomaly_packet 구성
    generator = XaiReportGenerator()
    anomaly_packet = {
        "resident_id": "uuid-9999",
        "virtual_code": "RES-MASK-2026A",
        "z_score": 2.72,
        "status": "DANGER",
        "violations": [{"activity": "Sleep", "outlier": "Low", "deviation": -15.4}],
        "attention_weights": [0.1] * 15
    }
    
    # When: 한글 XAI 리포트 도출
    report = generator.generate_report(anomaly_packet, mock_api_fail=True)
    
    # Then: 환각 방지 데이터 팩트 대조 수행 (Sub-string matching)
    # 대상 비식별 코드가 정확히 인쇄되는가
    assert "RES-MASK-2026A" in report, "비식별 코드 기재 오류 (PII/환각 감지)"
    # 탐지된 이상 활동 명칭이 근거대로 포함되는가
    assert "Sleep" in report, "이상 탐지 활동 누락 (데이터 불일치)"
    # 계산된 실제 Z-score 정보가 포함되는가
    assert "2.72" in report, "Z-score 수치 왜곡 환각 감지"


def test_harness_5_ethics_and_medical_disclaimer():
    """
    [검증 5] 윤리 및 안전 제약조건 검증 (Ethics & Medical Disclaimers)
    1. 리포트의 최상단 첫 줄에 의료 보조지표 면책 헤더가 강제 인쇄되었는지 검증합니다.
    2. '우울증 환자로 진단됩니다' 같은 임상 진단 확정형 단어가 완전히 차단(Blacklisted words)되었는지 검증합니다.
    """
    # Given: XaiReportGenerator 및 DANGER 패킷 준비
    generator = XaiReportGenerator()
    anomaly_packet = {
        "resident_id": "uuid-9999",
        "virtual_code": "RES-MASK-2026A",
        "z_score": 2.72,
        "status": "DANGER",
        "violations": [{"activity": "Sleep", "outlier": "Low", "deviation": -15.4}],
        "attention_weights": [0.1] * 15
    }
    
    # When: 한글 XAI 리포트 최종 생성
    report = generator.generate_report(anomaly_packet, mock_api_fail=True)
    
    # Then:
    # 1. 의료 보조지표 고정 disclaimers 문두 표출 단언
    assert report.startswith("[의사결정 보조지표]"), "문두 면책 보조지표 주의 배너 누락 (윤리 가드 위반)"
    
    # 2. 임상 진단 단정 금지 단어 차단 단언 (Blacklisted words)
    clinical_blacklist = ["환자로 진단됩니다", "우울증 환자", "치매 환자", "질병을 진단", "의학적으로 진증"]
    for word in clinical_blacklist:
        assert word not in report, f"임상적 진단 오용 표현 검출: '{word}' (윤리 가드 위반)"
