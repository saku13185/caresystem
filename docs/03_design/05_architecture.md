# 시스템 아키텍처 설계서 (System Architecture Design)

본 문서는 예방적 돌봄 AI 에이전트 시스템의 요구사항 및 도메인 모델을 기술적으로 만족하고 계층 간 의존성 제어를 극대화하기 위해, 클린/헥사고날 아키텍처(Clean/Hexagonal Architecture) 개념을 적용하여 서브시스템 경계, 폴더 구조, 그리고 시퀀스 다이어그램을 설계한 내역을 기록합니다.

---

## 1. 아키텍처 개요 및 계층 분리 규칙

의존성의 방향은 외부(프레임워크, 라이브러리, 입출력 장치)에서 내부(도메인 엔터티, 순수 비즈니스 규칙)로만 향하며, 핵심 비즈니스 로직은 어떠한 외부 기술(데이터베이스 종류, 프론트엔드 프레임워크, 외부 API 통신 규격)에도 종속되지 않도록 격리 설계합니다.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER (Adapters)                │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                     USE CASES LAYER (Ports)                    │   │
│   │   ┌────────────────────────────────────────────────────────┐   │   │
│   │   │                     DOMAIN CORE LAYER                  │   │   │
│   │   │   * Resident Entity                                    │   │   │
│   │   │   * DailyADLSummary Entity                             │   │   │
│   │   │   * AnomalyReport Aggregate (zScore, XAI)              │   │   │
│   │   │   * CaregiverAlert Aggregate                           │   │   │
│   │   └────────────────────────────────────────────────────────┘   │   │
│   │   * RunAnomalyDetectionUseCase                             │   │   │
│   │   * GenerateXaiReportUseCase                               │   │   │
│   │   * SupplySyntheticDataUseCase                             │   │   │
│   └────────────────────────────────────────────────────────────────┘   │
│   * PyTorch AttentionRNN Model Impl                            │   │
│   * CSV File Storage Reader/Writer                             │   │
│   * OpenAI/Local LLM Client                                    │   │
│   * Streamlit Web Presentation Dashboard                       │   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 폴더 트리 구조 (Folder Tree Structure)

MVP의 신속한 구현과 명확한 계층 분리를 지원하는 파이썬 기반 폴더 구조를 아래와 같이 동결합니다.

```
d:\연구실\연구\스마트시티개론\
├── docs/                             # 기획, 요구사항, 설계 마크다운 문서 저장소
│   ├── 00_context_management/        # 상태 관리 (DECISIONS, context_packet 등)
│   ├── 01_goals/                     # 기획 목표 및 이해관계자 정의서
│   ├── 02_requirements/              # 요구사항 명세서 및 MVP 스코프 정의서
│   └── 03_design/                    # 도메인 모델 및 아키텍처 설계서
├── src/                              # 시스템 실행 소스코드 루트
│   ├── domain/                       # DDD 도메인 레이어 (순수 비즈니스 로직, 외부 라이브러리 의존성 제로)
│   │   ├── __init__.py
│   │   ├── resident.py               # Resident, DailyADLSummary, SensorEvent 엔터티
│   │   ├── anomaly.py                # AnomalyReport 엔터티, BoxplotViolation 밸류 오브젝트
│   │   └── alert.py                  # CaregiverAlert 엔터티 및 상태 분류값
│   ├── usecases/                     # 애플리케이션 유스케이스 레이어 (동작 흐름 오케스트레이션 및 포트 선언)
│   │   ├── __init__.py
│   │   ├── supply_synthetic_data.py  # 합성 데이터 생성 흐름
│   │   ├── preprocess_adl_data.py    # 데이터 전처리 및 결측치 가중평균 보강 실행
│   │   ├── run_anomaly_detection.py  # AttentionRNN 추론 및 Double-step 검증 실행
│   │   └── generate_xai_report.py    # LLM XAI 돌봄 요약 보고서 도출 실행
│   ├── infrastructure/               # 인프라스트럭처 레이어 (세부 외부 기술 어댑터 구현체)
│   │   ├── __init__.py
│   │   ├── generators/               # CASAS 표준 규격 합성 데이터 동적 제너레이터 엔진
│   │   ├── models/                   # PyTorch 기반 AttentionRNN 신경망 아키텍처 및 훈련 모듈
│   │   ├── scorers/                  # Z-score 및 Boxplot IQR 이상치 스코어링 모듈
│   │   ├── llm/                      # API 통신 클라이언트 및 XAI 프롬프트 엔지니어링 템플릿
│   │   └── persistence/              # CSV 파일 입출력 및 메모리 버퍼 윈도우 관리 어댑터
│   └── presentation/                 # 표현 레이어 (사용자 화면 인터페이스)
│       ├── __init__.py
│       └── app.py                    # Streamlit 기반 예방 돌봄 대시보드 메인 진입점
├── tests/                            # BDD 시나리오 기반의 테스트 하네스 검증 코드
│   ├── test_generators.py            # 합성 데이터 정규화 및 수치 정합성 테스트
│   ├── test_models.py                # AttentionRNN 모델 입출력 텐서 및 가중치 추출 테스트
│   └── test_usecases.py              # 유스케이스 결측치 보강 및 예외 처리 흐름 테스트
└── requirements.txt                  # MVP 기술 스택 의존성 패키지 명세서
```

---

## 3. 파이프라인 시퀀스 다이어그램 (Sequence Diagram)

매일 자정 배치 스케줄러에 의해 동작하는 합성 데이터 생성부터 사회복지사 피드백까지의 엔드투엔드(End-to-End) 데이터 흐름과 호출 구조를 도식화합니다.

```mermaid
sequenceDiagram
    autonumber
    actor SW as 사회복지사 (Streamlit Dashboard)
    participant UC as run_anomaly_detection (UseCase)
    participant Gen as Synthetic Generator (Infra)
    participant Prep as Data Preprocessor (UseCase)
    participant RNN as AttentionRNN Predictor (Infra)
    participant Scorer as Double-step Scorer (Infra)
    participant LLM as LLM XAI Agent (Infra)
    participant Storage as CSV File Storage (Infra)

    Note over UC: 매일 자정 배치 스케줄러 트리거 동작
    UC->>Gen: 1. 일간 합성 데이터 생성 요청 (시나리오 주입)
    Gen->>Storage: 2. 생성된 CASAS 모사 원천 데이터 저장 (CSV)
    UC->>Prep: 3. 최근 16일치 데이터 로드 및 전처리 요청
    Prep->>Storage: 4. 16일치 ADL 점유비 파일 조회
    Storage-->>Prep: 5. ADL 점유비 반환
    Note over Prep: [EXCEPTION-01] 결측치 발견 시<br/>최근 3일 가중평균값으로 Imputation 보강
    Prep-->>UC: 6. 전처리 및 정규화 완료된 15일 윈도우 & 16일 차 실측 패킷 반환

    UC->>RNN: 7. 과거 15일 시계열 데이터 입력 (Batch, 15, 41)
    RNN-->>UC: 8. 16일 차 예측 텐서 (Batch, 41) & Attention 가중치 (Batch, 15) 반환
    
    UC->>Scorer: 9. 예측치와 16일 차 실측치 비교 스코어링 요청
    Note over Scorer: [Double-step Anomaly]<br/>1단계: MAE 오차 Z-score 연산<br/>2단계: 개별 활동 Boxplot IQR 아웃라이어 위반 체크
    Scorer-->>UC: 10. 위험 등급 판정 결과 반환 (정상/주의/고위험)

    alt 위험 등급이 [주의] 또는 [고위험]인 경우
        UC->>LLM: 11. XAI 자연어 보고서 작성 요청 (Z-score, IQR, 어텐션 가중치 context 주입)
        Note over LLM: [NFR-03-01] 최상단 헤더 영역에<br/>"의료적 최종 판단 아님" 경고 문구 하드코딩 표출
        LLM-->>UC: 12. 한국어 설명 보고서 텍스트 반환
    else 정상인 경우
        Note over UC: XAI 생성 생략, 빈 보고서 세팅
    end

    UC->>Storage: 13. 최종 AnomalyReport & CaregiverAlert 영속화 (CSV)
    
    Note over SW: 복지사가 아침 출근 후 대시보드 웹을 로드
    SW->>Storage: 14. 위험군 노인 리스트 및 이상 분석 조회
    Storage-->>SW: 15. 시각화 차트 및 한글 XAI 리포트 카드 제공
    SW->>Storage: 16. 보호자 경보 전송 승인(Approve) 및 정탐/오탐 피드백 메모 저장
```
