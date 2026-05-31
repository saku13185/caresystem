import numpy as np
from typing import List, Dict, Any, Tuple

class DoubleStepScorer:
    """
    1단계: 예측 오차 Z-score 검증 (전반적 이상 패턴 측정)
    2단계: 개별 활동 Boxplot IQR 검증 (국소 아웃라이어 파악)
    을 수행하는 이중 구조(Double-step) 이상 분류기
    """
    def __init__(self, historical_mae_mean: float = 3.2, historical_mae_std: float = 0.8):
        # 과거 통계적 MAE 평균 및 표준편차 기준 등록 (Z-score 분모/분자)
        self.mae_mean = historical_mae_mean
        self.mae_std = historical_mae_std

    def compute_mae_z_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
        """
        실측치와 예측치 벡터 간의 MAE 오차를 계산하고 Z-score 통계치로 환산합니다.
        반환: (MAE 수치, Z-score 수치)
        """
        # 예측치와 실측치 간의 평균 절대 오차(MAE) 연산
        mae = float(np.mean(np.abs(y_true - y_pred)))
        
        # Z-score 연산 공식 적용: (MAE - 평균) / 표준편차
        z_score = (mae - self.mae_mean) / self.mae_std
        return mae, z_score

    def check_boxplot_violations(self, y_true: np.ndarray, historical_dataset: np.ndarray, activity_labels: List[str]) -> List[Dict[str, Any]]:
        """
        41개 개별 일상생활 활동별로 역사적 분포의 Boxplot IQR 임계 범위(Q1 - 1.5*IQR, Q3 + 1.5*IQR)
        이탈 여부를 체크하여 극단적 수치 변이 항목을 식별합니다.
        historical_dataset 형상: (NumHistoryDays, 41)
        """
        violations = []
        
        for idx, act in enumerate(activity_labels):
            # 특정 활동의 역사적 점유율 데이터 슬라이싱
            history_shares = historical_dataset[:, idx]
            
            # 사분위수(Q1, Q3) 및 IQR(Q3 - Q1) 계산
            q1 = np.percentile(history_shares, 25)
            q3 = np.percentile(history_shares, 75)
            iqr = q3 - q1
            
            # Boxplot 극단 임계치 경계선 설정
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            actual_val = float(y_true[idx])
            
            # 하한 임계치 미달 시 Low Outlier 판정
            if actual_val < lower_bound:
                violations.append({
                    "activity": act,
                    "outlier": "Low",
                    "deviation": round(actual_val - lower_bound, 2),
                    "actual": round(actual_val, 2),
                    "bound": round(lower_bound, 2)
                })
            # 상한 임계치 초과 시 High Outlier 판정
            elif actual_val > upper_bound:
                violations.append({
                    "activity": act,
                    "outlier": "High",
                    "deviation": round(actual_val - upper_bound, 2),
                    "actual": round(actual_val, 2),
                    "bound": round(upper_bound, 2)
                })
                
        return violations

    def determine_danger_level(self, z_score: float, violations: List[Dict[str, Any]]) -> Tuple[int, str]:
        """
        Z-score 수치 및 Boxplot 위반 내역을 결합하여 3단계 위험도(0: 정상, 1: 주의, 2: 고위험)를 최종 산정합니다.
        """
        # 고위험(DANGER - 2) 기준: 전체 MAE Z-score가 2.5를 하드 코칭 초과하고
        # 수면(Sleep)이나 식사(Eat) 등의 핵심 일상에 극단적 위반(Boxplot Low)이 감지된 경우
        critical_activities = {"Sleep", "Eat"}
        has_critical_violation = any(v["activity"] in critical_activities and v["outlier"] == "Low" for v in violations)
        
        if z_score > 2.5 and has_critical_violation:
            return 2, "DANGER"
            
        # 주의(WARNING - 1) 기준: Z-score가 1.5를 초과하거나, 
        # Z-score는 높지 않으나 개별 활동의 Boxplot 위반 아웃라이어가 1개 이상 관측된 경우
        elif z_score > 1.5 or len(violations) > 0:
            return 1, "WARNING"
            
        # 정상(NORMAL - 0) 기준: 오차가 통계 오차 안정 범위 내이고 위반이 없는 상태
        else:
            return 0, "NORMAL"
