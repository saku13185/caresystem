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
* **DDD 레이어 아키텍처**: 순수 도메인 규칙(`domain/`), 유스케이스 구현(`usecases/`), 외부 프레임워크 및 데이터베이스 연동(`infrastructure/`), 대시보드 표현(`presentation/`) 레이어로 단방향 의존성 엄수(domain <- usecases <- infrastructure/presentation).
* **외부 프레임워크 격리**: PyTorch, Streamlit, OpenAI/GenAI SDK는 infrastructure와 presentation 레이어에 은닉하며, 유스케이스는 추상 포트 인터페이스를 정의하여 소비함.
* **배치 프로세싱 동결**: 실시간 스트리밍 분석을 배제하며, 일간 요약 배치 처리를 기반으로 설계됨.

### 3. 최근 수정 내역 (Recent Fixes)
* **수정 대상 1**: 유스케이스 계층의 DIP 위반 보완 (TECH-DEBT-03)
  - 유스케이스 레이어가 인프라 레이어의 구체 `DatabaseConnector`에 결합되지 않도록 느슨한 결합 구조(DIP)를 도입하여 단방향 의존성 흐름을 구현함.
  - **[NEW]** `src/usecases/ports/care_repository.py`: 추상 `CareRepositoryPort` Protocol 정의.
  - **[NEW]** `src/infrastructure/persistence/sqlite_care_repository.py`: `CareRepositoryPort`를 구현하며 `DatabaseConnector`를 감싸 호출하는 어댑터 클래스 도입.
  - **[MODIFY]** `src/usecases/preprocess_adl_data.py` & `src/usecases/run_anomaly_detection.py`: 구체 클래스 import를 완전히 제거하고 생성자를 통해 `CareRepositoryPort`를 주입받아 작동하도록 수정. 전처리기의 SQL 쿼리 로직을 인프라 레이어로 완전 이관.
  - **[MODIFY]** `src/infrastructure/persistence/db_connector.py` & `seed_data.py`: 유스케이스에서 이관된 SQL 쿼리 메서드(`get_adl_summaries_by_date_range`, `get_adl_summaries_before_date`) 구현 및 composition root에서의 의존성 조립 처리.
  - **[NEW]** `tests/test_dip_ports.py`: 소스코드 내 구체 DB 커넥터 직접 import 금지 여부를 검증하는 AST 정적 단언문 및 SQLite 의존성 없는 `FakeCareRepository` 단위 테스트 2건 추가.
* **수정 대상 2**: Streamlit 복지사 대시보드 마스터 로그인 세션 가드 추가 (TECH-DEBT-05)
  - 배포 환경에서의 노인 민감 데이터 보호를 위해 복지사 화면인 Streamlit 대시보드에 패스워드 인증 장벽을 추가함.
* **수정 대상 3**: AttentionRNN 모델 인메모리 싱글톤 캐시 구현 (TECH-DEBT-01)
  - 다중 주민 일괄 분석 배치 시 매번 가중치 파일(`attention_rnn.pt`)을 디스크에서 중복 로딩하던 병목을 캐싱하여 디스크 I/O를 최초 1회로 통제 및 스레드 세이프티 확보 완료.
* **수정 대상 4**: 복지사/관리자용 Streamlit 대시보드 가독성 개선 (UI-UX-01)
  - 대시보드의 사용성과 인지 가독성을 혁신하기 위해 Streamlit 레이아웃을 개선하고 주요 기능 요소들을 보강함.
  - **[MODIFY]** `src/presentation/app.py`:
    - **상단 Summary Metric Cards 추가**: 전체 대상자수, 고위험(DANGER) 수, 주의(WARNING) 수, 정상(NORMAL) 수, 그리고 조치 대기(PENDING) 건수를 나타내는 5개 메트릭 카드를 최상단에 배치.
    - **사이드바 이모지 적용**: `st.sidebar.radio` 선택 옵션에 `format_func`를 연동하여 주민별 상태(🔴/🟡/🟢)를 이모지로 표현하며, 내부 키값은 순수 `virtual_code` 문자열을 보존하여 StopIteration 오류 원천 방지.
    - **오늘 우선 확인 대상자 큐**: 사이드바 상단에 위험 등급이 `DANGER` 또는 `WARNING`이면서 조치 상태가 `PENDING`인 주민들의 실시간 우선순위 리스트 렌더링.
    - **XAI 리포트 탭 분할**: 기존 의료 disclaimer 고정 문구를 최상단에 유지하면서, 핵심 요약(상태 배지, Z-score, Boxplot 이탈 요약, AI 권장 조치 메모) 탭과 상세 분석 보고서(LLM 원문) 탭으로 뷰 분리.
    - **사회복지사 예방 조치 관문(피드백 폼) 개선**: 조치 상태에 따라 동적 경고 배너(`st.warning`, `st.success`, `st.info`)를 노출하고 피드백 폼의 명칭과 디자인을 다듬어 조치 기록 영속 저장 흐름 시각화.
    - **StopIteration 안전성 확보**: 선택 주민 매핑 시 `next((r for r in residents if r["virtual_code"] == selected_res_code), None)` 패턴과 예외 처리를 장착하여 검색 오류 방지.

### 4. 실행 및 검증 결과 (Verification Results)
* **pytest 단위 테스트**:
  - 로컬 가상환경 내 `python -m pytest` 실행 결과, 신규 테스트들을 포함하여 **총 26개 테스트 100% 무경고 통과(26 passed)** 완료.
* **DIP 의존성 역전 및 격리성**:
  - AST 구문 분석 검증 결과, 유스케이스 폴더 내에서 인프라 레이어의 구체 DB 커넥터를 참조하는 import가 전혀 존재하지 않음을 확인.
  - `FakeCareRepository` 기반으로 파일 입출력 및 SQLite 접속 없이도 모든 비즈니스 로직(전처리 및 이상 오케스트레이션)이 완벽히 작동함을 증명.
* **마스터 패스워드 접근 가드 동작**:
  - `MASTER_PASSWORD_HASH` 환경 변수 기반 단방향 PBKDF2 해시 검증 및 compare_digest 타이밍 공격 예방 가드가 정상 작동함을 입증.
* **모델 캐시 및 영속성 런타임 검증**:
  - 다중 노인 배치 추론 시 가중치 로드는 디스크에서 최초 1회만 발생하고 이후 인메모리 캐시 재사용 성공 확인. Named volume 및 non-root 권한 환경 하에서의 SQLite WAL 모드 충돌 없음 확인 완료.
* **Streamlit UI/UX 구동 검증**:
  - 로컬 Streamlit 서버 포트 8501 헤드리스 기동 검증 완료. 구문 오류나 라이브러리 참조 에러 없이 원활하게 구동됨을 실증.

### 5. 현재 구현 및 검증 현황 (Current Status)
* 11개 주요 Python 파일 정상 복원 및 로컬 .venv/Docker 컨테이너 환경의 실행 무결성 100% 달성.
* 딥러닝 디스크 I/O 최적화, 대시보드 마스터 비밀번호 세션 차단 가드, 유스케이스 계층의 DIP 의존성 역전 구조, 그리고 대시보드 가독성 및 사용성(UI-UX-01)을 완벽하게 구현 및 개선함.
* 규칙 기반 Fallback XAI 돌봄 보고서 고도화로 외부 API 키 누락 시에도 무정전 룰 기반 한글 리포트 영속 적재 완료.
* ⚠️ **[볼륨 유실 주의]**: `docker compose down -v`는 named volume을 삭제하여 DB 데이터를 초기화하므로 절대 사용금지.

### 6. 남은 과제 (Remaining Issues)
* 없음. 주요 기술 부채 및 환경 변수 불일치 에러, Streamlit UI/UX 가독성 개선(UI-UX-01)이 모두 종결되었으며, BDD 및 단위 테스트 26건이 안정적으로 통과하는 고품질의 스마트시티 안심 돌봄 관리 에이전트 시스템이 완비됨.

---

## 💡 ChatGPT와의 대화 시작 프롬프트 예시
> **사용자 프롬프트**:
> "우리는 Streamlit 복지사 대시보드에 마스터 패스워드 가드를 탑재하고, 유스케이스와 DB 어댑터를 CareRepositoryPort로 격리하여 DIP 위반을 보완했어. 또한, [UI-UX-01]을 진행해 요약 카드, 실시간 오늘 우선 확인 큐, format_func 기반 이모지 셀렉터, XAI 요약/상세 탭 분할, 동적 알림 조치 폼 등을 성공적으로 갱신했어. 26개 테스트 전체 통과 및 Streamlit 기동 검증도 무결해. 다음으로, 로드맵 상의 다음 단계인 다중 복지사 개별 계정 로그인 연동 및 세션 관리 고도화 방안에 대해 논의를 진행하고 싶어."
