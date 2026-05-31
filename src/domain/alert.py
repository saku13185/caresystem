from datetime import datetime
from typing import Optional

class CaregiverAlert:
    """
    사회복지사용 경보 및 피드백 처리 엔터티 (Aggregate Root)
    """
    def __init__(
        self,
        id: str,
        anomaly_report_id: str,
        action_status: str = "PENDING",
        feedback_message: Optional[str] = None,
        alert_sent_at: Optional[datetime] = None
    ):
        # 경보 고유 ID (UUID v4)
        self.id = id
        # 대상 이상 탐지 보고서 ID (UUID v4 FK)
        self.anomaly_report_id = anomaly_report_id
        # 경보 조치 현황 상태 ('PENDING', 'APPROVED', 'REJECTED')
        self.action_status = action_status
        # 사회복지사가 등록한 분석 정오탐 사유 및 관리 피드백 메시지
        self.feedback_message = feedback_message
        # 보호자 전송 완료 시점
        self.alert_sent_at = alert_sent_at
