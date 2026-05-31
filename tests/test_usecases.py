import pytest
from datetime import date
from src.infrastructure.persistence.db_connector import DatabaseConnector
from src.usecases.preprocess_adl_data import PreprocessADLDataUseCase
from src.usecases.run_anomaly_detection import RunAnomalyDetectionUseCase

def test_imputation_fallback_with_empty_database():
    """
    Given: 데이터베이스에 주민 요약 정보가 전무하여 15일 데이터가 부족한 경우
    When: 전처리 유스케이스 execute 구동 시
    Then: ValueError 예외가 즉각 발생하여 다운타임 없이 처리가 차단되는지 검증
    """
    db = DatabaseConnector("test_empty.db")
    usecase = PreprocessADLDataUseCase(db)
    
    # 윈도우 미달 시 ValueError 검증
    with pytest.raises(ValueError):
        usecase.execute("non-existent-uuid", date.today())
        
    # 테스트 종료 후 임시 테스트 파일 정리
    import os
    if os.path.exists("test_empty.db"):
        try:
            os.remove("test_empty.db")
        except PermissionError:
            pass

def test_anomaly_xai_fallback_integration():
    """
    [BDD Scenario 3 검증]
    Given: Z-score > 2.5(고위험) 상태와 Boxplot 수면 부족 이탈 결과 패킷 구성
    When: OpenAI API 통신 장애(mock_api_fail=True) 상황 하에서 LLM XAI 리포트 생성을 트리거 시
    Then: 의료 disclaimer 최상단 인쇄 및 주의보가 결합된 한국어 Fallback 리포트 출력 검증
    """
    usecase = RunAnomalyDetectionUseCase(DatabaseConnector("care_system.db"))
    
    anomaly_packet = {
        "resident_id": "test-uuid-9999",
        "virtual_code": "RES-TEST-001",
        "z_score": 2.7,
        "status": "Danger",
        "violations": [{"activity": "Sleep", "outlier": "Low", "deviation": -15.2}],
        "attention_weights": [0.1] * 15
    }
    
    # When: OpenAI API 장애 조건 주입
    report = usecase.execute_xai_reporting(anomaly_packet, mock_api_fail=True)
    
    # Then: 필수 하드코딩 경고문 헤더 인쇄 여부 확인
    assert "[의사결정 보조지표]" in report, "의료 진단 보조지표 경고 헤더가 누락되었습니다."
    assert "Danger" in report or "고위험" in report, "위험 등급 명칭이 보고서에 누락되었습니다."
    assert "Sleep" in report or "수면" in report, "이상행동 활동 명칭이 보고서에 누락되었습니다."
