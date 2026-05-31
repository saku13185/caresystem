import numpy as np
import json
from typing import List, Dict, Any, Tuple
from datetime import date, timedelta
from src.usecases.ports.care_repository import CareRepositoryPort

class PreprocessADLDataUseCase:
    """
    15일 슬라이딩 윈도우 시계열 데이터 가공 및 결측치 가중평균 보강(Imputation) 유스케이스
    """
    def __init__(self, db_repository: CareRepositoryPort):
        # 영속성 저장소 조회를 위한 DB 리포지토리 어댑터 바인딩
        self.db = db_repository
        # 41개 핵심 CASAS 활동 표준 목록
        from src.infrastructure.persistence.seed_data import CASAS_41_ACTIVITIES
        self.activities = CASAS_41_ACTIVITIES

    def execute(self, resident_id: str, target_date: date) -> Tuple[np.ndarray, np.ndarray]:
        """
        특정 노인의 분석 타겟 일자 기준, 과거 15일 슬라이딩 윈도우 입력 데이터 (15, 41) 및
        16일 차(당일) 실제 점유비 데이터 (41,)를 전처리하여 반환합니다.
        
        결측치가 존재할 경우 3일 가중평균 보강법 및 전체 평균 Fallback 보강법을 작동시킵니다.
        """
        # 1. 윈도우 인풋을 위해 타겟 일자 기준 최근 15일(윈도우) + 당일(16일차 실측) = 총 16일의 날짜 배열 생성
        dates_needed = [target_date - timedelta(days=d) for d in range(16)]
        dates_needed.reverse() # 시간 순서 정렬 (t-15일 ~ t일(당일))

        # 2. 데이터베이스에서 해당 일자의 ADL 요약 정보 로드
        summaries = self.db.get_adl_summaries_by_date_range(resident_id, dates_needed[0], dates_needed[-1])
        db_data = {
            item['date']: (json_to_dict(item['activity_shares']) if isinstance(item['activity_shares'], str) else item['activity_shares'])
            for item in summaries
        }

        if len(db_data) == 0:
            raise ValueError(f"주민 ID {resident_id}에 대해 대상 기간 내 실측 데이터가 존재하지 않습니다.")

        # 3. 16일간의 각 날짜별 41개 피처 벡터 구성 및 결측 검증
        adl_sequence: List[np.ndarray] = []
        
        for idx, current_date in enumerate(dates_needed):
            date_str = str(current_date)
            
            if date_str in db_data:
                # 정상 데이터 발견 시 벡터 생성
                day_shares = db_data[date_str]
                day_vector = self._shares_to_vector(day_shares)
                adl_sequence.append(day_vector)
            else:
                # 결측치(Null 또는 데이터 단선) 감지 시 보강 로직(Imputation) 수행
                # t-1일 가중치 0.5, t-2일 가중치 0.25, t-3일 가중치 0.25 적용
                imputed_vector = self._impute_missing_date(resident_id, dates_needed, idx, adl_sequence)
                adl_sequence.append(imputed_vector)

        # 4. 분석 윈도우 크기는 정확히 15일이어야 하며, 16일 차 실측 패킷까지 총 16개 차원 검증
        if len(adl_sequence) < 16:
            raise ValueError(f"분석에 필요한 최소 윈도우 크기(15일) 데이터가 부족합니다. 현재 확보된 데이터: {len(adl_sequence)}일치")

        # 5. 입력 윈도우 (15, 41) 및 타겟 실측 텐서 (41,) 분할 반환
        x_window = np.array(adl_sequence[:-1], dtype=np.float32) # (15, 41)
        y_true = np.array(adl_sequence[-1], dtype=np.float32)    # (41,)

        return x_window, y_true

    def _shares_to_vector(self, shares: Dict[str, float]) -> np.ndarray:
        """
        41개 ADL 점유비 JSON 딕셔너리를 고정 순서의 41차원 float32 numpy 벡터로 변환합니다.
        """
        vector = np.zeros(len(self.activities), dtype=np.float32)
        for i, act in enumerate(self.activities):
            vector[i] = shares.get(act, 0.0)
        return vector

    def _impute_missing_date(self, resident_id: str, dates_needed: List[date], current_idx: int, resolved_sequence: List[np.ndarray]) -> np.ndarray:
        """
        결측 데이터에 대하여 [t-1일(0.5), t-2일(0.25), t-3일(0.25)] 가중평균값으로 보강합니다.
        만일 3일 내내 연속 유실 시 최근 15일 정상일의 전체 평균값으로 Fallback 대체합니다.
        """
        target_date = dates_needed[current_idx]
        
        # 최근 3일간 이미 정제 완료된 시퀀스 벡터 확인
        available_history = resolved_sequence # 이미 처리된 과거 시퀀스
        history_len = len(available_history)
        
        weights = [0.5, 0.25, 0.25]
        imputed_sum = np.zeros(len(self.activities), dtype=np.float32)
        weight_sum = 0.0

        # 최근 3일의 가중 평균 계산 시도
        for offset in range(1, 4):
            hist_idx = history_len - offset
            if hist_idx >= 0:
                imputed_sum += available_history[hist_idx] * weights[offset - 1]
                weight_sum += weights[offset - 1]

        # 최근 가중평균 데이터를 확보한 경우 (정규화 유지)
        if weight_sum > 0.0:
            imputed_vector = imputed_sum / weight_sum
            # 합산 100.00% 스무딩 정규화 강제 보장
            total = np.sum(imputed_vector)
            if total > 0.0:
                imputed_vector = (imputed_vector / total) * 100.0
            return imputed_vector

        # 3일 연속 결측 발생 또는 극초반 데이터 결측 시 Fallback: 과거 15일 전체 정상 일자의 평균값 조회
        rows = self.db.get_adl_summaries_before_date(resident_id, target_date, 15)
            
        if not rows:
            # 과거 역사 데이터가 단 한 건도 없는 경우 균등 분배(Uniform Fallback)
            uniform_vector = np.full(len(self.activities), 100.0 / len(self.activities), dtype=np.float32)
            return uniform_vector

        # 과거 정상일의 평균 벡터 계산
        vectors = []
        for row in rows:
            shares = json_to_dict(row['activity_shares']) if isinstance(row['activity_shares'], str) else row['activity_shares']
            vectors.append(self._shares_to_vector(shares))
        
        mean_vector = np.mean(vectors, axis=0)
        # 스무딩 정규화
        total = np.sum(mean_vector)
        if total > 0.0:
            mean_vector = (mean_vector / total) * 100.0
        return mean_vector

def json_to_dict(json_str: str) -> Dict[str, Any]:
    """
    JSON 문자열을 안전하게 파이썬 딕셔너리로 역직렬화합니다.
    """
    try:
        return json.loads(json_str)
    except Exception:
        return {}
