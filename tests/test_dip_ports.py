import ast
import os
import pytest
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from src.usecases.ports.care_repository import CareRepositoryPort
from src.usecases.preprocess_adl_data import PreprocessADLDataUseCase
from src.usecases.run_anomaly_detection import RunAnomalyDetectionUseCase

class FakeCareRepository(CareRepositoryPort):
    """
    CareRepositoryPort Protocol을 구현하는 인메모리 Fake 레포지토리.
    테스트 목적으로 실제 데이터베이스(SQLite) 없이 메모리 상의 딕셔너리와 리스트로 영속 상태를 모사합니다.
    """
    def __init__(self):
        self.residents = {}
        self.adl_summaries = []
        self.anomaly_reports = []
        self.caregiver_alerts = []

    def get_resident(self, resident_id: str) -> Optional[Dict[str, Any]]:
        return self.residents.get(resident_id)

    def get_adl_summaries_by_date_range(self, resident_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        results = []
        for s in self.adl_summaries:
            if s["resident_id"] == resident_id and start_date <= s["date"] <= end_date:
                results.append(s)
        # 시간 오름차순 정렬
        results.sort(key=lambda x: x["date"])
        return results

    def get_adl_summaries_before_date(self, resident_id: str, before_date: date, limit: int) -> List[Dict[str, Any]]:
        results = []
        for s in self.adl_summaries:
            if s["resident_id"] == resident_id and s["date"] < before_date:
                results.append(s)
        # 시간 내림차순 정렬 후 limit개 슬라이스
        results.sort(key=lambda x: x["date"], reverse=True)
        return results[:limit]

    def get_daily_adl_summaries(self, resident_id: str, limit_days: int) -> List[Dict[str, Any]]:
        results = []
        for s in self.adl_summaries:
            if s["resident_id"] == resident_id:
                results.append(s)
        results.sort(key=lambda x: x["date"], reverse=True)
        return results[:limit_days]

    def update_resident_status(self, resident_id: str, status: str) -> None:
        if resident_id in self.residents:
            self.residents[resident_id]["current_status"] = status

    def insert_anomaly_report(
        self,
        report_id: str,
        resident_id: str,
        analysis_date: date,
        z_score: float,
        status: str,
        attention_weights: List[float],
        boxplot_violations: List[Dict[str, Any]],
        xai_report_content: Optional[str] = None,
        is_xai_generated: bool = False
    ) -> None:
        self.anomaly_reports.append({
            "id": report_id,
            "resident_id": resident_id,
            "analysis_date": analysis_date,
            "z_score": z_score,
            "status": status,
            "attention_weights": attention_weights,
            "boxplot_violations": boxplot_violations,
            "xai_report_content": xai_report_content,
            "is_xai_generated": is_xai_generated
        })

    def insert_caregiver_alert(
        self,
        alert_id: str,
        anomaly_report_id: str,
        action_status: str = "PENDING",
        feedback_message: Optional[str] = None,
        alert_sent_at: Optional[datetime] = None
    ) -> None:
        self.caregiver_alerts.append({
            "id": alert_id,
            "anomaly_report_id": anomaly_report_id,
            "action_status": action_status,
            "feedback_message": feedback_message,
            "alert_sent_at": alert_sent_at
        })

def test_ast_check_zero_direct_db_connector_imports():
    """
    [DIP 정적 AST 단언 검증]
    유스케이스 계층 파일인 preprocess_adl_data.py와 run_anomaly_detection.py가
    구체 db_connector.py 모듈을 직접 임포트하지 않는지 AST 분석을 통해 정적으로 단언합니다.
    """
    target_files = [
        "src/usecases/preprocess_adl_data.py",
        "src/usecases/run_anomaly_detection.py"
    ]
    
    for file_path in target_files:
        assert os.path.exists(file_path), f"분석 대상 파일 부재: {file_path}"
        
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
            
        for node in ast.walk(tree):
            # 1. 'import db_connector' 형태 검사
            if isinstance(node, ast.Import):
                for name in node.names:
                    assert "db_connector" not in name.name, f"{file_path} 내 구체 db_connector 직접 import 발견!"
            # 2. 'from ... import DatabaseConnector' 형태 검사
            elif isinstance(node, ast.ImportFrom):
                assert node.module is None or "db_connector" not in node.module, f"{file_path} 내 구체 db_connector 모듈 importFrom 발견!"
                for name in node.names:
                    assert "DatabaseConnector" not in name.name, f"{file_path} 내 구체 DatabaseConnector 클래스 import 발견!"

def test_usecases_with_fake_repository():
    """
    [FakeRepository 유스케이스 격리 테스트]
    SQLite DB 생성 없이 인메모리 Fake 레포지토리를 인젝션하여
    전처리 및 이상 탐지 오케스트레이션 유스케이스가 무결하게 동작하는지 검증합니다.
    """
    # 1. Given: FakeRepository 생성 및 가상 노인 데이터 셋업
    repo = FakeCareRepository()
    resident_id = "fake-resident-001"
    repo.residents[resident_id] = {
        "id": resident_id,
        "virtual_code": "RES-FAKE-999",
        "current_status": "NORMAL"
    }
    
    # 2. 16일치 가상 ADL 데이터(41차원 균등분포) 시딩 (Preprocess 윈도우 충족용)
    from src.infrastructure.persistence.seed_data import CASAS_41_ACTIVITIES
    target_date = date(2026, 5, 31)
    mock_shares = {act: 100.0 / len(CASAS_41_ACTIVITIES) for act in CASAS_41_ACTIVITIES}
    
    for i in range(16):
        d = target_date - timedelta(days=i)
        repo.adl_summaries.append({
            "id": f"fake-summary-{i}",
            "resident_id": resident_id,
            "date": d,
            "activity_shares": mock_shares
        })
        
    # 3. When: PreprocessADLDataUseCase 실행
    preprocessor = PreprocessADLDataUseCase(repo)
    x_window, y_true = preprocessor.execute(resident_id, target_date)
    
    # Then: 입력 윈도우 (15, 41) 및 타겟 실측 텐서 (41,) 규격 단언
    assert x_window.shape == (15, 41)
    assert y_true.shape == (41,)
    
    # 4. When: RunAnomalyDetectionUseCase 실행 (Mock 가중치 사용)
    usecase = RunAnomalyDetectionUseCase(repo, model_path="non_existent_model.pt")
    result = usecase.execute(resident_id, target_date)
    
    # Then: 이상 탐지 오케스트레이션 결과 검증
    assert result["resident_id"] == resident_id
    assert result["virtual_code"] == "RES-FAKE-999"
    assert result["status"] in ["NORMAL", "WARNING", "DANGER"]
    assert "z_score" in result
    
    # 5. Then: Fake 레포지토리 상태 갱신 및 결과 저장 유무 단언
    assert len(repo.anomaly_reports) == 1
    assert len(repo.caregiver_alerts) == 1
    assert repo.residents[resident_id]["current_status"] == result["status"]
