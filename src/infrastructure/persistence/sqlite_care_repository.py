from typing import List, Dict, Any, Optional
from datetime import date, datetime
from src.usecases.ports.care_repository import CareRepositoryPort
from src.infrastructure.persistence.db_connector import DatabaseConnector

class SQLiteCareRepository(CareRepositoryPort):
    """
    CareRepositoryPort Protocol을 구현하는 SQLite 영속성 어댑터.
    내부적으로 DatabaseConnector를 주입받아 데이터베이스 조회 및 조작 업무를 대행합니다.
    """
    def __init__(self, db_connector: DatabaseConnector):
        self.db = db_connector

    def get_resident(self, resident_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get_resident(resident_id)

    def get_adl_summaries_by_date_range(self, resident_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        return self.db.get_adl_summaries_by_date_range(resident_id, start_date, end_date)

    def get_adl_summaries_before_date(self, resident_id: str, before_date: date, limit: int) -> List[Dict[str, Any]]:
        return self.db.get_adl_summaries_before_date(resident_id, before_date, limit)

    def get_daily_adl_summaries(self, resident_id: str, limit_days: int) -> List[Dict[str, Any]]:
        return self.db.get_daily_adl_summaries(resident_id, limit_days)

    def update_resident_status(self, resident_id: str, status: str) -> None:
        self.db.update_resident_status(resident_id, status)

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
        self.db.insert_anomaly_report(
            report_id=report_id,
            resident_id=resident_id,
            analysis_date=analysis_date,
            z_score=z_score,
            status=status,
            attention_weights=attention_weights,
            boxplot_violations=boxplot_violations,
            xai_report_content=xai_report_content,
            is_xai_generated=is_xai_generated
        )

    def insert_caregiver_alert(
        self,
        alert_id: str,
        anomaly_report_id: str,
        action_status: str = "PENDING",
        feedback_message: Optional[str] = None,
        alert_sent_at: Optional[datetime] = None
    ) -> None:
        self.db.insert_caregiver_alert(
            alert_id=alert_id,
            anomaly_report_id=anomaly_report_id,
            action_status=action_status,
            feedback_message=feedback_message,
            alert_sent_at=alert_sent_at
        )
