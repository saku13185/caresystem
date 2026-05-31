# 개발 완료 및 운영 인수 인계 보고서 (Deployment & Handoff Report)

본 문서는 예방적 돌봄 AI 에이전트 시스템의 전체 아키텍처 및 핵심 백엔드/프론트엔드 모듈 개발이 100% 완료됨에 따라, 다른 연구자 및 개발자가 시스템을 로컬/프로덕션 환경에 신속하게 배포하고 운영 및 디버깅을 지속할 수 있도록 데브옵스 인프라 명세와 실행 방법을 자산화한 최종 인도용 가이드입니다.

---

## 1. 프로젝트 핵심 상태 요약 (Development Summary)

본 스마트시티 개론 연구 연계 AI 시스템은 독거노인의 스마트홈 일상생활(ADL) 센서 로그 패턴을 분석하여 고독사 및 우울 이상 패턴을 예방 조기 발견하는 목적을 가집니다.

* **최종 완수 상태**: `Stage 7 - 기술부채 해결 및 최종 프로덕션 동결(Freeze)` 완료.
* **4대 완수 작업 (MVP Sprint Tasks) + 최적화**:
  1. **Task 1 (데이터베이스 및 가상 제너레이터)**: 비식별 SQLite 스키마 구축 및 41개 일상 행동의 총합이 100.00% 정규화 정합성을 갖춘 30일 시계열 데이터 시드 생성 스크립트 구축 완료.
  2. **Task 2 (AttentionRNN 예측 모델)**: 과거 15일 슬라이딩 윈도우 기반 16일 차 41개 ADL 점유비 예측 및 15일간 각 날짜별 기여 중요도(Attention Weights)를 정밀 추출하는 PyTorch GRU 신경망 및 훈련/추론 파이프라인 완수.
  3. **Task 3 (Double-step 스코어링 & LLM XAI)**: 1단계 MAE Z-score 및 2단계 Boxplot IQR 임계 범위 이탈 이중 검증 분류기 탑재 완료 및 의료 disclaimer가 하드코딩된 한글 XAI 리포트 OpenAI API/Fallback 생성기 구축 완수.
  4. **Task 4 (Streamlit 웹 대시보드 UI)**: 다크모드 글라스모피즘 미학 테마 적용, Plotly 어텐션/IQR 시각화 차트 제공, 정오탐 피드백 기입 즉시 SQLite DB 영속성 갱신 연동 완수.
  5. **Task 5 (싱글톤 가중치 캐시 최적화)**: 다중 주민 배치 이상 감지 구동 시 PyTorch 가중치 파일(`attention_rnn.pt`)의 최초 1회 로딩 이후 핫 메모리를 재사용하는 `AttentionRNNModelCache` 모듈을 연동하여 중복 디스크 I/O 병목 제거 완료.
* **BDD 하네스 테스트 결과**: 5대 핵심 지표(데이터 무결성, 모델 오차 바인딩, 임계치 분류 정합성, 설명의 데이터 일치성, 윤리 가드) 자동화 검증을 포함해 전체 BDD/단위 테스트 **100% 통과 (26 passed)**. (복원 후 검증 완수)

---

## 2. 배포 및 운영 인프라 스크립트 명세

프로덕션급의 격리 배포 환경 조성을 위해 Docker 및 Docker Compose 스크립트를 완비하였습니다.

### 2.1. 환경 변수 템플릿 (`.env.example`)
* **GEMINI_API_KEY**: Google Gemini 서비스 호출용 API 키 (AIzaSy...)
* **GEMINI_MODEL**: 사용할 Gemini 모델명 (`gemini-2.5-flash`)
* **MODEL_PATH**: AttentionRNN 모델 파라미터 파일명 (`attention_rnn.pt`)
* **DATABASE_PATH**: SQLite 데이터베이스 파일명 (`care_system.db`)

### 2.2. 컨테이너 이미지 스펙 (`Dockerfile`)
* **베이스**: `python:3.12-slim` (경량 공식 이미지)
* **보안 및 디렉터리 격리**: 
  - 컨테이너 내부에 `/app/data` 및 `/app/models` 디렉터리를 사전 생성하고 소유권을 **Non-root 사용자 (`careuser`)**에게 위임하여 격리 구동 보안을 달성함.
  - 빌드 시점에 초기 `care_system.db` 및 `attention_rnn.pt`가 이미지 내의 각 안전 경로에 COPY 복사됨.
* **경로 보장**: `ENV PYTHONPATH=/app` 환경 변수를 주입하여 패키지 탐색 문제 해결.

### 2.3. 서비스 오케스트레이션 (`docker-compose.yml`)
* **포트 포워딩**: `8501:8501` 매핑 적용.
* **데이터베이스 영속성 (named volume)**: 
  - Windows 호스트 상에서의 Non-root 사용자 권한 충돌 및 SQLite 트랜잭션 도크 락(`database is locked`) 문제를 방지하기 위해, SQLite DB는 호스트 bind mount 대신 Docker **named volume (`care_data:/app/data`)**을 사용하여 관리함.
  - ⚠️ **중요 (볼륨 유실 경고)**: `docker compose down -v` 또는 `docker compose down --volumes` 명령을 실행하면 마운트된 named volume(`care_data`)이 시스템에서 즉시 삭제되며 데이터베이스의 모든 데이터가 완전히 소멸합니다. 데이터 보존이 필요할 경우 반드시 `-v` 옵션 없이 `docker compose down`만 실행하십시오.
* **모델 파일 연동**:
  - `attention_rnn.pt` 모델은 이미지 내에 복사 탑재되나, 호스트에서 재학습 완료된 가중치를 런타임에 동적으로 주입받아 자동 로딩할 수 있도록 읽기 전용 bind mount(`:ro`)를 함께 구성함.

---

## 3. 2차 개선과제 및 아키텍처적 기술 부채 목록

차기 개발 주기에서 우선 조치해야 할 코어 보안 및 성능 리팩토링 항목입니다.

1. **`[TECH-DEBT-04]` Tensor 변환 O(N) 오버헤드 최적화**: 훈련 루프 내 `torch.tensor` 복사를 주소 공유 포인터인 `torch.from_numpy` 제로 카피 연산으로 변경. (차기 유력 Task 후보)

---

## 4. XAI 생성 모델 연동 및 무정전 안정 운영 가이드 (XAI Handoff Guidelines)

본 시스템은 외부 대형 언어 모델(LLM)을 활용하여 사회복지사에게 설명 가능한 AI(XAI) 리포트를 제공합니다. 외부 API 연동의 불안정성을 통제하기 위해 설계된 아키텍처 명세 및 운영 가이드라인입니다.

### 4.1. API Key Dependency (외부 API 의존성)
* 시스템은 Google GenAI 공식 SDK 및 `gemini-2.5-flash` 모델을 사용하여 자연어 리포트를 동적으로 도출합니다.
* 연동을 위해서는 로컬 `.env` 파일에 `GEMINI_API_KEY` 환경 변수가 바인딩되어 있어야 합니다.
* API 보안을 위해 콘솔 에러 출력부([xai_report_generator.py:L106-107](file:///c:/Users/Gram%20Pro360/.gemini/antigravity-ide/scratch/care_system/src/infrastructure/llm/xai_report_generator.py#L106-107))에 키 노출 방지를 위한 정규식 마스킹 인터셉터가 탑재되어 있습니다.

### 4.2. Fallback Safety Mechanism (장애 감내 안전장치)
* 외부 API 장애(키 미설정, 네트워크 단선, 호출 할당량 초과)가 감지되더라도 전체 이상 탐지 파이프라인과 SQLite 적재, Streamlit UI는 절대 다운되지 않습니다.
* `xai_report_generator.py` 내 `try-except` 예외 격리 및 `mock_api_fail=True` 재귀 복구 설계에 따라, API 호출 실패 시 즉시 **규칙 기반(Rule-based)의 Fallback 한글 리포트**를 로컬에서 자동 조립하여 데이터베이스에 영속화합니다. 이는 외부 요인으로 인한 시스템 전체 마비를 원천 방지하는 핵심 안전장치입니다.

### 4.3. Operational Notes (운영 시 주의사항)
* 배포 및 가동 시 `.env` 파일이 Git 저장소에 커밋되어 노출되지 않도록 강력히 통제해야 합니다.
* 시스템은 비동기 스트리밍이 아닌 일일 자정 배치 처리를 기반으로 동작하므로, API 호출 속도 제한(Rate Limit)에 거의 영향을 받지 않습니다.

### 4.4. Known Limitations & Constraints (알려진 제약 사항)
* **로컬 Docker CLI 부재**: 호스트 개발 에이전트 내에 Docker 및 WSL2 배포판이 미구성된 상태로 남은 한계가 있으나, 실제 타겟 환경인 Windows WSL2 백엔드 Docker Desktop 실 장비에서 최종 실측 런타임 영속성 검증을 마쳤습니다.
* **GEMINI_API_KEY 미설정 경고 로그**: API Key 미설정 시 콘솔에 `[XAI_GENERATOR_ERROR] Google GenAI API Exception` 경고가 출력될 수 있으나, 시스템은 즉시 안전하게 1단계 로컬 Fallback 보고서 모드로 자동 전환되므로 안심하고 운영 가능합니다.
* **단일 마스터 패스워드 인증 한계**: 대시보드 보안 장벽은 단일 비밀번호 해싱(`MASTER_PASSWORD_HASH`)에 의존하므로, 다중 복지사 계정별 ID/PW 개별 권한 격리 및 OAuth2 방식의 고도화 토큰 인증은 지원하지 않는 구조적 보안 제약이 있습니다.

### 4.5. Verification Checklist (운영 확인 체크리스트)
- [x] `.env` 파일에 API Key가 공백 상태일 때도 XAI 보고서가 로컬 Fallback 모드로 오류 없이 출력되는가?
- [x] 가상환경 `.venv`가 활성화되고 `python -m pytest` 실행 시 26개 테스트 시나리오가 모두 성공하는가?
- [x] 데이터베이스 리포트 품질 검증 스크립트(`check_db.py`) 실행 시 PII 누출 및 금지어 탐지가 0건으로 안정적인가?
- [x] Docker Desktop Windows WSL2 backend 환경 하에 named volume `care_data` 내에서 SQLite `-wal/-shm` 파일 권한 충돌 및 DB 락 없이 정상 실행되고, 컨테이너 리빌드/다운 시 데이터가 완전 영속 보존되는가?
- [x] 다중 주민 배치 분석 구동 시 가중치 파일 `attention_rnn.pt` 로딩이 인메모리 싱글톤 캐시(`AttentionRNNModelCache`)에 의해 최초 1회만 디스크로부터 실행되는가?
- [x] 유스케이스 계층의 구체 DatabaseConnector 직접 import가 제거되고 CareRepositoryPort 추상 인터페이스를 주입하도록 DIP 위반 보완이 처리되었는가?

### 4.6. Next Maintainer Notes (차기 유지보수자 인수인계 가이드)
* **API 비의존형 XAI 수정**: API Key가 없는 무과금 상태에서 XAI 보고서를 수정하거나 룰 기반 내용을 확장하려면 [xai_report_generator.py:L53-69](file:///c:/Users/Gram%20Pro360/.gemini/antigravity-ide/scratch/care_system/src/infrastructure/llm/xai_report_generator.py#L53-69) 내의 1단계 Fallback 가이드 텍스트 빌더 부분을 보수적으로 수정하십시오.
* **캐시 라이프사이클**: 로컬 환경에서 모델 학습(`ModelTrainer.train_on_data`)을 연속해서 돌리는 테스트를 할 때는, 훈련 후 캐시된 모델 가중치를 무효화하기 위해 반드시 `AttentionRNNModelCache.clear_cache()`를 실행하여 메모리를 동기화해 주어야 합니다.

### 4.7. 윤리적 및 임상적 제약 조건의 준수 (Ethical Disclaimer)
* **임상 진단 단정 금지**: 보고서 텍스트에 "피돌봄 노인은 우울증 환자로 판단됩니다" 또는 "치매가 의심됩니다"와 같은 임상적 최종 진단성 문장을 포함시키는 것을 절대 금지합니다.
* **의료진 최종 판단 대체 불가 고정 표출**: 모든 보고서의 문두에는 다음 배너가 고정 하드코딩 결합되어 표출되어야 합니다:
  `[의사결정 보조지표] 본 문서는 의료진의 최종 임상적 진단을 대체할 수 없으며, 예방 및 모니터링 보조 목적으로만 활용해야 합니다.`
* **개인식별정보(PII) 격리**: 데이터베이스 및 LLM 통신 패킷에는 노인의 성명, 주소 대신 난수화된 비식별화 코드(`RES-MASK-2026A` 등)만 전달되어야 합니다.
