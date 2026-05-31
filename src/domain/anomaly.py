from typing import List, Dict, Any, Optional
from datetime import date

class BoxplotViolation:
    """
    Boxplot IQR 임계 범위 이탈 세부 정보를 담는 Value Object
    """
    def __init__(self, activity_label: str, outlier_type: str, deviation_value: float):
        # 이상 행동 라벨명 (예: 'Sleep')
        self.activity_label = activity_label
        # 이상 유형 구분 ('High' 또는 'Low')
        self.outlier_type = outlier_type
        # 임계치를 벗어난 실제 편차 수치
        self.deviation_value = deviation_value

class AnomalyReport:
    """
    이상 탐지 결과 및 LLM XAI 분석 보고서 엔터티 (Aggregate Root)
    """
    def __init__(
        self,
        id: str,
        resident_id: str,
        analysis_date: date,
        z_score: float,
        status: str,
        attention_weights: List[float],
        boxplot_violations: List[Dict[str, Any]],
        xai_report_content: Optional[str] = None,
        is_xai_generated: bool = False
    ):
        # 보고서 고유 ID (UUID v4)
        self.id = id
        # 대상 피돌봄 노인 ID (UUID v4 FK)
        self.resident_id = resident_id
        # 분석 실행 기준 일자
        self.analysis_date = analysis_date
        # 예측 MAE 오차의 통계적 Z-score 수치
        self.z_score = z_score
        # 최종 판정 등급 ('NORMAL', 'WARNING', 'DANGER')
        self.status = status
        # RNN 예측 모델이 출력한 15일간의 어텐션 가중치 기여도 배열
        self.attention_weights = attention_weights
        # Boxplot IQR 임계 범위 이탈 활동 리스트
        self.boxplot_violations = boxplot_violations
        # LLM을 통해 자동 완성된 한국어 분석 소견 보고서 원문
        self.xai_report_content = xai_report_content
        # XAI 설명서 작성 완료 플래그
        self.is_xai_generated = is_xai_generated
