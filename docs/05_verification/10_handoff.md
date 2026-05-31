# 개발 완료 및 운영 인수 인계 보고서 (Deployment & Handoff Report)

본 문서는 예방적 돌봄 AI 에이전트 시스템의 전체 아키텍처 및 핵심 백엔드/프론트엔드 모듈 개발이 100% 완료됨에 따라, 다른 연구자 및 개발자가 시스템을 로컬/프로덕션 환경에 신속하게 배포하고 운영 및 디버깅을 지속할 수 있도록 데브옵스 인프라 명세와 실행 방법을 자산화한 최종 인도용 가이드입니다.

---

## 1. 프로젝트 핵심 상태 요약 (Development Summary)

본 스마트시티 개론 연구 연계 AI 시스템은 독거노인의 일상생활(ADL) 센서 로그 패턴을 분석하여 고독사 및 우울 이상 패턴을 예방 조기 발견하는 목적을 가집니다.

* **최종 완수 상태**: `Stage 6 - 개발 워크플로 최종 종결 및 동결(Freeze)` 완료.
* **4대 완수 작업 (MVP Sprint Tasks)**:
  1. **Task 1 (데이터베이스 및 가상 제너레이터)**: 비식별 SQLite PK/FK 스키마 구축 완료 및 41개 일상 행동의 총합이 100.00% 정규화 정합성을 갖춘 30일 시계열 데이터 시드 생성 스크립트 구축 완료.
  2. **Task 2 (AttentionRNN 예측 모델)**: 과거 15일 슬라이딩 윈도우 기반 16일 차 41개 ADL 점유비 예측 및 15일간 각 날짜별 기여 중요도(Attention Weights)를 정밀 추출하는 PyTorch GRU 신경망 및 훈련/추론 파이프라인 완수.
  3. **Task 3 (Double-step 스코어링 & LLM XAI)**: 1단계 MAE 오차의 Z-score 판정 및 2단계 Boxplot IQR 임계 범위 이탈 이중 검증 분류기 탑재 완료 및 의료 disclaimer가 하드코딩된 한글 XAI 리포트 OpenAI API/Fallback 생성기 구축 완수.
  4. **Task 4 (Streamlit 웹 대시보드 UI)**: 다크모드 글라스모피즘 미학 테마 적용, Plotly 어텐션/IQR 시각화 차트 제공, 정오탐 피드백 기입 즉시 SQLite DB 영속성 갱신 연동 완수.
* **BDD 하네스 테스트 결과**: 5대 핵심 지표(데이터 무결성, 모델 오차 바인딩, 임계치 분류 정합성, 설명의 데이터 일치성, 윤리 가드) 자동화 검증을 포함해 전체 테스트 **100% 통과 (8 passed)**. (복원 후 검증 완수)

---

## 2. 배포 및 운영 인프라 스크립트 명세

프로덕션급의 격리 배포 환경 조성을 위해 Docker 및 Docker Compose 스크립트를 완비하였습니다.

### 2.1. 환경 변수 템플릿 (`.env.example`)
* **OPENAI_API_KEY**: OpenAI 서비스 호출용 API 키 (sk-...)
* **MODEL_PATH**: AttentionRNN 모델 파라미터 파일명 (`attention_rnn.pt`)
* **DATABASE_PATH**: SQLite 데이터베이스 파일명 (`care_system.db`)

### 2.2. 컨테이너 이미지 스펙 (`Dockerfile`)
* **베이스**: `python:3.12-slim` (경량 오피셜 이미지)
* **보안 통제**: 컨테이너 내부 침투 시 권한 탈취를 차단하는 **Non-root 전용 사용자 (`careuser`)** 환경 격리 구동.
* **경로 보장**: `ENV PYTHONPATH=/app` 환경 변수를 주입하여 파이썬 패키지 의존성 탐색 오류 영구 예방.

### 2.3. 서비스 오케스트레이션 (`docker-compose.yml`)
* 포트 포워딩 `8501:8501` 적용 및 SQLite 파일 `./care_system.db`를 볼륨 마운트하여 컨테이너 셧다운 시에도 복지사의 정오탐 피드백 메모 데이터가 안전하게 보존되도록 보장.

---

## 3. 2차 개선과제 및 아키텍처적 기술 부채 목록

차기 개발 주기에서 우선 조치해야 할 코어 보안 및 성능 리팩토링 항목을 [OPEN_QUESTIONS.md](file:///d:/%EC%97%B0%EA%B5%AC%EC%8B%A4/%EC%97%B0%EA%B5%AC/%EC%8A%A4%EB%A7%88%ED%8A%B8%EC%8B%9C%ED%8B%B0%EA%B0%9C%EB%A1%A0/docs/00_context_management/OPEN_QUESTIONS.md)에 동기화 자산화하였습니다.

1. **`[TECH-DEBT-01]` 모델 가중치 중복 디스크 I/O 병목 해소**: 싱글톤 인메모리 캐시 전환을 통한 배치 조회 성능 최적화.
2. **`[TECH-DEBT-03]` 유스케이스 계층의 DIP 위반 보완**: 구체 DB 커넥터 직접 임포트를 해제하고 추상 레포지토리 포트 인터페이스 주입 설계 도입.
3. **`[TECH-DEBT-04]` Tensor 변환 O(N) 오버헤드 최적화**: 훈련 루프 내 `torch.tensor` 복사를 주소 공유 포인터인 `torch.from_numpy` 제로 카피 연산으로 변경.
4. **`[TECH-DEBT-05]` 웹 대시보드 로그인 인증 세션 추가 (High Security)**: 상용 배포 전 전용 마스터 패스워드 가드 UI 탑재.
5. **`[TECH-DEBT-06]` 에러 콘솔 스택 PII API Key 마스킹 필터 추가**: 콘솔 출력에 sk-... 등의 원천 토큰 노출 방지를 위한 정규식 안심 필터 인터셉터 장착.
6. **`[BUG-01]` SQLite 저장 시 numpy `float32` 타입의 JSON 직렬화 불가(TypeError) 오류**: Double-step 연산 및 Z-score 통계 출력값이 float32/64로 SQLite 쿼리에 인입 시 `json.dumps()` 예외 발생. 데이터 저장소 연입 전 명시적 float 캐스팅 적용 필요. (복원 테스트 검증 과정에서 추가 식별됨 -> **[해결 완료]** `db_connector.py` 내 `to_native_types` 재귀 캐스팅 가드로 조치 완료)

---

## 4. XAI 생성 모델 연동 및 무정전 안정 운영 가이드 (XAI Handoff Guidelines)

본 시스템은 외부 대형 언어 모델(LLM)을 활용하여 사회복지사에게 설명 가능한 AI(XAI) 리포트를 제공합니다. 외부 API 연동의 불안정성을 통제하기 위해 설계된 아키텍처 명세 및 운영 가이드라인입니다.

### 4.1. API Key Dependency (외부 API 의존성)
* 시스템은 Google GenAI 공식 SDK 및 `gemini-2.5-flash` 모델을 사용하여 자연어 리포트를 동적으로 도출합니다.
* 연동을 위해서는 로컬 `.env` 파일에 `GEMINI_API_KEY` 환경 변수가 바인딩되어 있어야 합니다. (더미 입력값: `GEMINI_API_KEY=AIzaSy...[더미 키 형식]`)
* API 보안을 위해 콘솔 에러 출력부([xai_report_generator.py:L106-107](file:///c:/Users/Gram%20Pro360/.gemini/antigravity-ide/scratch/care_system/src/infrastructure/llm/xai_report_generator.py#L106-107))에 키 노출 방지를 위한 정규식 마스킹 인터셉터가 탑재되어 있습니다.

### 4.2. Fallback Safety Mechanism (장애 감내 안전장치)
* 외부 API 장애(키 미설정, 네트워크 단선, 호출 할당량 초과)가 감지되더라도 전체 이상 탐지 파이프라인과 SQLite 적재, Streamlit UI는 절대 다운되지 않습니다.
* `xai_report_generator.py` 내 `try-except` 예외 격리 및 `mock_api_fail=True` 재귀 복구 설계에 따라, API 호출 실패 시 즉시 **규칙 기반(Rule-based)의 Fallback 한글 리포트**를 로컬에서 자동 조립하여 데이터베이스에 영속화합니다. 이는 외부 요인으로 인한 시스템 전체 마비를 원천 방지하는 핵심 안전장치입니다.

### 4.3. Operational Notes (운영 시 주의사항)
* 배포 및 가동 시 `.env` 파일이 Git 저장소에 커밋되어 노출되지 않도록 강력히 통제해야 합니다.
* 시스템은 비동기 스트리밍이 아닌 일일 자정 배치 처리를 기반으로 동작하므로, API 호출 속도 제한(Rate Limit)에 거의 영향을 받지 않습니다.

### 4.4. Known Non-Critical Issues (알려진 비임계 결함/현상)
* **API_KEY_INVALID 경고 로그 출력**: `.env`에 유효하지 않은 API 키가 등록되어 있을 경우, 콘솔에 `[XAI_GENERATOR_ERROR] Google GenAI API Exception: ...` 로그가 출력되나, 이는 Fallback 안전장치가 정상 가동 중임을 의미하므로 서비스 운영 상 무해합니다.

### 4.5. Verification Checklist (운영 확인 체크리스트)
- [ ] `.env` 파일에 유효한 `GEMINI_API_KEY`와 `GEMINI_MODEL=gemini-2.5-flash`가 기입되어 있는가?
- [ ] 가상환경 `.venv`가 활성화되고 `pytest` 실행 시 8개 테스트 시나리오가 모두 성공하는가?
- [ ] 시드 데이터 생성 명령어 실행 후 `caregiver_alerts` 및 `anomaly_reports` 테이블에 분석 결과가 누락 없이 기입되는가?

### 4.6. Next Maintainer Notes (차기 유지보수자 인수인계 가이드)
* 실제 유효한 API Key를 적용하여 실측 테스트를 진행하려면, 발급된 키를 `.env`에 배치한 후 `.venv/Scripts/python.exe`로 `seed_database()`를 실행하여 생성 과정을 계측하십시오.
* XAI 보고서의 어조를 바꾸거나 요약 스타일을 수정하려면 [xai_report_generator.py:L79-93](file:///c:/Users/Gram%20Pro360/.gemini/antigravity-ide/scratch/care_system/src/infrastructure/llm/xai_report_generator.py#L79-93) 내의 System Prompt 영역을 안전하게 수정하되, 아래의 윤리적 가이드라인 제약 조건을 절대 침범하지 않도록 주의하십시오.

### 4.7. 윤리적 및 임상적 제약 조건의 준수 (Ethical Disclaimer)
* **임상 진단 단정 금지**: 보고서 텍스트에 "피돌봄 노인은 우울증 환자로 판단됩니다" 또는 "치매가 의심됩니다"와 같은 임상적 최종 진단성 문장을 포함시키는 것을 절대 금지합니다.
* **의료진 최종 판단 대체 불가 고정 표출**: 모든 보고서의 문두에는 다음 배너가 고정 하드코딩 결합되어 표출되어야 합니다:
  `[의사결정 보조지표] 본 문서는 의료진의 최종 임상적 진단을 대체할 수 없으며, 예방 및 모니터링 보조 목적으로만 활용해야 합니다.`
* **개인식별정보(PII) 격리**: 데이터베이스 및 LLM 통신 패킷에는 노인의 성명, 주소 대신 난수화된 비식별화 코드(`RES-MASK-2026A` 등)만 전달되어야 합니다.
