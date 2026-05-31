# ChatGPT 공유용 프로젝트 컨텍스트 (Context for ChatGPT)

이 문서는 ChatGPT 또는 다른 LLM 에이전트와 대화를 나눌 때, 프로젝트의 도메인 지식, 아키텍처 규칙, 현재 코드 상태를 빠르고 정확하게 전달할 수 있도록 구성된 **컨텍스트 패킷**입니다.

이 문서의 내용을 복사하여 ChatGPT의 첫 프롬프트로 주입하면 혼선 없이 정밀한 리팩토링 및 신규 기능 개발 논의를 전개할 수 있습니다.

---

## 📋 [ChatGPT 프롬프트 주입용 템플릿]

### 1. 시스템 개요 (System Overview)
* **시스템명**: 독거노인 안심 예방 돌봄 AI 에이전트 시스템 (Care Agent System)
* **목적**: 독거노인의 스마트홈 일상생활(ADL) 41개 활동 점유 비율 데이터를 분석, **AttentionRNN 딥러닝 예측 모형**과 **Z-score + Boxplot IQR Double-step 이상 탐지 기법**을 활용하여 이상 패턴을 발견하고, **OpenAI/GenAI XAI 보고서**를 통해 사회복지사의 빠른 조치를 보조하는 시스템.
* **기술 스택**: Python, PyTorch (GRU), SQLite, Streamlit, Plotly, OpenAI API.

### 2. 아키텍처 및 도메인 규칙
* **DDD 레이어 아키텍처**: 순수 도메인 규칙(`domain/`), 유스케이스 구현체(`usecases/`), 인프라 어댑터(`infrastructure/`), 표현 계층(`presentation/`)의 단방향 의존성 흐름 고수 (`domain` -> `usecases` -> `infrastructure` / `presentation`).
* **데이터 무결성**: 41개 ADL 일일 점유율 합은 반드시 **정확히 100.00% (오차범위 ±0.01%)**로 보정되어야 함.
* **분석 제약**: sliding window 크기는 **과거 15일 고정**, 피처 입력 및 출력은 **41개 차원 고정**.
* **안전 제약 (윤리 가드)**:
  - 어떠한 XAI 보고서에도 개인식별정보(PII)의 노출을 금지하며 가상 코드(`RES-MASK-XXXX`)를 활용함.
  - 리포트 문두에 반드시 의료 보조지표 고정 disclaimers 배너(`[의사결정 보조지표] 본 문서는 의료진의 최종 임상적 진단을 대체할 수 없으며...`)를 하드코딩 표출함.
  - "우울증 환자로 진단됩니다"와 같은 임상 최종 진정형 단어를 차단(Blacklisted words)함.

### 3. 최근 수정 내역 (Recent Fixes)
* **수정 대상**: numpy.float32 / numpy.float64 의 JSON 시리아라이즈 경고
* **수정 전 현상**: `seed_data.py` 실행 시 SQLite 데이터 적재 연산 중 `TypeError: Object of type float32 is not JSON serializable` 오류와 함께 이상 보고서 생성 경고가 출력됨.
* **수정 목적**: `numpy.float32`, `numpy.float64`, `numpy.int64`, `np.ndarray` 등의 numpy 데이터 타입이 `json.dumps()`에 인입되더라도 오류를 일으키지 않도록 사전에 표준 타입으로 변환함.
* **적용된 2차 변경 상세**:
  * **[MODIFY]** `src/infrastructure/persistence/db_connector.py`:
    - JSON 직렬화 전 데이터 구조를 재귀적으로 돌며 numpy 타입을 파이썬 표준 타입(numpy generic -> `.item()`, numpy array -> `.tolist()`)으로 치환하는 `to_native_types` 헬퍼 함수를 추가.
    - `insert_daily_adl_summary` 및 `insert_anomaly_report` 메서드 내 `json.dumps()` 직전과 `z_score` 파라미터 바인드 직전에 본 안전 변환 필터를 적용.
    - 기존의 물리 DB 스키마, 호출 시그니처 및 저장 포맷(JSON 규격)은 기존과 100% 동일하게 유지.
  * **[변경 없음]** `src/infrastructure/scorers/double_step_scorer.py`:
    - 도메인/유스케이스 계층의 계산 로직 침범을 방지하기 위해 Double-step 판정 알고리즘 자체는 수정하지 않고, 인프라층 어댑터(`db_connector.py`)에서 문제를 완전 흡수하도록 설계함.
  * **[변경 없음]** 기타 소스코드 파일 및 테스트 파일 일체.

### 4. 실행 및 검증 결과 (Verification Results)
* **pytest**: 
  - `pytest` 실행 결과, **8개 테스트 전체 통과 (8 passed)**로 기존 검증 시나리오 무결성 유지.
* **seed_data.py**:
  - `seed_database()` 가동 결과, 5명 분의 다채로운 이상 시나리오 모의 데이터 적재 성공.
  - **`float32` JSON 시리아라이즈 WARNING**: **완전 해소** (관련 TypeError 콘솔 출력 제거됨).
* **Streamlit**:
  - `localhost:8501`에서 대시보드 서버가 정상 구동되고, CSS 주입 및 Plotly 그래프 렌더링이 문제없이 연동됨을 교차 검증 완료.

### 5. 현재 구현 및 검증 현황 (Current Status)
* 11개 주요 Python 파일 100% 정상 소스코드로 복원 완료.
* `.venv` 로컬 가상환경 구성 및 `requirements.txt` 의존성 설치 완료.
* `pytest` 8건 Pass 완료 (5대 검증 항목 통과).
* `care_system.db` 내 5인 데이터 적재 완료 및 Streamlit 8501 뷰어 실행 검증 완료.
* **JSON 직렬화 경고 해결 완료**: numpy 형변환 가드로 에러 제로화 성공.

### 6. 남은 과제 (Remaining Issues)
* **Google GenAI API 키 미설정**: API_KEY_INVALID로 인한 LLM 생성 장애 로그 잔존 (단, Fallback 대체 텍스트가 설계에 따라 정상 발행되어 안정 작동함).
* **[미확인]**: 유효한 API Key를 주입했을 때의 실제 Gemini API 응답 생성 성능 및 XAI 리포트 한글 품질 검증.
* **PyTorch 가중치 모델 로드 검증**: 현재 로컬에 `attention_rnn.pt` 파일이 없어 오케스트레이터가 Mock 예측(통계 노이즈) 모드로 작동하고 있음. `train_pipeline.py`를 실행하여 실제 모델 가중치 파일을 학습 및 생성하고, 이를 정상 로드하여 실제 GRU 신경망 순방향 추론이 돌아가는지 검증해야 함.

### 7. 다음 수정 예정 후보 (Next Task)
* **Task명**: PyTorch AttentionRNN 모델 학습 실행 및 로컬 추론 동작 검증
* **이유**: 현재 시계열 예측 모듈이 Mock 예측(Fallback) 모드로 동작 중이므로, 실제 딥러닝 모델 가중치를 학습/생성하고 오케스트레이터가 모델 파일을 성공적으로 로드하여 순방향 추론이 정상 수행되는지 검증하기 위함.
* **대상 파일**: `src/infrastructure/models/train_pipeline.py` (학습 실행), `src/infrastructure/models/attention_rnn.py` (동적 모델 로드)
* **변경 예정 내용**: 별도의 소스코드 변경 없이 학습 파이프라인 스크립트를 구동하여 `attention_rnn.pt` 파일을 빌드 및 적재.
* **완료 조건**: `attention_rnn.pt` 가중치 파일이 성공적으로 생성되고, `run_anomaly_detection.py` 가동 시 Mock Fallback 로그가 아닌 실제 AttentionRNN 추론 연산이 수행됨.
* **확인 방법**: 학습 실행 후 pytest 스위트를 재실행하여 추론 테스트의 통과 여부 및 모델 가중치 파일 탐지 로그 확인.
* **ChatGPT에 상담할 점**: `train_pipeline.py`가 과거 15일 슬라이딩 윈도우 인풋 규격 `(Batch, 15, 41)`과 16일 차 예측 아웃풋 규격 `(Batch, 41)`에 완벽하게 부합하는 데이터셋 제너레이터를 구성하여 학습을 전개하는지 코드 정합성 검증 방법.

---

## 💡 ChatGPT와의 대화 시작 프롬프트 예시
> **사용자 프롬프트**:
> "우리는 numpy.float32 / numpy.float64 의 JSON 시리아라이즈 경고를 해결하고, Gemini API 키 미설정 상태에서의 Fallback 작동 메커니즘과 .env 설정 가이드를 README.md 및 10_handoff.md에 문서화 완료했어. 현재 상태 패킷은 위와 같아. 다음 단계로, 실제 PyTorch AttentionRNN 모델 가중치 파일(attention_rnn.pt)을 생성하기 위해 train_pipeline.py를 실행하고, 이를 오케스트레이터에서 정상적으로 로드하여 Fallback(Mock 예측)이 아닌 실측 신경망 추론이 작동하는지 검증하고 싶어. 기존 모델 구현과 학습 파이프라인의 입출력 형상이 맞는지 점검하고 안전하게 실행할 계획을 검토해줘."
