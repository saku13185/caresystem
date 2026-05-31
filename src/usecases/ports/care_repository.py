from typing import Protocol, List, Dict, Any, Optional
from datetime import date, datetime

class CareRepositoryPort(Protocol):
    """
    유스케이스 계층이 영속성 인프라 계층(SQLite 등)에 의존하지 않도록
    추상화된 데이터 접근 계약을 정의하는 Repository Port Protocol.
    """
    def get_resident(self, resident_id: str) -> Optional[Dict[str, Any]]:
        """
        피돌봄 노인의 현재 비식별 상태 정보를 단건 조회합니다.
        """
        ...

    def get_adl_summaries_by_date_range(self, resident_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        특정 기간 동안의 일별 요약 데이터 리스트를 조회합니다.
        """
        ...

    def get_adl_summaries_before_date(self, resident_id: str, before_date: date, limit: int) -> List[Dict[str, Any]]:
        """
        특정 일자 이전의 최근 N일치 일별 요약 데이터 리스트를 조회합니다.
        """
        ...

    def get_daily_adl_summaries(self, resident_id: str, limit_days: int) -> List[Dict[str, Any]]:
        """
        특정 노인의 과거 N일간의 슬라이딩 윈도우용 ADL 요약 데이터를 로드합니다.
        """
        ...

    def update_resident_status(self, resident_id: str, status: str) -> None:
        """
        피돌봄 노인의 현재 이상 분류 위험도를 갱신합니다.
        """
        ...

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
        """
        이상 탐지 보고서 및 분석 결과를 추가합니다.
        """
        ...

    def insert_caregiver_alert(
        self,
        alert_id: str,
        anomaly_report_id: str,
        action_status: str = "PENDING",
        feedback_message: Optional[str] = None,
        alert_sent_at: Optional[datetime] = None
    ) -> None:
        """
        비상 돌봄 경보 및 사회복지사 조치 메모 이력을 추가합니다.
        """
        ...
