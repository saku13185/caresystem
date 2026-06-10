# 스마트시티 독거노인 안심 예방 돌봄 AI 에이전트 시스템 (Care Agent System)

본 시스템은 독거노인의 스마트홈 일상생활(ADL) 센서 점유비 데이터를 분석하여, **AttentionRNN 딥러닝 예측 모형**과 **Double-step 이상 탐지 기법**을 활용하여 이상 패턴을 조기에 발견하고, **OpenAI/GenAI LLM 설명 가능성(XAI) 자연어 보고서**를 통해 사회복지사의 빠른 선제 조치를 보조하는 예방적 돌봄 AI 에이전트 소프트웨어입니다.

---

## 🚀 주요 기능 (Core Features)

1. **CASAS 41개 ADL 일간 점유율 합성 제너레이터**
   * 불면증(Sleep), 식사유실(Eat) 등의 행동 장애 변이 시나리오 주입 기능.
   * 일일 41개 일상생활 시간 점유율 합산 **정확히 $100.00\%$ 정규화 무결성** 보장.
2. **AttentionRNN 15일 윈도우 예측 엔진 및 싱글톤 캐시**
   * 과거 15일간의 행동 윈도우 `(Batch, 15, 41)`를 입력받아 다음 날의 패턴 `(Batch, 41)` 예측.
   * 각 날짜별 기여도 중요도를 해석하는 **Self-Attention 가중치** 추출.
   * **[인메모리 캐싱]** 다중 주민 일괄 분석 시 가중치 파일(`attention_rnn.pt`)의 최초 1회 로딩 이후 핫 메모리를 재사용하는 `AttentionRNNModelCache` 싱글톤 캐시 모듈 탑재.
3. **Double-step 이중 이상 탐지 스코어러**
   * 1단계: 예측치-실측치 MAE 오차의 통계적 **Z-score 검증** (Z > 2.5 시 고위험).
   * 2단계: 개별 활동의 역사적 **Boxplot IQR 범위 이탈 검사** (국소 아웃라이어 파악).
4. **맥락 주입형(Context-Injected) LLM XAI 리포트**
   * 의료적 오인 방지 경고문 최상단 **하드코딩 인쇄** 및 개인정보(PII)의 철저한 UUID 격리.
   * OpenAI API 장애 시 정형화된 규격 기반 **Fallback 구문 즉시 자동 발급**.
5. **Streamlit 다크모드 글라스모피즘 복지사 대시보드**
   * 위험군 대상자 카드식 필터링 보드, Plotly 어텐션/임계치 이탈 반응형 차트.
   * 복지사 피드백 메모 및 정오탐 수집 즉시 **SQLite DB 실시간 영속 업데이트**.

---

## 📂 코드베이스 폴더 아키텍처

```
care_system/
├── docs/                             # 연구 기획, 요구사항, 아키텍처, 검증 문서군
│   ├── 00_context_management/        # 상태 패킷 (context_packet, DECISIONS, OPEN_QUESTIONS)
│   ├── 03_design/                    # 도메인 모델, 데이터베이스 스키마 및 아키텍처 설계
│   └── 05_verification/              # 테스트 전략 및 데브옵스 인수인계 보고서 (10_handoff)
├── src/                              # 시스템 실행 소스코드 루트
│   ├── domain/                       # DDD 도메인 레이어 (Resident, Anomaly, Alert 엔터티)
│   ├── usecases/                     # 유스케이스 레이어 (전처리 보강, 이상 탐지 오케스트레이션)
│   ├── infrastructure/               # 인프라 계층
│   │   ├── models/                   # PyTorch RNN 구조 및 학습/추론 파이프라인, model_cache
│   │   ├── scorers/                  # Z-score 및 Boxplot IQR 이상 분류 모듈
│   │   ├── llm/                      # XAI 자연어 리포트 제너레이터 어댑터
│   │   └── persistence/              # SQLite DB 연동 커넥터 및 데이터 시더 (seed_data)
│   └── presentation/                 # 표현 계층 (Streamlit 안심 대시보드 웹앱)
├── tests/                            # BDD 시나리오 기반의 테스트 하네스 검증 코드
│   ├── test_env_paths.py             # DATABASE_PATH / MODEL_PATH 환경변수 연동 테스트
│   ├── test_model_cache.py           # AttentionRNNModelCache 싱글톤 동작 및 로드 횟수 테스트
│   ├── test_models.py                # AttentionRNN 텐서 및 가중치 형상 검증
│   ├── test_pii_detection.py         # check_db 이름 오탐 차단 정밀도 검증 테스트
│   └── test_usecases.py              # 결측치 보강 및 LLM Fallback 연동 통합 검증
├── Dockerfile                        # 경량 배포 및 Non-root 보안 통제 컨테이너 빌드 파일
├── docker-compose.yml                # 포트 매핑 및 SQLite named volume 영속 보존 오케스트레이션
└── requirements.txt                  # Python 핵심 의존성 목록
```

---

## 🛠️ 빠른 시작 가이드 (Quick Start Guide)

### 1. 로컬 개발 환경 셋업 (Windows PowerShell 기준)
```bash
# 가상환경 구성 및 활성화
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell

# 필수 라이브러리 설치
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 가상 데이터 시드 데이터 적재 (Database Seeding)
SQLite DB 파일에 30일치 합성 ADL 요약 데이터 및 이상 보고서 모의 시드를 적재합니다.
```bash
.venv\Scripts\python.exe -m src.infrastructure.persistence.seed_data
```
* **성능 최적화 확인**: 5명의 노인 레코드를 순차 시딩할 때, `[AttentionRNNModelCache] Loading model from disk`가 1회 실행된 이후, 2~5번째 노인부터는 `Reusing cached AttentionRNN model` 로그가 출력되며 인메모리 싱글톤 캐시가 작동합니다.
* **직렬화 경고 해결**: numpy `float32/64` 데이터 타입의 SQLite 입력 JSON 직렬화 불가 오류(TypeError)가 해결되어 무경고 적재가 완수됩니다.

### 3. BDD 테스트 구동 (19개 테스트 100% 통과)
5대 검증 항목, 환경변수 오버라이드, PII 탐지 정교화, 모델 캐시 및 전체 결합 테스트를 구동합니다.
```bash
$env:PYTHONPATH="."
.venv\Scripts\python.exe -m pytest
```

### 4. Streamlit 안심 모니터링 웹 대시보드 로컬 실행
```bash
.venv\Scripts\python.exe -m streamlit run src/presentation/app.py
```
* 브라우저에서 `http://localhost:8501` 주소로 자동으로 세련된 다크모드 화면이 렌더링됩니다. 복지사 피드백 메모 저장 시 즉각 SQLite DB에 영속 동기화됩니다.

---

## 🐳 Docker 컨테이너 프로덕션 배포 가이드

### 1. 환경 변수 파일 생성
`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 OpenAI/Gemini API Key를 기입합니다.
```bash
copy .env.example .env
```

### 2. Docker Compose 빌드 및 가동
```bash
# 백그라운드로 대시보드 구동
docker compose up --build -d
```
* **데이터베이스 영속성 (named volume)**: 
  본 시스템의 SQLite 데이터베이스는 호스트의 bind mount 대신 Docker **named volume (`care_data`)**을 사용하여 관리됩니다.
* ⚠️ **주의 (볼륨 데이터 보존)**: 컨테이너를 정지/삭제할 때 `docker compose down -v` 또는 `docker compose down --volumes` 명령을 실행하면 마운트된 named volume(`care_data`)이 삭제되어 내부의 모든 데이터베이스 레코드가 영구 소멸합니다. 단순히 컨테이너만 정지하고 데이터를 보존하려면 `-v` 옵션을 제외하고 `docker compose down`만 실행하십시오.
* **Windows WSL2 환경 named volume 권장 이유**: Windows Docker Desktop(WSL2 백엔드)에서 NTFS 호스트 경로의 파일을 직접 컨테이너에 bind mount하는 경우, Non-root 사용자 권한 불일치로 인한 쓰기 권한 오류(Permission Denied) 및 SQLite 트랜잭션 도중 파일 잠금(Locking) 버그로 인한 `database is locked` 에러가 빈번하게 발생할 수 있습니다. 반면, named volume은 Linux 네이티브 파일 시스템(EXT4) 상에서 영속되기 때문에 POSIX 파일 잠금과 소유권 격리가 완벽히 보장되어 안정적으로 동작합니다.
* **모델 파일 연동**:
  빌드 시 `attention_rnn.pt` 실측 가중치가 이미지 내부에 COPY되며, `docker-compose.yml`에서 읽기 전용 bind mount(`:ro`)로 호스트와 연결되어 호스트 상의 모델 파일이 갱신되는 경우 즉시 적용됩니다.

---

## 🛡️ API 결함 감내 및 Fallback 메커니즘 (Fault-Tolerance & Fallback)

Google GenAI 또는 OpenAI API키가 설정되지 않았거나 유효하지 않은 경우에도, 시스템 전체의 파이프라인은 중단되지 않습니다. 대신, 룰 기반(Rule-based)의 Fallback XAI 보고서를 자동 생성하여 이상 탐지 결과가 사회복지사의 확인 단계까지 안전하게 도달하도록 보증합니다. 이 기능은 외부 API 장애 시에도 시스템의 연속성을 유지하기 위한 안전장치입니다.

### 1. Fallback 작동 흐름
* **자동 진입**: 로컬 환경 변수에 `GEMINI_API_KEY`가 없거나 기본 더미 값(`your_gemini_api_key_here`)인 경우, API 요청을 보내지 않고 **즉시 1단계 Fallback 규칙**에 따라 로컬 한국어 대체 리포트(Format: 수치 정보 및 조치 지침 결합형)가 즉시 자동 생성됩니다.
* **예외 격리**: 유효하지 않은 키를 입력하여 API 통신 도중 `Exception`이 발생한 경우, 이를 내부 `try-except` 블록에서 안전하게 격리하고 에러 로그를 출력한 뒤 **2단계 Fallback 재귀 호출**을 통해 무정전 상태로 시스템을 정상 복구합니다.

---

## 🏆 주요 검증 완료 항목 (Verification Done)
1. **손상 Python 파일 복원 완료**: 11개 핵심 코드 원본 복구 및 정상화 완수.
2. **.venv 가상환경 구축**: PyTorch, Streamlit, SciPy 등의 의존성 requirements 구축 및 이관 성공.
3. **pytest 전체 통과**: 신규 환경변수/캐시/PII 테스트를 포함하여 전체 19개 BDD 시나리오 100% 통과.
4. **seed_data.py 실행 무결성**: 30일 시계열 데이터 합성 생성기 및 시드 무경고 적재 성공.
5. **Streamlit 안심 대시보드 구동**: 8501 포트 반응형 글라스모피즘 다크모드 대시보드 렌더링 확인.
6. **numpy.float32/float64 JSON 직렬화 해결**: SQLite 입하 형변환 가드로 TypeError 제거.
7. **무과금 Fallback XAI 검증**: API Key 미설정 및 장애 상황 하에서 100% 한글 대체 보고서 작성/보존 실증.
8. **check_db.py PII 이름 오탐 개선**: 성씨 결합 단독 이름 조사 매칭(이탈, 이상) 오탐 0건 개선 및 단위테스트화.
9. **DATABASE_PATH / MODEL_PATH 환경변수 연동**: Docker 및 로컬 분리 타겟팅 가능하도록 런타임 환경변수 수용.
10. **WSL2 컨테이너 named volume 실측**: non-root `careuser`의 SQLite wal/shm 권한 에러 방지 및 데이터 영속 실증 완료.
11. **AttentionRNN 실모델 학습 및 추론**: `attention_rnn.pt` 실가중치 로딩 및 Mock 예측 강제 강등 해제.
12. **Model Cache 최적화**: 중복 가중치 로드를 최초 1회로 제어하는 `AttentionRNNModelCache` 연동 완료.

---

## 🛠️ 트러블슈팅 (Troubleshooting)

* **현상**: `seed_data.py` 실행 시 콘솔에 `[XAI_GENERATOR_ERROR] Google GenAI API Exception` 에러가 다량 출력됩니다.
  - **원인**: `.env` 파일 내에 `GEMINI_API_KEY`가 없거나 무효한 API 키가 지정된 상태입니다.
  - **대처**: 이는 시스템의 설계된 안전장치(Fallback)가 가동 중인 것으로, **정상 작동**입니다. 대시보드를 켜면 룰 기반 대체 텍스트가 정상적으로 데이터베이스로부터 조회되어 표출됩니다. 만약 실제 AI 분석 리포트를 원하시면, 위에 안내된 로컬 환경 변수 가이드에 따라 발급받으신 유효한 API 키를 `.env`에 올바르게 삽입해 주십시오.
* **현상**: `seed_data.py` 기동 시 `DATABASE_PATH` 탐색 중 `NameError: name 'os' is not defined` 에러로 중단됩니다.
  - **대처**: `seed_data.py` 상단에 `import os`가 추가된 최신 버전 코드를 사용하고 있는지 확인하십시오.
* **현상**: Windows PowerShell에서 `Activate.ps1` 실행 시 권한 에러가 발생합니다.
  - **대처**: PowerShell을 관리자 권한으로 열어 `Set-ExecutionPolicy RemoteSigned` 명령어를 실행하여 스크립트 실행 권한을 획득하십시오.
