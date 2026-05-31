import sqlite3
import json
import os
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import date, datetime

def to_native_types(obj: Any) -> Any:
    """
    numpy 데이터 타입을 Python 표준 데이터 타입으로 재귀적 변환
    """
    if isinstance(obj, dict):
        return {k: to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_native_types(x) for x in obj]
    elif isinstance(obj, tuple):
        return tuple(to_native_types(x) for x in obj)
    elif isinstance(obj, np.ndarray):
        return to_native_types(obj.tolist())
    elif isinstance(obj, np.generic):
        return obj.item()
    return obj

class DatabaseConnector:
    """
    SQLite 데이터베이스 커넥터 및 DDL 실행 어댑터
    """
    def __init__(self, db_path: Optional[str] = None):
        # SQLite 파일 저장 경로 설정 (DATABASE_PATH 환경변수가 있으면 우선 사용)
        self.db_path = db_path or os.environ.get("DATABASE_PATH", "care_system.db")
        
        # DB 파일의 부모 디렉터리가 존재하지 않는 경우 자동 생성
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        # 데이터베이스 및 테이블 초기화 수행
        self.initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """
        데이터베이스 커넥션을 안전하게 획득합니다.
        SQLite 다중 세션 락(Lock) 충돌 방지를 위해 타임아웃을 30초로 설정합니다.
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        # 외래키 제약조건(Foreign Key Constraint) 활성화
        conn.execute("PRAGMA foreign_keys = ON;")
        # 결과를 딕셔너리 포맷으로 파싱하도록 설정
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self) -> None:
        """
        물리 스키마 DDL 스크립트를 실행하여 테이블 및 고속 조회 인덱스를 생성합니다.
        """
        ddl_queries = [
            # 1. 피돌봄 노인 마스터 테이블
            """
            CREATE TABLE IF NOT EXISTS residents (
                id VARCHAR(36) PRIMARY KEY,
                virtual_code VARCHAR(50) UNIQUE NOT NULL,
                current_status VARCHAR(20) NOT NULL DEFAULT 'NORMAL',
                registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 2. CASAS 가상 원시 센서 이벤트 로그 테이블
            """
            CREATE TABLE IF NOT EXISTS casas_sensor_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resident_id VARCHAR(36) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                sensor_location VARCHAR(50) NOT NULL,
                sensor_status VARCHAR(10) NOT NULL,
                activity_label VARCHAR(50) NOT NULL,
                FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
            );
            """,
            # 3. 일별 전처리 ADL 점유율 요약 테이블
            """
            CREATE TABLE IF NOT EXISTS daily_adl_summaries (
                id VARCHAR(36) PRIMARY KEY,
                resident_id VARCHAR(36) NOT NULL,
                date DATE NOT NULL,
                activity_shares TEXT NOT NULL, -- 41개 활동 및 점유 비율을 JSON 문자열로 저장
                is_normalized BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
            );
            """,
            # 4. 이상 탐지 결과 및 LLM XAI 분석 보고서 테이블
            """
            CREATE TABLE IF NOT EXISTS anomaly_reports (
                id VARCHAR(36) PRIMARY KEY,
                resident_id VARCHAR(36) NOT NULL,
                analysis_date DATE NOT NULL,
                z_score REAL NOT NULL,
                status VARCHAR(20) NOT NULL,
                attention_weights TEXT NOT NULL, -- 15일 가중치 배열을 JSON 문자열로 저장
                boxplot_violations TEXT NOT NULL, -- Boxplot 이탈 목록을 JSON 문자열로 저장
                xai_report_content TEXT,
                is_xai_generated BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
            );
            """,
            # 5. 사회복지사용 경보 및 피드백 처리 테이블
            """
            CREATE TABLE IF NOT EXISTS caregiver_alerts (
                id VARCHAR(36) PRIMARY KEY,
                anomaly_report_id VARCHAR(36) NOT NULL,
                action_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                feedback_message TEXT,
                alert_sent_at TIMESTAMP,
                FOREIGN KEY (anomaly_report_id) REFERENCES anomaly_reports(id) ON DELETE CASCADE
            );
            """,
            # 6. 복합 인덱스 (조회 성능 최적화)
            # 센서 이벤트 집계 연산 성능 개선을 위한 복합 인덱스
            "CREATE INDEX IF NOT EXISTS idx_sensor_events_resident_time ON casas_sensor_events(resident_id, timestamp);",
            # 15일 슬라이딩 윈도우 조회를 위한 복합 인덱스
            "CREATE INDEX IF NOT EXISTS idx_adl_summary_resident_date ON daily_adl_summaries(resident_id, date);",
            # 노인별 이상 보고서 조회 최적화 인덱스
            "CREATE INDEX IF NOT EXISTS idx_anomaly_report_resident_date ON anomaly_reports(resident_id, analysis_date);"
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for query in ddl_queries:
                cursor.execute(query)
            conn.commit()

    # --- CRUD Helper Methods ---

    def insert_resident(self, id: str, virtual_code: str, current_status: str = "NORMAL") -> None:
        """
        신규 피돌봄 노인 비식별 마스터 정보를 추가합니다.
        """
        query = "INSERT INTO residents (id, virtual_code, current_status) VALUES (?, ?, ?);"
        with self.get_connection() as conn:
            conn.execute(query, (id, virtual_code, current_status))
            conn.commit()

    def get_resident(self, resident_id: str) -> Optional[Dict[str, Any]]:
        """
        피돌봄 노인의 현재 비식별 상태 정보를 단건 조회합니다.
        """
        query = "SELECT * FROM residents WHERE id = ?;"
        with self.get_connection() as conn:
            row = conn.execute(query, (resident_id,)).fetchone()
            return dict(row) if row else None

    def update_resident_status(self, resident_id: str, status: str) -> None:
        """
        피돌봄 노인의 현재 이상 분류 위험도를 갱신합니다.
        """
        query = "UPDATE residents SET current_status = ? WHERE id = ?;"
        with self.get_connection() as conn:
            conn.execute(query, (status, resident_id))
            conn.commit()

    def insert_daily_adl_summary(self, id: str, resident_id: str, date_val: date, activity_shares: Dict[str, float], is_normalized: bool) -> None:
        """
        일별 전처리 ADL 점유율 요약 레코드를 추가합니다.
        """
        shares_json = json.dumps(to_native_types(activity_shares))
        query = "INSERT INTO daily_adl_summaries (id, resident_id, date, activity_shares, is_normalized) VALUES (?, ?, ?, ?, ?);"
        with self.get_connection() as conn:
            conn.execute(query, (id, resident_id, str(date_val), shares_json, 1 if is_normalized else 0))
            conn.commit()

    def get_daily_adl_summaries(self, resident_id: str, limit_days: int = 15) -> List[Dict[str, Any]]:
        """
        특정 노인의 과거 N일간의 슬라이딩 윈도우용 ADL 요약 데이터를 로드합니다.
        """
        query = "SELECT * FROM daily_adl_summaries WHERE resident_id = ? ORDER BY date DESC LIMIT ?;"
        with self.get_connection() as conn:
            rows = conn.execute(query, (resident_id, limit_days)).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['activity_shares'] = json.loads(item['activity_shares'])
                result.append(item)
            return result

    def insert_anomaly_report(self, report_id: str, resident_id: str, analysis_date: date, z_score: float, status: str, attention_weights: List[float], boxplot_violations: List[Dict[str, Any]], xai_report_content: Optional[str] = None, is_xai_generated: bool = False) -> None:
        """
        이상 탐지 보고서 및 분석 결과를 추가합니다.
        """
        weights_json = json.dumps(to_native_types(attention_weights))
        violations_json = json.dumps(to_native_types(boxplot_violations))
        native_z_score = to_native_types(z_score)
        query = """
            INSERT INTO anomaly_reports (id, resident_id, analysis_date, z_score, status, attention_weights, boxplot_violations, xai_report_content, is_xai_generated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            conn.execute(query, (report_id, resident_id, str(analysis_date), native_z_score, status, weights_json, violations_json, xai_report_content, 1 if is_xai_generated else 0))
            conn.commit()

    def insert_caregiver_alert(self, alert_id: str, anomaly_report_id: str, action_status: str = "PENDING", feedback_message: Optional[str] = None, alert_sent_at: Optional[datetime] = None) -> None:
        """
        비상 돌봄 경보 및 사회복지사 조치 메모 이력을 추가합니다.
        """
        query = "INSERT INTO caregiver_alerts (id, anomaly_report_id, action_status, feedback_message, alert_sent_at) VALUES (?, ?, ?, ?, ?);"
        with self.get_connection() as conn:
            conn.execute(query, (alert_id, anomaly_report_id, action_status, feedback_message, alert_sent_at))
            conn.commit()

    def update_caregiver_feedback(self, alert_id: str, action_status: str, feedback_message: str) -> None:
        """
        사회복지사의 피드백 수집 및 오탐/승인 여부에 대해 상태 및 메모를 업데이트합니다.
        """
        query = "UPDATE caregiver_alerts SET action_status = ?, feedback_message = ? WHERE id = ?;"
        with self.get_connection() as conn:
            conn.execute(query, (action_status, feedback_message, alert_id))
            conn.commit()

    def get_adl_summaries_by_date_range(self, resident_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        특정 기간 동안의 일별 요약 데이터 리스트를 조회합니다.
        """
        query = """
            SELECT date, activity_shares 
            FROM daily_adl_summaries 
            WHERE resident_id = ? AND date BETWEEN ? AND ?
            ORDER BY date ASC;
        """
        with self.get_connection() as conn:
            rows = conn.execute(query, (resident_id, str(start_date), str(end_date))).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['activity_shares'] = json.loads(item['activity_shares'])
                result.append(item)
            return result

    def get_adl_summaries_before_date(self, resident_id: str, before_date: date, limit: int) -> List[Dict[str, Any]]:
        """
        특정 일자 이전의 최근 N일치 일별 요약 데이터 리스트를 조회합니다.
        """
        query = """
            SELECT activity_shares 
            FROM daily_adl_summaries 
            WHERE resident_id = ? AND date < ?
            ORDER BY date DESC LIMIT ?;
        """
        with self.get_connection() as conn:
            rows = conn.execute(query, (resident_id, str(before_date), limit)).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['activity_shares'] = json.loads(item['activity_shares'])
                result.append(item)
            return result
