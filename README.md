# 스마트시티 독거노인 안심 예방 돌봄 AI 에이전트 시스템 (Care Agent System)

본 시스템은 독거노인의 스마트홈 일상생활(ADL) 센서 점유비 데이터를 분석하여, **AttentionRNN 딥러닝 예측 모형**과 **Double-step 이상 탐지 기법**을 활용하여 이상 패턴을 조기에 발견하고, **OpenAI LLM 설명 가능성(XAI) 자연어 보고서**를 통해 사회복지사의 빠른 선제 조치를 보조하는 예방적 돌봄 AI 에이전트 소프트웨어입니다.

---

## 🚀 주요 기능 (Core Features)

1. **CASAS 41개 ADL 일간 점유율 합성 제너레이터**
   * 불면증(Sleep), 식사유실(Eat) 등의 행동 장애 변이 시나리오 주입 기능.
   * 일일 41개 일상생활 시간 점유율 합산 **정확히 $100.00\%$ 정규화 무결성** 보장.
2. **AttentionRNN 15일 윈도우 예측 엔진**
   * 과거 15일간의 행동 윈도우 `(Batch, 15, 41)`를 입력받아 다음 날의 패턴 `(Batch, 41)` 예측.
   * 각 날짜별 기여도 중요도를 해석하는 **Self-Attention 가중치** 추출.
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
d:\연구실\연구\스마트시티개론\
├── docs/                             # 연구 기획, 요구사항, 아키텍처, 검증 문서군
│   ├── 00_context_management/        # 상태 패킷 (context_packet, DECISIONS, OPEN_QUESTIONS)
│   ├── 03_design/                    # 도메인 모델, 데이터베이스 스키마 및 아키텍처 설계
│   └── 05_verification/              # 테스트 전략 및 데브옵스 인수인계 보고서
├── src/                              # 시스템 실행 소스코드 루트
│   ├── domain/                       # DDD 도메인 레이어 (Resident, Anomaly, Alert 엔터티)
│   ├── usecases/                     # 유스케이스 레이어 (전처리 보강, 이상 탐지 오케스트레이션)
│   ├── infrastructure/               # 인프라 계층 (PyTorch RNN, Scorer, LLM 어댑터, DB SQLite)
│   └── presentation/                 # 표현 계층 (Streamlit 안심 대시보드 웹앱)
├── tests/                            # BDD 시나리오 기반의 테스트 하네스 검증 코드
│   ├── test_models.py                # AttentionRNN 텐서 및 가중치 형상 검증
│   ├── test_usecases.py              # 결측치 보강 및 LLM Fallback 연동 통합 검증
│   └── test_harness.py               # 하네스 엔지니어링 5대 검증 항목 집중 자동화 검증
├── Dockerfile                        # 경량 배포 및 Non-root 보안 통제 컨테이너 빌드 파일
├── docker-compose.yml                # 포트 매핑 및 SQLite 볼륨 영속 보존 오케스트레이션
└── requirements.txt                  # Python 핵심 의존성 목록
```

---

## 🛠️ 빠른 시작 가이드 (Quick Start Guide)

### 1. 로컬 개발 환경 셋업 (Windows PowerShell 기준 검증 완료)
```bash
# 가상환경 구성 및 활성화
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell

# 필수 라이브러리 설치
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 가상 데이터 시드 데이터 적재 (Database Seeding - 검증 완료)
시스템 구동을 위해 30일치 합성 ADL 요약 데이터 및 이상 보고서 모의 시드를 SQLite DB 파일에 적재합니다.
```bash
.venv\Scripts\python.exe -c "import sys; sys.path.append('src'); from infrastructure.persistence.seed_data import seed_database; seed_database('care_system.db')"
```
* **주의**: 현재 `numpy.float32` 타입 데이터가 SQLite 입력 시 JSON 직렬화 오류(TypeError)를 발생시키는 경고 로그가 확인되었으나, 데이터 적재 자체는 성공적으로 수행됩니다 (차기 개선 대상).

### 3. 하네스 BDD 테스트 구동 (8개 테스트 100% 통과 완료)
5대 검증 항목 및 전체 단위/결합 테스트를 실행합니다.
```bash
# PYTHONPATH 설정과 함께 pytest 실행
$env:PYTHONPATH="."
.venv\Scripts\python.exe -m pytest
```

### 4. Streamlit 안심 모니터링 웹 대시보드 로컬 실행 (기동 검증 완료)
```bash
.venv\Scripts\python.exe -m streamlit run src/presentation/app.py
```
* 브라우저에서 `http://localhost:8501` 주소로 자동으로 세련된 다크모드 화면이 열립니다.

---

## 🐳 Docker 컨테이너 프로덕션 배포 가이드

운영 환경에서 Docker를 통해 격리 배포하고 영속성을 유지하는 방법입니다.

### 1. 환경 변수 파일 생성
`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 OpenAI API Key를 기입하십시오.
```bash
copy .env.example .env
```

### 2. Docker Compose 빌드 및 가동
```bash
# 백그라운드로 대시보드 구동
docker-compose up --build -d
```
* `docker-compose.yml` 볼륨 정의에 따라, 컨테이너를 재시작해도 복지사가 저장한 피드백 메모 및 정오탐 SQL 상태가 로컬의 `care_system.db`에 영구 안전하게 동기화 보존됩니다.

---

## 🛡️ API 결함 감내 및 Fallback 메커니즘 (Fault-Tolerance & Fallback)

Google GenAI 또는 OpenAI API키가 설정되지 않았거나 유효하지 않은 경우에도, 시스템 전체의 파이프라인은 중단되지 않습니다. 대신, 룰 기반(Rule-based)의 Fallback XAI 보고서를 자동 생성하여 이상 탐지 결과가 사회복지사의 확인 단계까지 안전하게 도달하도록 보증합니다. 이 기능은 외부 API 장애 시에도 시스템의 연속성을 유지하기 위한 안전장치입니다.

### 1. Fallback 작동 흐름
* **자동 진입**: 로컬 환경 변수에 `GEMINI_API_KEY`가 없거나 기본 더미 값(`your_gemini_api_key_here`)인 경우, API 요청을 보내지 않고 **즉시 1단계 Fallback 규칙**에 따라 로컬 한국어 대체 리포트(Format: 수치 정보 및 조치 지침 결합형)가 즉시 자동 생성됩니다.
* **예외 격리**: 유효하지 않은 키를 입력하여 API 통신 도중 `Exception`이 발생한 경우, 이를 내부 `try-except` 블록에서 안전하게 격리하고 에러 로그를 출력한 뒤 **2단계 Fallback 재귀 호출**을 통해 무정전 상태로 시스템을 정상 복구합니다.
* **시딩(Database Seeding) 시의 동작**: `seed_data.py`를 통해 가상 데이터를 주입할 때에도 동일하게 Fallback 분석 파이프라인이 자동 작동하여 데이터베이스 적재 실패 없이 성공적으로 적재 완료됩니다.

---

## 🔑 로컬 환경 변수 (.env) 설정 및 보안 가이드 (Environment & Security)

Gemini API(Google AI Studio) 등 외부 생성형 AI 모델과의 실측 연동을 진행하려면 프로젝트 루트 디렉토리에 `.env` 파일을 수동으로 구성해 주어야 합니다.

### 1. 환경 변수 파일 구성 방법 및 작성 예시
`.env.example` 파일을 참고하여 아래 형식과 같이 `.env` 파일을 생성하십시오.
```env
# Google Gemini API Key (Google AI Studio 발급 권장)
GEMINI_API_KEY=AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q

# 사용할 LLM 모델 식별자
GEMINI_MODEL=gemini-2.5-flash

# PyTorch 가중치 및 DB 파일 기본 저장명
MODEL_PATH=attention_rnn.pt
DATABASE_PATH=care_system.db
```
* **⚠️ 경고 (보안 제약)**: `GEMINI_API_KEY` 및 서비스 비밀키는 **절대로 Git 저장소(Github 등)에 커밋하여 업로드하지 마십시오.** 이 프로젝트는 `.gitignore` 또는 `.antigravityignore` 설정을 통해 `.env` 파일의 유출을 차단하도록 격리되어 있습니다.

### 2. 실제 API 연동 후 검증 방법
유효한 `GEMINI_API_KEY`를 `.env`에 설정한 상태에서, 아래 명령어를 실행하여 API 호출에 에러가 없고 동적 자연어 보고서가 올바르게 작동하는지 검증합니다.
```bash
# 가상환경 활성화 후 모의 데이터 리시딩 실행
.venv\Scripts\python.exe -c "import sys; sys.path.append('src'); from infrastructure.persistence.seed_data import seed_database; seed_database('care_system.db')"
```
* **성공 판정**: CLI 로그 상에 `Google GenAI API Exception` 경고가 발생하지 않고, Streamlit 대시보드 내 리포트 영역에 모델이 작성한 친절한 한국어 돌봄 보고서(Fallback 문구가 미포함된 동적 해설)가 표출되어야 합니다. (실제 키 연동 상태에서의 동작 검증은 개별 발급 상태에 따라 **[미확인]** 영역으로 관리됨).

### ⚖️ 윤리적 및 임상적 제약 조건 (Ethical Disclaimer)
* 생성된 XAI 자연어 보고서의 문두에는 항상 `[의사결정 보조지표] 본 문서는 의료진의 최종 임상적 진단을 대체할 수 없으며...` 라는 헤더 문구가 강제로 결합되어 출력됩니다.
* 본 시스템은 의료/임상 진단을 대체할 수 없으며, 사회복지사의 수동 의사결정을 보조하기 위한 목적으로만 사용되어야 합니다.

---

## 🛠️ 트러블슈팅 (Troubleshooting)

* **현상**: `seed_data.py` 실행 시 콘솔에 `[XAI_GENERATOR_ERROR] Google GenAI API Exception` 에러가 다량 출력됩니다.
  - **원인**: `.env` 파일 내에 `GEMINI_API_KEY`가 없거나 무효한 API 키가 지정된 상태입니다.
  - **대처**: 이는 시스템의 설계된 안전장치(Fallback)가 가동 중인 것으로, **정상 작동**입니다. 대시보드를 켜면 룰 기반 대체 텍스트가 정상적으로 데이터베이스로부터 조회되어 표출됩니다. 만약 실제 AI 분석 리포트를 원하시면, 위에 안내된 로컬 환경 변수 가이드에 따라 발급받으신 유효한 API 키를 `.env`에 올바르게 삽입해 주십시오.
* **현상**: Windows PowerShell에서 `Activate.ps1` 실행 시 권한 에러가 발생합니다.
  - **대처**: PowerShell을 관리자 권한으로 열어 `Set-ExecutionPolicy RemoteSigned` 명령어를 실행하여 스크립트 실행 권한을 획득하십시오.
