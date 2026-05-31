import os
import uuid
import random
import json
from datetime import date, timedelta, datetime
from typing import Dict, List, Optional
from src.infrastructure.persistence.db_connector import DatabaseConnector

# 41개 핵심 CASAS 일상생활 활동(ADL) 표준 레이블 정의
CASAS_41_ACTIVITIES: List[str] = [
    'Sleep', 'Cook', 'Eat', 'Shower', 'Watch_TV', 'Read', 'Work', 'Rest', 'Go_Out', 'Clean',
    'Dress', 'Groom', 'Wash_Dishes', 'Laundry', 'Exercise', 'Drink_Water', 'Take_Medicine', 'Toileting', 'Nap', 'Meditation',
    'Relax', 'Call_Family', 'Call_Doctor', 'Use_Computer', 'Listen_Music', 'Gardening', 'Organize', 'Dusting', 'Vacuuming', 'Make_Bed',
    'Sort_Mail', 'Write_Journal', 'Stretching', 'Prepare_Snack', 'Brush_Teeth', 'Wash_Face', 'Comb_Hair', 'Shave', 'Put_On_Shoes', 'Take_Off_Shoes',
    'Check_Calendar'
]

def generate_normalized_adl_shares() -> Dict[str, float]:
    """
    41개 활동의 일간 점유율 총합이 정확히 100.00%를 만족하도록 디렉션 노이즈를 주입하고 정규화합니다.
    """
    raw_shares: Dict[str, float] = {}
    
    # 1단계: 주요 활동에 높은 기본 점유시간 분배
    base_shares = {
        'Sleep': 33.0,     # 약 8시간
        'Rest': 15.0,      # 약 3.6시간
        'Watch_TV': 12.0,  # 약 2.8시간
        'Go_Out': 10.0,    # 약 2.4시간
        'Cook': 6.0,       # 약 1.4시간
        'Eat': 5.0,        # 약 1.2시간
        'Shower': 3.0,     # 약 40분
    }
    
    total_assigned = 0.0
    for act in CASAS_41_ACTIVITIES:
        if act in base_shares:
            # 약간의 가우시안 노이즈 주입
            val = max(1.0, base_shares[act] + random.uniform(-1.5, 1.5))
            raw_shares[act] = val
        else:
            # 마이너 활동들은 매우 작은 기초 시간 분배
            raw_shares[act] = max(0.1, random.uniform(0.1, 0.5))
        total_assigned += raw_shares[act]
        
    # 2단계: 합산 100.00%로 강제 정규화 스무딩 필터 적용
    normalized_shares: Dict[str, float] = {}
    running_sum = 0.0
    for i, act in enumerate(CASAS_41_ACTIVITIES):
        if i == len(CASAS_41_ACTIVITIES) - 1:
            # 마지막 요소는 누적 오차를 반영하여 정확히 100.00%에 도달하도록 보정
            normalized_shares[act] = round(100.0 - running_sum, 2)
        else:
            share = round((raw_shares[act] / total_assigned) * 100.0, 2)
            normalized_shares[act] = share
            running_sum += share
            
    return normalized_shares

def seed_database(db_path: Optional[str] = None, force: bool = True) -> None:
    """
    초기 개발 및 데모 시연을 위한 모의 시드 데이터를 영속 테이블에 안전하게 주입합니다.
    force=True인 경우 기존 테이블 데이터를 모두 초기화하고 다양한 상태의 주민 5명을 적재합니다.
    수집된 ADL 시계열 데이터를 기반으로 AI 이상 감지 유스케이스를 실행하여 anomaly_reports 및 alerts를 기입합니다.
    """
    resolved_path = db_path or os.environ.get("DATABASE_PATH", "care_system.db")
    db = DatabaseConnector(resolved_path)
    
    # 0단계: 기존 데이터 초기화 및 강제 재적재 설정
    with db.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM residents;").fetchone()[0]
        if count > 0 and not force:
            # 이미 시딩이 완료되었고 강제 덮어쓰기가 비활성화된 경우 무시
            return
        if force:
            # 기존 데이터를 초기화하여 무결한 리시딩 보장
            conn.execute("DELETE FROM caregiver_alerts;")
            conn.execute("DELETE FROM anomaly_reports;")
            conn.execute("DELETE FROM daily_adl_summaries;")
            conn.execute("DELETE FROM casas_sensor_events;")
            conn.execute("DELETE FROM residents;")
            conn.commit()

    # 5명의 다채로운 모의 노인 시나리오 정의
    residents_scenarios = [
        {
            "virtual_code": "RES-MASK-2026A",
            "status": "DANGER",
            "anomaly_type": "INSOMNIA", # 심각한 수면 장애 시나리오
            "desc": "고독사 고위험 관찰 대상자 (불면증 및 급격한 식사량 유실)"
        },
        {
            "virtual_code": "RES-MASK-2026B",
            "status": "NORMAL",
            "anomaly_type": "NONE", # 건강하고 규칙적인 노인
            "desc": "지극히 규칙적이고 건강한 일상을 보내는 피돌봄 노인"
        },
        {
            "virtual_code": "RES-MASK-2026C",
            "status": "WARNING",
            "anomaly_type": "ISOLATION", # 급격한 외출 중단 및 고립 시나리오
            "desc": "사회적 고립 경고 대상자 (외출 급감 및 실내 누워있는 시간 급증)"
        },
        {
            "virtual_code": "RES-MASK-2026D",
            "status": "NORMAL",
            "anomaly_type": "NONE",
            "desc": "자연스러운 생활 노이즈 수준의 정상 범주 노인"
        },
        {
            "virtual_code": "RES-MASK-2026E",
            "status": "WARNING",
            "anomaly_type": "MALNUTRITION", # 조리 및 식사 유실 시나리오
            "desc": "식생활 관리 경고 대상자 (조리 및 식사 시간 급감, 영양 불균형 우려)"
        }
    ]

    start_date = date.today() - timedelta(days=30)

    for scenario in residents_scenarios:
        resident_id = str(uuid.uuid4())
        virtual_code = scenario["virtual_code"]
        db.insert_resident(resident_id, virtual_code, scenario["status"])

        # 1. 30일 동안의 일별 ADL 점유율 요약 데이터 생성하여 DB 적재
        for d in range(30):
            target_date = start_date + timedelta(days=d)
            shares = generate_normalized_adl_shares()

            # 시나리오별 후반부(최근 5일) 특이 패턴 및 인공 노이즈 주입
            if d >= 25:
                if scenario["anomaly_type"] == "INSOMNIA":
                    shares['Sleep'] = max(8.0, shares.get('Sleep', 33.0) - 18.0)
                    shares['Rest'] = shares.get('Rest', 15.0) + 12.0
                    shares['Eat'] = max(0.5, shares.get('Eat', 5.0) - 3.8)
                elif scenario["anomaly_type"] == "ISOLATION":
                    shares['Go_Out'] = max(0.0, shares.get('Go_Out', 10.0) - 9.5)
                    shares['Sleep'] = shares.get('Sleep', 33.0) + 8.0
                    shares['Rest'] = shares.get('Rest', 15.0) + 5.0
                elif scenario["anomaly_type"] == "MALNUTRITION":
                    shares['Cook'] = max(0.5, shares.get('Cook', 6.0) - 5.0)
                    shares['Eat'] = max(0.5, shares.get('Eat', 5.0) - 4.2)
                    shares['Rest'] = shares.get('Rest', 15.0) + 9.2

                # 41개 ADL 점유비 총합 100.00% 재규격화 강제 적용
                total = sum(shares.values())
                running_sum = 0.0
                keys = list(shares.keys())
                for i, k in enumerate(keys):
                    if i == len(keys) - 1:
                        shares[k] = round(100.0 - running_sum, 2)
                    else:
                        shares[k] = round((shares[k] / total) * 100.0, 2)
                        running_sum += shares[k]

            summary_id = str(uuid.uuid4())
            db.insert_daily_adl_summary(
                id=summary_id,
                resident_id=resident_id,
                date_val=target_date,
                activity_shares=shares,
                is_normalized=True
            )

    # 2단계: 실증 AI 이상 감지 오케스트레이션 유스케이스 트리거
    # (하드코딩 기입을 전면 제거하고, 데이터베이스에서 실측 시계열을 직접 '읽어와서' 
    #  AttentionRNN 예측, Double-Step 판별 및 Gemini XAI 보고서 자동 작성을 완수합니다)
    from src.usecases.run_anomaly_detection import RunAnomalyDetectionUseCase
    from src.infrastructure.persistence.sqlite_care_repository import SQLiteCareRepository
    
    repository = SQLiteCareRepository(db)
    usecase = RunAnomalyDetectionUseCase(repository)
    print("\n[AI Anomaly Detection & XAI Pipeline Triggered]")
    print("-> 데이터베이스로부터 시계열을 '읽어와서' AI 분석 및 실증 보고서를 생성합니다.")
    
    with db.get_connection() as conn:
        all_residents = conn.execute("SELECT id, virtual_code FROM residents;").fetchall()
        
    for r_id, code in all_residents:
        print(f" - 분석 대상 피돌봄 노인 구동: {code}")
        try:
            # 실증 데이터 기반의 로직 분석 및 LLM API 동적 생성/적재 전개
            usecase.execute(resident_id=r_id, target_date=date.today())
        except Exception as e:
            print(f"   [WARNING] {code} 이상 보고서 생성 실패: {str(e)}")

if __name__ == "__main__":
    seed_database()
