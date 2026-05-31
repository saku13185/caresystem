# [구현 지시서] Task 1: DB 물리 스키마 세팅 및 가상 데이터 시뮬레이터 개발

본 문서는 예방적 돌봄 AI 에이전트 시스템의 **Task 1: 데이터베이스 세팅 및 가상 ADL 합성 데이터 제너레이터**를 개발 중 환각 없이 완벽하게 구현하기 위한 상세 코딩 지시서입니다.

---

## 1. 아키텍처적 목적 및 맥락 격리

* **수정/신규 대상 파일**: 
  - [NEW] `src/domain/resident.py` (도메인 엔터티)
  - [NEW] `src/infrastructure/persistence/db_connector.py` (SQLite DDL 실행 및 연결 관리 어댑터)
  - [NEW] `src/infrastructure/generators/synthetic_generator.py` (합성 데이터 시뮬레이터 구현체)
  - [NEW] `tests/test_generators.py` (BDD Scenario 1 검증 하네스)
* **금지 사항 (하드 리미트)**:
  - 실제 IoT 물리 스마트 센서 연동 프로토콜, 소켓 리스너 등 하드웨어 연동 라이브러리를 임포트하거나 구현하는 것을 엄격히 금지합니다.
  - 노인의 성명, 주민등록번호, 연락처 등 고유식별정보(PII) 컬럼 설계를 배제하며, 모든 노인은 난수화된 가상 ID(`UUID v4`)로 대체 격리되어야 합니다.

---

## 2. 하드웨어 제약 및 입력/출력 규격

### 2.1. 데이터베이스 스키마 제약
* **SQLite 물리 테이블 구성**: 
  - `residents` (id: UUID v4 PK, virtual_code: VARCHAR UNIQUE, current_status: VARCHAR)
  - `casas_sensor_events` (id: BIGINT PK AUTO_INCREMENT, resident_id: UUID FK, timestamp: TIMESTAMP, sensor_location: VARCHAR, sensor_status: VARCHAR, activity_label: VARCHAR)
  - `daily_adl_summaries` (id: UUID PK, resident_id: UUID FK, date: DATE, activity_shares: JSON, is_normalized: BOOLEAN)
* **성능 인덱스 설정**: 
  - 15일 슬라이딩 윈도우 조회를 위한 복합 인덱스 `idx_adl_summary_resident_date(resident_id, date)` 및 로우 레벨 이벤트 전처리를 위한 `idx_sensor_events_resident_time(resident_id, timestamp)`를 DDL 수준에서 활성화해야 함.

### 2.2. 시뮬레이터 입출력 규격
* **입력 파라미터 (Input parameters)**:
  - `resident_id` (UUID): 대상 노인의 가상 식별자
  - `days_to_generate` (INT): 합성 데이터를 생성할 일수 (기본값: 30일)
  - `scenario_type` (String): 주입할 행동 장애 변이 종류 ('normal', 'insomnia', 'meals_skipped')
* **출력 규격 (Output interfaces)**:
  - 생성 완료 시 `daily_adl_summaries` 테이블에 일별로 데이터를 자동 적재하고, 저장된 CSV 파일 또는 DB 덤프를 반환합니다.
  - 하루 41개 일상 활동 점유비의 총합은 정확히 **$100.00\%$ (통계 오차 허용 한계 $\pm 0.01\%$)**로 소수점 보정 필터(Normalization)가 적용되어야 합니다.

---

## 3. 에러 처리 및 Fallback 규칙

* **오차 보정 예외**: 41개 활동 생성 후 총합이 $100\%$를 이탈하는 수치 오차가 발생할 시, 임의의 활동 값을 스무딩 절삭하여 강제로 $100.00\%$를 보정하는 보정 로직을 포함시켜 파일 손상을 원천 방지합니다.
* **DB 커넥션 예외**: SQLite 파일 잠김(Database is locked) 등의 디바이스 I/O 예외 발생 시, 최대 3회 재시도(Retry with Backoff) 후 에러 로그를 남기고 작업을 안전하게 예외 격리합니다.

---

## 4. BDD 기반 수용 기준 및 테스트 코드 구조

### [BDD Scenario 1]
* **Given**: 합성 데이터 생성기가 특정 독거노인의 불면증 시나리오 파라미터를 입력받아 41개 핵심 ADL 일간 시간 점유율(%) 시계열 데이터를 30일치 동적 생성했을 때
* **When**: 생성된 파일 내 1일 차부터 30일 차까지 각 날짜별 41개 활동 점유율 백분율 수치의 합산값을 검증하는 정합성 스크립트를 구동했을 때
* **Then**: 모든 일자에 대한 활동 점유율 합이 오차 범위를 만족하는 **정확히 $100.00\% \pm 0.01\%$**로 정상 보정되고 에러가 반환되지 않아야 합니다.

### [실행 가능 테스트 코드 스켈레톤]
```python
# tests/test_generators.py
import pytest
from src.infrastructure.generators.synthetic_generator import SyntheticGenerator

def test_synthetic_data_normalization():
    generator = SyntheticGenerator()
    # Given
    resident_id = "test-uuid-1234"
    days = 30
    
    # When
    data = generator.generate_adl_shares(resident_id=resident_id, days=days, scenario='insomnia')
    
    # Then
    for day_data in data:
        total_share = sum(day_data['activity_shares'].values())
        assert abs(total_share - 100.0) <= 0.01, f"Normalization error at date {day_data['date']}: {total_share}%"
```
