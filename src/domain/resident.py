import uuid
from typing import Dict, Optional
from datetime import date, datetime

class DailyADLSummary:
    """
    일별 전처리 ADL 점유율 요약 엔터티
    """
    def __init__(self, id: str, resident_id: str, date_val: date, activity_shares: Dict[str, float], is_normalized: bool = False):
        # 고유 식별자 (UUID v4)
        self.id = id
        # 대상 노인 식별자 (UUID v4)
        self.resident_id = resident_id
        # 요약 기준 일자
        self.date = date_val
        # 41개 ADL 행동 및 점유비율 매핑 JSON 딕셔너리
        self.activity_shares = activity_shares
        # 100% 정규화 정합성 만족 여부 플래그
        self.is_normalized = is_normalized

class Resident:
    """
    피돌봄 노인 엔터티 (Aggregate Root)
    """
    def __init__(self, id: str, virtual_code: str, current_status: str = "NORMAL", registered_at: Optional[datetime] = None):
        # 고유 식별자 (UUID v4)
        self.id = id
        # 비식별 난수 가상 연구 코드
        self.virtual_code = virtual_code
        # 현재 이상 상태 분류 등급 ('NORMAL', 'WARNING', 'DANGER')
        self.current_status = current_status
        # 최초 등록 일시
        self.registered_at = registered_at or datetime.now()
