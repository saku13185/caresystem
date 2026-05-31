# 프로젝트 컨텍스트 상태 관리 패킷 (context_packet)

본 문서는 프로젝트의 현재 진행 단계, 컨텍스트 요약, 그리고 다음 마일스톤을 실시간으로 추적하여 상태의 일관성을 유지하기 위해 작성되었습니다.

---

## 1. 현재 프로젝트 상태 마킹

* **대단계**: Phase 7 - 破損ファイル復元および第1次動作検証の完了 (Verification & Recovery Complete)
* **소단계**: 자동 복구를 통한 코드 정상화, JSON 직렬화 경고 해결 및 5대 검증 통과 (8/8 Passed)
* **최종 업데이트 시점**: 2026-05-31T20:10:00+09:00
* **상태 요약**: Google Drive 다운로드 오류로 인해 HTML 경고문으로 덮어씌워졌던 11개의 주요 Python 소스코드를 전면 복원 완료함. 로컬 가상환경(`.venv`)을 구성하여 의존성 라이브러리를 정상 설치하였으며, `pytest`를 통한 자동 검증 결과 8개 테스트 케이스가 100% 통과함. 모의 DB 시딩(`seed_data.py`)을 통해 5명의 시나리오별 데이터를 SQLite에 성공적으로 적재하고 Streamlit 대시보드(`localhost:8501`)의 실행 및 초기 연동 무결성을 확인 완료함. 이 과정에서 발견된 `float32` 타입의 JSON 직렬화 에러를 `db_connector.py` 내의 안전 변환 헬퍼(to_native_types) 구현을 통해 최종 해결함.

---







## 2. 기획 및 이해관계자 컨텍스트 요약

```mermaid
graph TD
    SubGraph_Human[인간 이해관계자]
    SubGraph_Agent[시스템 에이전트]

    Elderly[독거노인: 비활성 행위자] -->|ADL 행동 패턴 수집| Gen[합성 데이터 제너레이터]
    Gen -->|가상 시계열 데이터| RNN[AttentionRNN 예측기]
    RNN -->|예측 & 어텐션 가중치| Classifier[Double-step 분류기]
    Classifier -->|위험도 등급 패킷| LLM[LLM XAI 추론기]
    LLM -->|자연어 보고서| SW[사회복지사: 최상위 의사결정 및 승인 권한]
    SW -->|승인된 정제된 보고서| Guardian[보호자: 제한적 1인 조회 권한]
```

### 2.1. 요구사항 및 BDD 수용 기준 바인딩 요약
1. [FR-01/Scenario 1] 시계열 합성 데이터 정규화:
   - CASAS 41개 ADL 일간 점유율 합성 시 시나리오 주입 기능을 확보해야 하며, 생성된 데이터의 일일 총합은 강제 정규화를 통해 정확히 100.00% (오차 범위 0.01% 이내)의 무결성을 만족해야 함.
2. [FR-02/Scenario 2] AttentionRNN 15일 윈도우 예측:
   - (Batch, 15, 41) 규격의 시계열 데이터를 처리하여 16일 차 예측 텐서 (Batch, 41) 및 15일 가중 기여도를 나타내는 Attention weight를 정상 산출해야 함.
3. [FR-03/FR-04/Scenario 3] Double-step 판정 및 LLM XAI 보고서 자동 연계:
   - 예측-실측 간 MAE 오차의 Z-score 1차 검증(Z > 2.5일 시 고위험) 및 역사적 Boxplot IQR 영역 2차 검증을 거친 후, LLM이 환각 없이 사실에만 기반하여 "의료적 최종 진단 아님" 헤더 문구를 포함한 자연어 한글 보고서를 최종 출력해야 함.
4. [NFR-01/02/03] 주요 품질 속성 제약:
   - 딥러닝 추론 속도 100ms 이내, LLM 생성 속도 5초(상용)/15초(로컬) 이내 보장.
   - 단선 시 최근 3일간의 행동 데이터 가중평균값(0.5, 0.25, 0.25)으로 결측치 자동 대체 보강(Imputation).
   - 모든 XAI 리포트에는 개인식별정보(PII) 조회를 완전 차단하고, 익명 UUID v4 체계로 분석 정보를 전달해야 함.

### 2.2. MVP 개발 범위 및 아키텍처 제약조건 동결 (Context Freeze Payload)
* MVP 필수 구현 (Must-Have): CASAS 41개 ADL 일간 점유율 합성 제너레이터, AttentionRNN 훈련 및 추론 파이프라인, Z-score + Boxplot IQR 이중 이상 탐지, LLM 돌봄 보고서 XAI 추론기, Streamlit 복지사 웹 대시보드 UI.
* MVP 강력 제외 (Won't-Have): 스마트홈 물리 하드웨어 센서 및 실시간 수집 연동, OAuth2 고도화 다중 권한 보안 레이어, 모바일 기기(iOS/Android) 이식 패키징, 실시간 분산 스트리밍(Kafka 등) 프레임워크 설계.

### 2.3. 도메인 개념 모델 구조 (DDD Aggregates Structure)
```mermaid
classDiagram
    class Resident {
        <<Aggregate Root>>
        +UUID id
        +String virtualCode
        +RiskStatus currentStatus
    }
    class DailyADLSummary {
        <<Entity>>
        +Date date
        +Map activityShares
    }
    class AnomalyReport {
        <<Aggregate Root>>
        +UUID id
        +Float zScore
        +RiskStatus status
        +List attentionWeights
    }
    class BoxplotViolation {
        <<Value Object>>
        +ActivityLabel activityLabel
        +OutlierType type
    }
    class CaregiverAlert {
        <<Aggregate Root>>
        +UUID id
        +AlertStatus actionStatus
        +String feedbackMessage
    }

    Resident "1" *-- "0..*" DailyADLSummary
    AnomalyReport "1" *-- "0..*" BoxplotViolation
    AnomalyReport "1" -- "1" Resident
    CaregiverAlert "1" -- "1" AnomalyReport
```

### 2.4. 시스템 아키텍처 및 의존성 가이드라인 (Architecture Guidelines)
* 의존성 단방향 제약: domain -> usecases -> infrastructure / presentation 단방향 흐름 고수. 도메인 코어는 다른 어떠한 레이어도 임포트하거나 참조하지 않고 순수 파이썬 데이터 구조 및 도메인 규칙만 포함함.
* 외부 프레임워크 격리: PyTorch 기계학습 모듈, OpenAI SDK 클라이언트, Streamlit 웹 컴포넌트는 전적으로 infrastructure/ 및 presentation/ 내부 어댑터에 한정 은닉되며, usecases/는 추상 포트 인터페이스를 정의해 이들을 약결합으로 소비 제어함.
* 배치 프로세싱 동결: 실시간 스트리밍 분석을 영구 배제하며, 자정 배치 동작으로 데이터를 파싱하고 이상치를 CSV 영속성 저장소에 기록하는 동기 파일 처리 방식을 채택함.

### 2.5. 물리 데이터베이스 테이블 요약 및 성능 인덱스 가이드 (Database Physical Guidelines)
* 릴레이션 격리 규칙: 모든 주민 데이터 및 예측 결과에는 UUID v4 난수를 PK로 연동하고 실제 개인 정보(PII) 수집을 전면 차단함.
* 시계열 인덱스 강제: 15일 슬라이딩 윈도우 조회를 위한 복합 인덱스 idx_adl_summary_resident_date(resident_id, date) 및 로우 레벨 이벤트 전처리를 위한 idx_sensor_events_resident_time(resident_id, timestamp)를 물리 저장소 구동 수준에서 필히 활성화하여 쿼리 레이턴시를 10ms 이하로 통제함.
* 데이터 보존 정책 (TTL): 일간 전처리 요약 데이터는 최소 3개년(1095일) 보존하며, 30일 경과한 로우 레벨 가상 센서 로그는 매일 자정 퍼지 삭제 조치하여 디스크 비대화를 차단함.

### 2.6. 세부 개발 작업 맵 및 Blocker 현황 요약 (Sprint Task Matrix)
* Task 1 (최선행 Blocker): DB DDL 셋업 및 41개 ADL 점유비 합성 제너레이터 구현 (Scenario 1 정밀도 100% 검증).
* Task 2: 3일 결측 가중평균 Imputation 및 PyTorch AttentionRNN 15일 윈도우 시계열 모델 훈련/추론 모듈 구현 (Scenario 2 검증).
* Task 3: MAE Z-score 및 Boxplot IQR Double-step 판별 분류기 및 LLM XAI 자연어 보고서 생성 어댑터 완성 (Scenario 3 검증).
* Task 4: Streamlit 모니터링 UI 및 피드백 DB 바인딩 완료 (UI 영속성 최종 통합 검증).
* 개발 제약: Task 1 완료 전에는 Task 2의 시계열 예측 훈련을 전개할 수 없음. UI(Task 4)는 Mock 전처리 패킷으로 병렬 개발 보장.

### 2.7. 에이전트 코딩 프롬프트 명세 및 아키텍처 하드 리미트 (Implementation Prompts Matrix)
* task_1_prompt.md: DB 물리 스키마 DDL 셋업 및 41개 ADL 합산 100% 정규화 보장 가상 생성 시뮬레이터 (PII 차단, UUID v4 연동, Scenario 1 통과 의무).
* task_2_prompt.md: 최근 3일 결측 가중평균 Imputation 및 과거 15일 윈도우 (Batch, 15, 41) PyTorch AttentionRNN 16일 차 예측 (Batch, 41) 및 (Batch, 15) Attention 가중치 추출 (Scenario 2 통과 의무).
* task_3_prompt.md: MAE 오차 Z-score 연산 및 개별 Boxplot IQR 이탈 Double-step 이상치 검사, 위험 등급(0/1/2) 산정, LLM XAI 보고서 자동 생성 (의료 경고문 문두 하드코딩 표출, PII 완전 차단, API Fallback 텍스트 탑재, Scenario 3 통과 의무).
* task_4_prompt.md: Streamlit 반응형 단일 웹 UI, 다크모드 글라스모피즘 HSL 컬러 테마 적용, 위험 등급별 보드, 어텐션/편차 시각화, 복지사 정오탐 피드백 기입 즉시 SQLite 실시간 바인딩 영속 저장 (UI 통합 검증 통과 의무).

---

## 3. Next 마일스톤 (Next Milestones)

* **차기 진행 예정 작업**: Phase 8 - Google GenAI / OpenAI API 키 연동 가이드 문서화 및 환경 정비
  * **목표**: API 키 미설정 상태에서의 Fallback 작동 시나리오와 실측 API 연동 매뉴얼을 작성하여, 신규 개발자가 환경변수(`.env`) 설정을 원활히 마칠 수 있도록 가이드 문서 고도화.
  * **주요 산출물**: API 키 연동 지침이 추가된 `README.md` 및 배포 인수 인계 보고서.
