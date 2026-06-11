# 스마트시티 독거노인 안심 예방 돌봄 AI 에이전트 시스템 (Care Agent System)

본 시스템은 독거노인의 스마트홈 일상생활(ADL) 센서 점유비 데이터를 분석하여, **AttentionRNN 딥러닝 예측 모형**과 **Double-step 이상 탐지 기법**을 활용한 자동화된 위험군 조기 예측 및 XAI 기반의 해석 가능한 보고서를 제공하는 복지사 의사결정 지원 시스템입니다.

---

## 🚀 주요 기능 (Core Features)

1. **CASAS 41개 ADL 일간 점유율 합성 제너레이터**
   * 불면증(Sleep), 식사유실(Eat) 등의 행동 장애 변이 시나리오 주입 기능.
   * 일일 41개 일상생활 시간 점유율 합산 **정확히 $100.00\%$ 정규화 무결성** 보장.
2. **AttentionRNN 15일 윈도우 예측 엔진 및 싱글톤 캐시**
   * 과거 15일간의 행동 윈도우 `(Batch, 15, 41)`를 입력받아 다음 날의 패턴 `(Batch, 41)` 예측.
   * 각 날짜별 기여도 중요도를 해석하는 **Self-Attention 가중치** 추출.
   * **[인메모리 캐싱]** 다중 주민 일괄 분석 시 가중치 파일(`attention_rnn.pt`)의 최초 1회 로딩 이후 핫 메모리를 재사용하는 `AttentionRNNModelCache` 싱글톤 캐시.
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

## 🧠 AttentionRNN 모델 상세 설명

### 1. 모델 아키텍처 개요
**AttentionRNN**은 시간 시계열 ADL 패턴의 미래 행동을 예측하고, 각 과거 시점의 기여도(Attention Weight)를 해석 가능하게 추출하는 **Self-Attention 메커니즘이 탑재된 RNN 모델**입니다.

### 2. 입출력 스펙
- **입력 (Input)**:
  - 형태: `(Batch, Seq_Length=15, Features=41)` 
  - 의미: 배치 단위 대상자들의 과거 15일간 ADL 점유율 시계열 데이터
  - 범위: 각 Feature(ADL 활동)는 0~1 범위의 정규화된 점유율
  
- **출력 (Output)**:
  - 예측값: `(Batch, 41)` — 다음 날(D+1)의 41개 ADL 점유율 예측
  - Attention 가중치: `(Batch, 15)` — 각 과거 일자(D-14 ~ D)가 미래 예측에 미치는 기여도 스코어

### 3. 내부 구조
```
Input (Batch, 15, 41)
    ↓
LSTM Layer (hidden_dim=64)
    ↓
Self-Attention (key, query, value 프로젝션)
    ↓
Attention Output (Batch, 64) + Attention Weights (Batch, 15)
    ↓
FC Layer (64 → 41)
    ↓
Output (Batch, 41) + Weights (Batch, 15)
```

- **LSTM 계층**: 시간적 의존성 학습으로 장기 패턴 포착
- **Self-Attention 계층**: 각 시점의 중요도를 동적으로 가중치화
- **완전연결 계층**: 최종 41차원 ADL 예측 생성

### 4. 학습 파이프라인
- **손실함수**: MAE (Mean Absolute Error) - 강건한 이상치 처리
- **최적화기**: Adam (learning_rate=0.001)
- **배치 크기**: 32
- **에포크**: 100 이상 (조기 종료: validation loss 기준)
- **정규화**: Batch Normalization + Dropout(0.3)

### 5. 추론 및 캐싱 전략
```python
# 싱글톤 캐시 구조
class AttentionRNNModelCache:
    _instance = None
    _model = None  # 최초 1회만 로드, 이후 재사용
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = torch.load('attention_rnn.pt')
        return cls._model
```

- **첫 번째 추론**: `attention_rnn.pt` 파일을 디스크에서 메모리로 로딩 (약 100ms)
- **이후 추론**: 메모리상의 캐시된 모델 재사용 (약 5ms) → **20배 성능 향상**

### 6. 해석성 (Interpretability)
- **Attention 시각화**: Plotly 히트맵으로 각 대상자의 일자별 기여도 표시
- **Top-K 중요 날짜 추출**: 상위 3개 가장 중요한 과거 날짜 강조 표시
- **의료 전문가 검증**: Attention 가중치의 의료적 타당성 (예: 최근 3일이 더 높은 가중치)

### 7. 모델 경로 및 환경변수
```bash
# 로컬 개발 환경
MODEL_PATH=./src/infrastructure/models/weights/attention_rnn.pt

# Docker 환경
MODEL_PATH=/app/models/attention_rnn.pt
```

---

## 📋 개발 과정 설명 문서

### 1. 프로젝트 진화 타임라인

#### Phase 1: 요구사항 수집 & 아키텍처 설계 (Week 1-2)
- **스테이크홀더**: 복지사, 의료 전문가, 데이터 과학자
- **핵심 요구사항**:
  - 독거노인 고위험 상황 조기 예측
  - 해석 가능한 AI (XAI) 리포트 제공
  - 의료 오진 방지 안전장치
  - 오프라인 Fallback 지원
- **산출물**: `docs/00_context_management/REQUIREMENTS.md`

#### Phase 2: 도메인 모델 & DB 설계 (Week 3)
- **도메인 엔터티**: Resident, ADLRecord, Anomaly, Alert
- **DDD 적용**: 도메인 언어(Ubiquitous Language) 정의
- **DB 스키마**: SQLite 테이블 설계 (Resident, Records, Alerts, Feedback)
- **산출물**: `docs/03_design/DOMAIN_MODEL.md`, `SCHEMA.sql`

#### Phase 3: 머신러닝 모델 개발 (Week 4-5)
- **데이터 준비**: CASAS 공개 데이터셋 전처리
- **기저선 모델**: Linear Regression, Random Forest 벤치마킹
- **AttentionRNN 개발**: PyTorch 구현 및 하이퍼파라미터 튜닝
- **성능 평가**: MAE, RMSE, 이상탐지 정확도(Precision/Recall)
- **산출물**: `src/infrastructure/models/attention_rnn.py`, `train_model.py`

#### Phase 4: 이상탐지 엔진 (Week 6)
- **Double-step 설계**:
  - 1단계: 통계적 이상 (Z-score)
  - 2단계: 개별 활동 기반 이상 (IQR Boxplot)
- **임계값 튜닝**: ROC 곡선 기반 최적 임계값 선정
- **산출물**: `src/infrastructure/scorers/double_step_scorer.py`

#### Phase 5: XAI 리포트 생성 (Week 7)
- **LLM 통합**: OpenAI GPT-4 / Google Gemini API
- **프롬프트 엔지니어링**: 맥락 주입형(Context-Injected) 프롬프트 설계
- **PII 격리**: 대상자 이름 → UUID 치환
- **Fallback 규칙**: API 장애 시 규칙 기반 리포트 자동 생성
- **산출물**: `src/infrastructure/llm/xai_generator.py`

#### Phase 6: Streamlit 대시보드 개발 (Week 8)
- **UI/UX**: 복지사 페르소나 기반 설계
- **반응형 차트**: Plotly 라이브러리 활용
- **실시간 피드백 수집**: SQLite 동기 쓰기
- **다크모드 & 글라스모피즘**: 최신 디자인 트렌드 적용
- **산출물**: `src/presentation/app.py`

#### Phase 7: Docker 배포 & 운영 (Week 9)
- **컨테이너화**: Dockerfile 경량화 (Alpine 기반)
- **Non-root 사용자**: 보안 강화 (`careuser`)
- **Named Volume**: SQLite 데이터 영속성 보장
- **docker-compose.yml**: 로컬/프로덕션 환경 분리
- **산출물**: `Dockerfile`, `docker-compose.yml`

#### Phase 8: 통합 테스트 & 검증 (Week 10)
- **BDD 테스트**: 19개 시나리오 100% 통과
- **성능 벤치마크**: 5명 대상자 배치 처리 시간 측정
- **보안 감시**: PII 탐지 정밀도, API 에러 처리
- **산출물**: `tests/test_*.py`, `docs/05_verification/TEST_REPORT.md`

### 2. 주요 의사결정 (Decisions)
| 의사결정 항목 | 선택지 A | 선택지 B | **채택** | 근거 |
|---|---|---|---|---|
| RNN 구조 | LSTM | GRU | **LSTM** | 메모리 셀로 장기 패턴 학습 우수 |
| Attention | Multi-head | Single | **Single** | 모델 복잡도 감소, 해석성 향상 |
| DB | PostgreSQL | SQLite | **SQLite** | 경량 배포, 컨테이너 친화적 |
| XAI 소스 | In-house LLM | API | **API** | 의료 수준의 정확한 설명 필요 |
| 캐싱 전략 | 매 요청마다 로드 | 싱글톤 캐시 | **싱글톤** | 20배 성능 향상 |
| Fallback | 에러 반환 | 자동 규칙 생성 | **규칙 생성** | 서비스 연속성 보장 |

### 3. 열린 질문 & 개선 사항 (Open Questions)
1. **모델 재학습 주기**: 현재 정적 모델 사용 → 6개월 주기 자동 재학습 고려
2. **멀티모달 센서 통합**: 현재 점유 센서만 사용 → 온도, 습도 등 추가 센서 통합
3. **다국어 XAI**: 현재 한국어 전용 → 영어, 중국어 다언어 지원
4. **개인화 임계값**: 현재 글로벌 Z-score 임계값 → 개인별 적응형 임계값 학습
5. **실시간 모니터링**: 현재 일일 배치 → AWS Lambda + SQS 기반 실시간 처리

---

## 📖 설치 및 운영 설명서

### 1. 사전 요구사항
```
Operating Systems: Windows 10/11, macOS, Linux
Python: 3.9 이상 (3.11 권장)
Docker: 20.10 이상 (배포 환경)
RAM: 최소 4GB (로컬), 8GB (프로덕션)
Storage: 1GB (코드 + 모델 + DB)
```

### 2. 로컬 개발 환경 상세 셋업

#### Windows PowerShell
```powershell
# 1단계: 저장소 클론
git clone https://github.com/saku13185/caresystem.git
cd caresystem

# 2단계: Python 버전 확인 (3.9+ 필수)
python --version

# 3단계: 가상환경 생성 & 활성화
python -m venv .venv
.venv\Scripts\Activate.ps1

# 권한 에러 발생 시
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4단계: 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 5단계: 환경변수 설정
copy .env.example .env
# .env 파일에 API Key 기입 (또는 빈 상태로 Fallback 모드 진입)
```

#### macOS/Linux (Bash)
```bash
# 1단계~2단계: 동일
git clone https://github.com/saku13185/caresystem.git
cd caresystem
python3 --version

# 3단계: 가상환경 생성 & 활성화
python3 -m venv .venv
source .venv/bin/activate

# 4단계~5단계: 동일
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

### 3. 데이터베이스 초기화

#### 자동 시딩 (권장)
```bash
# 30일 시계열 합성 데이터 + 이상 보고서 자동 생성
python -m src.infrastructure.persistence.seed_data

# 예상 실행 시간: 약 10~15초
# 로그 예시:
# [seed_data] Starting database seeding...
# [AttentionRNNModelCache] Loading model from disk...
# [seed_data] Inserted 5 residents with 150 records
# [seed_data] Seeding completed successfully
```

#### 수동 DB 관리
```bash
# SQLite 셸 진입
sqlite3 care_system.db

# 테이블 목록 확인
.tables

# 데이터 조회 (예: 대상자 목록)
SELECT resident_id, name, age FROM residents LIMIT 10;

# DB 종료
.exit
```

### 4. 테스트 실행 및 검증

#### 전체 테스트 (19개 시나리오)
```bash
# 환경변수 설정
$env:PYTHONPATH = "."

# pytest 실행 (verbose 모드)
pytest -v --tb=short

# 개별 테스트 모듈 실행
pytest tests/test_models.py -v
pytest tests/test_model_cache.py -v
pytest tests/test_pii_detection.py -v
```

#### 커버리지 리포트
```bash
pytest --cov=src --cov-report=html
# coverage/index.html 파일에서 라인별 커버리지 확인
```

### 5. 로컬 대시보드 실행

```bash
# Streamlit 서버 시작
streamlit run src/presentation/app.py

# 자동 브라우저 오픈
# 접속 주소: http://localhost:8501

# 종료: Ctrl+C
```

**대시보드 주요 기능**:
- 🏠 **대시보드 홈**: 5명 대상자의 위험도 카드 필터링
- 📊 **상세 분석**: 선택 대상자의 Attention 히트맵 + Anomaly 차트
- 📝 **복지사 피드백**: 메모 입력 → 실시간 SQLite DB 저장
- ⚙️ **시스템 설정**: API Key 설정, 임계값 조정

### 6. Docker 프로덕션 배포

#### 사전 확인
```bash
docker --version  # Docker 20.10+
docker compose --version  # Docker Compose 2.0+
```

#### 배포 단계
```bash
# 1단계: 환경변수 파일 생성
copy .env.example .env

# 2단계: 이미지 빌드 (초회만)
docker compose build

# 3단계: 백그라운드 실행
docker compose up -d

# 4단계: 로그 모니터링
docker compose logs -f care_app

# 5단계: 대시보드 접속
# http://localhost:8501 (또는 배포 서버 IP)

# 6단계: 서비스 중지 (데이터 보존)
docker compose stop

# 7단계: 서비스 재시작
docker compose start
```

#### 컨테이너 내부 문제 해결
```bash
# 컨테이너 셸 접근
docker compose exec care_app bash

# 로그 상세 조회
docker compose logs --tail=50 care_app

# 볼륨 데이터 확인
docker volume inspect care_data

# 전체 제거 (⚠️ 주의: 데이터도 삭제됨)
docker compose down -v
```

### 7. 환경변수 설정 가이드

**`.env` 파일 템플릿**:
```bash
# API Keys (선택사항 - Fallback 자동 지원)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 경로 설정 (선택사항 - 기본값 자동 적용)
DATABASE_PATH=./care_system.db
MODEL_PATH=./src/infrastructure/models/weights/attention_rnn.pt

# 로깅 레벨
LOG_LEVEL=INFO

# Flask/Streamlit 포트
PORT=8501

# 배포 환경
ENVIRONMENT=development  # 또는 production
```

### 8. 성능 튜닝 & 최적화

#### CPU 기반 추론 최적화
```python
# src/infrastructure/models/model_cache.py 수정
import torch
device = torch.device("cpu")  # 또는 "cuda" (GPU 있는 경우)

model = torch.load("attention_rnn.pt", map_location=device)
model = model.to(device)
model.eval()
```

#### 배치 처리 최적화
```bash
# 5명 대상자 순차 처리: 약 2초
# 동시 처리 권장: 배치 크기 64 이하

# 메모리 프로파일링
python -m memory_profiler src/infrastructure/persistence/seed_data.py
```

#### DB 쿼리 최적화
```sql
-- 인덱스 생성 (속도 향상)
CREATE INDEX idx_resident_id ON records(resident_id);
CREATE INDEX idx_record_date ON records(record_date);

-- 느린 쿼리 진단
EXPLAIN QUERY PLAN SELECT * FROM anomalies WHERE resident_id = 1;
```

### 9. 모니터링 및 로깅

#### 시스템 로그 확인
```bash
# 로컬 환경
tail -f logs/care_system.log

# Docker 환경
docker compose logs -f care_app --tail=100
```

#### 로그 레벨 설정
```python
# src/infrastructure/logger.py
import logging

logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/care_system.log'),
        logging.StreamHandler()
    ]
)
```

#### 성능 메트릭 수집
```bash
# 평균 응답 시간 측정
time python -m src.infrastructure.persistence.seed_data

# 메모리 사용량 모니터링
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

### 10. 보안 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 등재되어 있는가?
- [ ] API Key가 하드코딩되지 않았는가?
- [ ] Docker 이미지에 Non-root 사용자 `careuser` 설정됨?
- [ ] SQLite 데이터베이스 파일 권한이 `600`인가?
- [ ] PII 필터링 테스트 통과 (`pytest tests/test_pii_detection.py`)?
- [ ] HTTPS/SSL 인증서 설정 완료 (프로덕션)?
- [ ] 정기적 백업 스케줄 수립?

### 11. 트러블슈팅 심화 가이드

| 증상 | 원인 | 해결 방법 |
|---|---|---|
| `ModuleNotFoundError: No module named 'torch'` | PyTorch 미설치 | `pip install torch` |
| `CUDA out of memory` | GPU 메모리 부족 | CPU 모드로 전환: `device="cpu"` |
| `SQLite database is locked` | 동시 쓰기 충돌 | 연결 타임아웃 증가: `timeout=10` |
| `PermissionError: [Errno 13]` (Docker) | Non-root 권한 부족 | `docker compose exec -u root care_app chown -R careuser /app` |
| `ConnectionRefusedError: Port 8501` | 포트 충돌 | `lsof -i :8501` 후 프로세스 종료 |
| `OutOfMemory (OOM) killed` | 컨테이너 메모리 초과 | `docker-compose.yml`에서 메모리 제한 증가 |

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
* **성능 최적화 확인**: 5명의 노인 레코드를 순차 시딩할 때, `[AttentionRNNModelCache] Loading model from disk`가 1회 실행된 이후, 2~5번째 노인부터는 `Reusing cached model` 메시지 확인 가능.
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
* ⚠️ **주의 (볼륨 데이터 보존)**: 컨테이너를 정지/삭제할 때 `docker compose down -v` 또는 `docker compose down --volumes` 명령을 실행하면 마운트된 named volume(`care_data`)이 **완전히 삭제**됩니다. 데이터 손실 방지 위해 `docker compose down` (플래그 없음)으로 정지만 권장합니다.
* **Windows WSL2 환경 named volume 권장 이유**: Windows Docker Desktop(WSL2 백엔드)에서 NTFS 호스트 경로의 파일을 직접 컨테이너에 bind mount하는 경우, Non-root 사용자 권한 문제로 SQLite WAL/SHM 파일 생성 시 Permission Denied 에러가 발생할 수 있습니다. Named volume은 WSL2 내부의 ext4 파일시스템을 사용하므로 권한 문제 없음.
* **모델 파일 연동**:
  빌드 시 `attention_rnn.pt` 실측 가중치가 이미지 내부에 COPY되며, `docker-compose.yml`에서 읽기 전용 bind mount(`:ro`)로 호스트와 연결되어 호스트 상의 모델 파일 업데이트 시에도 새로운 빌드 불필요.

---

## 🛡️ API 결함 감내 및 Fallback 메커니즘 (Fault-Tolerance & Fallback)

Google GenAI 또는 OpenAI API키가 설정되지 않았거나 유효하지 않은 경우에도, 시스템 전체의 파이프라인은 중단되지 않습니다. 대신, 룰 기반(Rule-based)의 Fallback 리포트 생성 엔진이 즉시 활성화되어 의료 전문가 검수 하의 정형화된 XAI 분석 보고서를 자동 발급합니다.

### 1. Fallback 작동 흐름
* **자동 진입**: 로컬 환경 변수에 `GEMINI_API_KEY`가 없거나 기본 더미 값(`your_gemini_api_key_here`)인 경우, API 요청을 보내지 않고 **즉시 1단계 Fallback 규칙**에 진입합니다.
* **예외 격리**: 유효하지 않은 키를 입력하여 API 통신 도중 `Exception`이 발생한 경우, 이를 내부 `try-except` 블록에서 안전하게 격리하고 에러 로그를 출력한 후 2단계 규칙 기반 리포트 생성으로 자동 폴백합니다.
* **일관된 출력**: API 성공 여부와 관계없이 **동일한 형식의 의료 해석 보고서**가 대시보드에 표시되므로 복지사 사용 경험에 단절이 없습니다.

---

## 🛠️ 트러블슈팅 (Troubleshooting)

* **현상**: `seed_data.py` 실행 시 콘솔에 `[XAI_GENERATOR_ERROR] Google GenAI API Exception` 에러가 다량 출력됩니다.
  - **원인**: `.env` 파일 내에 `GEMINI_API_KEY`가 없거나 무효한 API 키가 지정된 상태입니다.
  - **대처**: 이는 시스템의 설계된 안전장치(Fallback)가 가동 중인 것으로, **정상 작동**입니다. 대시보드를 켜면 룰 기반 대체 텍스트가 정상적으로 데이터베이스에 저장되고 표시됩니다.

* **현상**: `seed_data.py` 기동 시 `DATABASE_PATH` 탐색 중 `NameError: name 'os' is not defined` 에러로 중단됩니다.
  - **대처**: `seed_data.py` 상단에 `import os`가 추가된 최신 버전 코드를 사용하고 있는지 확인하십시오.

* **현상**: Windows PowerShell에서 `Activate.ps1` 실행 시 권한 에러가 발생합니다.
  - **대처**: PowerShell을 관리자 권한으로 열어 `Set-ExecutionPolicy RemoteSigned` 명령어를 실행하여 스크립트 실행 권한을 획득하십시오.

* **현상**: Docker 실행 시 `port 8501 already in use` 에러.
  - **대처**: `docker compose down` 후 기존 컨테이너 정리하거나, 포트 변경: `docker-compose.yml`의 `ports: "8502:8501"` 수정.

* **현상**: SQLite 데이터베이스 `database is locked` 에러.
  - **대처**: 동시 접근 설정 조정: `sqlite3.connect(..., timeout=30.0)` 또는 `docker compose restart` 컨테이너 재시작.

---

## 📚 추가 자료 및 링크

- **논문 & 연구**: `docs/00_context_management/` 참고
- **아키텍처 다이어그램**: `docs/03_design/ARCHITECTURE.png`
- **테스트 보고서**: `docs/05_verification/TEST_REPORT.md`
- **API 문서**: 각 모듈의 `__doc__` 주석 참고

---

## 📞 연락처 및 지원

- **개발자**: saku13185
- **GitHub Issues**: [Report Bug](https://github.com/saku13185/caresystem/issues)
- **이메일**: (프로젝트별 지정)

---

**마지막 업데이트**: 2026년 6월 11일  
**버전**: 1.0.0 (Production Ready)
