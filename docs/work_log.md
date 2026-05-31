# 작업 로그 (Work Log)

본 문서는 프로젝트 복구 및 제1차 검증 단계에서 수행된 구체적인 작업 내역과 결과를 영구 기록하여, 개발 상태의 정합성을 확보하기 위한 문서입니다.

---

## 📅 작업 이력 (Log History)

### 1. 2026-05-31: Google Drive 다운로드 오류 복구 및 검증 (Phase 7 진입)

* **작업 개요**:
  - Google Drive 연동 과정에서 발생한 보안 경고로 인해 HTML로 덮어씌워진 11개 Python 소스코드의 전면 정상화.
  - 로컬 실행을 위한 가상환경 구축 및 전체 테스트 검증 수행.

* **세부 수행 내역**:
  1. **구글 드라이브 경고 우회 자동화 복구 스크립트 실행**
     - `docs/04_tasks_and_prompts`와 `tests`를 분석하여 11개 주요 코드가 HTML 경고문으로 훼손된 것을 발견.
     - direct download url과 query parameter(`confirm=t`, `uuid`)를 자동 추출해 재다운로드하는 파이썬 스크립트([recover_files.py](file:///C:/Users/Gram%20Pro360/.gemini/antigravity-ide/brain/b8de90da-8497-4602-ace7-87a0828b0f5e/scratch/recover_files.py))를 제작 및 실행.
     - 11개 파일 전체를 100% 정상 소스코드로 복원 완료.
  2. **가상환경 구성 및 의존성 라이브러리 설치**
     - `python -m venv .venv` 명령어를 통해 독립된 파이썬 실행 환경 구축.
     - `.venv\Scripts\python.exe -m pip install -r requirements.txt` 명령어로 PyTorch, SciPy, Streamlit, OpenAI 등의 필수 패키지 설치 완료.
  3. **자동화 BDD 테스트 스위트 검증**
     - `.venv\Scripts\python.exe -m pytest` 실행.
     - [test_harness.py](file:///c:/Users/Gram%20Pro360/.gemini/antigravity-ide/scratch/care_system/tests/test_harness.py)에 명시된 5대 핵심 검증 항목(데이터 무결성, 모델 MAE 범위, 위험 등급 분류, LLM 환각 방지, 의료 배너 주의 가드)을 포함해 **8개 전체 테스트 통과 (8 Passed)** 확인.
  4. **모의 데이터베이스 시딩 실행**
     - SQLite에 5명의 돌봄 대상 노인 시나리오(불면증, 사회고립, 영양불균형, 정상군) 시드 적재 완료.
     - 명령어: `.venv\Scripts\python.exe -c "import sys; sys.path.append('src'); from infrastructure.persistence.seed_data import seed_database; seed_database('care_system.db')"`
  5. **Streamlit 웹 안심 대시보드 로컬 기동 검증**
     - Streamlit 서버를 로컬 8501 포트로 Headless 기동하여 오류 없이 렌더링 준비를 마치고 대기하는 것을 확인 완료(정상 확인 후 프로세스는 안전하게 종료 처리).
     - 명령어: `.venv\Scripts\python.exe -m streamlit run src/presentation/app.py --server.port 8501 --server.headless true`

---

### 2. 2026-05-31: numpy.float32/numpy.float64 JSON 직렬화 오류 해결

* **작업 개요**:
  - `seed_data.py` 실행 시 발생하던 numpy 데이터 타입의 SQLite JSON 직렬화 불가 경고(`TypeError`)를 수정.
* **세부 수행 내역**:
  1. **형변환 헬퍼 함수 정의 및 적용**
     - [db_connector.py](file:///c:/Users/Gram%20Pro360/.gemini/antigravity-ide/scratch/care_system/src/infrastructure/persistence/db_connector.py) 파일 내에 `to_native_types()` 함수를 구현하여, numpy 객체 및 다차원 배열을 파이썬 표준 데이터 구조로 재귀 변환하도록 조치.
     - `insert_daily_adl_summary()` 및 `insert_anomaly_report()` 내 `json.dumps()` 전과 `native_z_score` 바인드 처리에 적용 완료.
  2. **재검증 수행**
     - pytest 8개 시나리오 100% 정상 통과 확인.
     - `seed_database()` 재실행 결과, `float32 is not JSON serializable` **WARNING 로그가 완전히 제거**되고 5명의 노인 레코드가 정상 보존됨을 확인 완료.
  3. **2026-05-31: Fallback 메커니즘 및 .env 환경 가이드 문서화**
     - [README.md](file:///c:/Users/Gram%20Pro360/.gemini/antigravity-ide/scratch/care_system/README.md) 및 [10_handoff.md](file:///c:/Users/Gram%20Pro360/.gemini/antigravity-ide/scratch/care_system/docs/05_verification/10_handoff.md)에 외부 API 장애 상황 극복을 위한 Fallback 세부 설계(1단계/2단계 구조) 및 `.env` 안전 보안 가이드를 완비하여 최종 기술 자산화 완료.

---

## 🔍 확인된 정상 동작 내역 (Confirmed Status)

1. **테스트 패스**: 8개 유스케이스 및 모델 차원 텐서 규격 연산 정상 동작.
2. **XAI Fallback 동작**: OpenAI API 키가 주입되지 않은 상황에서 `Google GenAI API Exception: 400`이 발생했으나, 오케스트레이터의 Fallback 메커니즘이 안정적으로 동작하여 한국어 대체 경보 리포트가 정상 생성 및 영속 저장됨.
3. **대시보드 기동**: CSS 주입, HSL 컬러 팔레트, Plotly 그래프 및 SQLite 라이브러리가 Streamlit 서버 상에 안정적으로 로드됨.
4. **JSON 직렬화 경고 해소**: numpy 데이터의 SQLite 입력 시 JSON 직렬화 경고가 발생하지 않음.
5. **문서화 고도화**: `.env` 설정 예시, PII/비밀키 노출 경고 및 의료 disclaimers 설명 문서 추가 완료.

---

## 🛠️ 발견된 개선 과제 및 기술 부채 (Issues & Backlogs)

1. **실제 외부 API 연동 테스트**
   - **조치 방안**: 추후 본 서비스 운영자가 유효한 API Key를 획득하여 `.env`에 기입하고 Fallback 메커니즘이 아닌 실측 모델 생성 성능을 계측해야 함.
   - **[미확인]**: 유효한 API Key가 설정된 상태에서의 실제 외부 API와의 동적 연동 결과 및 XAI 텍스트 품질 수준에 대해서는 현재 미확인 상태임.
