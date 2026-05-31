# 스마트시티 실증 지구 상용 배포 및 확장 로드맵 (Smart City Pilot Deployment & Scaling Roadmap)

본 문서는 예방적 돌봄 AI 에이전트 시스템이 기술 부채 보완(캐시 최적화, 인증 가드, 의존관계 역전)을 완료하고 BDD 테스트를 통과한 상태에서, 향후 스마트시티 실증 지구에 실제 상용 배포된 이후 시스템을 다중 복지사 및 다중 지자체 규모로 확장하기 위해 마련된 **고도화 및 보안 강화 확장 로드맵**입니다.

---

## 1. 📍 현재 완료 상태 (Current Completion Status)

- **딥러닝 추론 최적화 완료**: `AttentionRNNModelCache` 싱글톤 패턴 연동을 통해 매 주민 분석 시 발생하는 모델 PT 파일의 디스크 중복 I/O 레이턴시 소거 완료.
- **접근 제어 가드 구축 완료**: PBKDF2-SHA256 패스워드 암호화 해싱 및 `hmac.compare_digest` 안전 비교를 탑재한 Streamlit 대시보드 로그인 장벽 완비.
- **DIP 아키텍처 역전 완료**: `CareRepositoryPort` Protocol 및 `SQLiteCareRepository` 어댑터 도입으로 유스케이스 레이어와 SQLite의 물리적 결합도를 완벽 분리.
- **데이터 보안 및 Fallback 탑재**: PII 누출 탐지 및 예외어 필터 고도화 완료 및 외부 LLM API 단선 시 무과금 규칙 기반 1단계 Fallback 요약 보고서 적재 검증 완료.
- **컨테이너 영속성 확인**: Non-root `careuser` 기반 SQLite WAL 저널 및 named volume 마운트 영속성 수립.
- **테스트 통과**: AST 정적 임포트 금지 검사 및 FakeRepository 단위 검사 등을 통합하여 **pytest 총 26건 100% Passed**.

---

## 2. 🎯 로드맵 설계 원칙 (Roadmap Design Principles)

1. **최소 침습 및 DIP 격리 유지**: 향후 데이터베이스나 인증 체계를 수정할 때도, 유스케이스(`preprocess_adl_data.py`, `run_anomaly_detection.py`) 레이어의 비즈니스 코어와 신경망 추론 로직은 일체 건드리지 않고 인프라 어댑터만 교체 및 플러그인하도록 강제합니다.
2. **보안 퍼스트 (Security First)**: 공공 실증 사업의 성격상, 노인 생활 데이터 및 조치 피드백 메모의 무결성과 기밀성을 확보하기 위해 전구간 암호화와 사후 감사 추적성을 극대화합니다.
3. **효율적 최적화 (Efficiency Optimization)**: 인메모리 캐싱과 제로 카피 연산을 활용하여, 대량의 시뮬레이션 합성 데이터 훈련 시 CPU/GPU의 자원 소모를 최소화합니다.

---

## 3. 🚀 Phase A: 실증 배포 안정화 (Pilot Deployment Stabilization)

- **목표**: 상용 인프라 이식 전, 프로덕션 환경과의 불일치를 제거하고 무중단 구동력을 확보합니다.
- **세부 태스크**:
  - `docker-compose.yml` 내에 헬스체크(`healthcheck`) 가이드를 보강하여, Streamlit 포트(8501) 미응답 시 컨테이너 자동 재기동 스케줄링 연동.
  - 상용 `.env` 환경 변수 구성 및 유효한 OpenAI/Gemini 라이브 API Key 주입 후, Fallback 모드가 아닌 2단계 GenAI 라이브 보고서 자동 생성 정확도 실증.
  - 지자체 내 모니터링 관리 장비에 마운트하여 SQLite 쓰기 레이턴시(Locking 타임아웃 30초 내) 런타임 지표 점검.

---

## 4. 👥 Phase B: 복지사 개별 계정 및 역할 기반 접근 제어 (Caregiver Accounts & RBAC)

- **목표**: 단일 마스터 비밀번호 체계의 보안 한계를 극복하고 복지사별 업무 이력 추적 및 책임 권한 격리를 실현합니다.
- **세부 태스크**:
  - `users` 마스터 테이블 설계: 사용자 고유 식별자, 이름, PBKDF2 해싱된 패스워드, 소속 지자체 코드, 관리 등급 컬럼 생성.
  - Streamlit UI 내 다중 계정 로그인 세션 바인딩 및 세션 타임아웃(30분 미활동 시 자동 세션 만료) 탑재.
  - **역할군 격리(RBAC)**: 
    - `SystemAdmin`: 지자체 주민 마스터 등록, 학습 스케줄 실행 권한.
    - `Caregiver`: 담당 지구 노인 대시보드 열람 및 조치 피드백(APPROVED/REJECTED) 기입 권한.
    - `Auditor`: XAI 보고서 생성 이력 감사 및 보안 로그 조회 권한.

---

## 5. 🔒 Phase C: HTTPS / Reverse Proxy / 보안 헤더 (Web Security Hardening)

- **목표**: 대시보드로 통하는 모든 네트워크 웹 트래픽을 암호화하고 일반적인 웹 취약점 공격 벡터를 차단합니다.
- **세부 태스크**:
  - **Reverse Proxy 아키텍처**: Caddy 또는 Nginx 경량 컨테이너를 Streamlit 컨테이너 전면에 구성하여 SSL/TLS 1.3 핸드셰이크 처리를 일임하고 Let's Encrypt를 통한 인증서 자동 갱신 연동.
  - **보안 헤더 주입**: 프록시 단에서 OWASP 보안 규격에 부합하도록 다음 필수 헤더 설정.
    - `Strict-Transport-Security` (HSTS 강제)
    - `Content-Security-Policy` (외부 스크립트 실행 제한)
    - `X-Frame-Options: DENY` (Clickjacking 공격 방어)
    - `X-Content-Type-Options: nosniff` (MIME 스니핑 방어)

---

## 6. 📊 Phase D: 감사 로그 및 운영 관측성 (Audit Logs & Observability)

- **목표**: 복지사의 조치 사실에 대한 불변의 사후 감사 이력을 보존하고 런타임 상태를 모니터링합니다.
- **세부 태스크**:
  - **감사 로그 테이블 (`audit_logs`) 설계**:
    - `id` (UUID PK), `operator_id` (복지사 ID), `action_type` (로그인, 로그아웃, 피드백_승인, 피드백_반려), `target_resident_id` (비식별 주민 코드), `ip_address`, `browser_agent`, `created_at` (타임스탬프)
  - 감사 로그 적재 API는 트랜잭션 단위로 묶어 처리하며 변경/삭제가 절대 불가능하도록 권한 통제.
  - Prometheus + Grafana 스택 연동: 컨테이너 CPU/Memory 모니터링, SQLite 락 대기 빈도 계측, 모델 캐시 히트율 실시간 시각화 대시보드 구축.

---

## 7. ⚡ Phase E: TECH-DEBT-04 훈련 루프 제로 카피 텐서 최적화 (Memory Optimization)

- **목표**: 대량의 시나리오 ADL 합성 시계열 학습 시 발생하는 메모리 할당 및 가비지 컬렉션(GC) 병목 오버헤드를 극소화합니다.
- **세부 태스크**:
  - 훈련 스크립트 내에서 넘파이 어레이 데이터에서 PyTorch 텐서 인스턴스를 루프 내 매 Epoch마다 새로 생성하는 `torch.tensor(numpy_arr)` 부분을 메모리 주소를 공유하는 제로 카피 연산자인 `torch.from_numpy(numpy_arr)`로 대체.
  - 디바이스(CPU/GPU) 전송(to device) 위치를 루프 진입 전으로 통합하고, 연산 시 인플레이스(`in-place`) 연산 처리(예: `x.add_(y)` 등)를 적용하여 중간 텐서 메모리 단편화 예방.
  - PyTorch Profiler를 학습 루프에 일시 탑재하여 리팩토링 전후의 CUDA 메모리 할당 및 오버헤드 프로파일링 보고서 작성.

---

## 8. 🗄️ Phase F: DB 확장성 및 PostgreSQL 전환 로드맵 (Database Migration)

- **목표**: 단일 파일 SQLite의 스레드 쓰기 락 한계를 극복하고, 멀티 아파트 단지 및 다중 지자체 규모의 대용량 동시 트랜잭션을 수용합니다.
- **DIP 아키텍처적 전환 설계의 극강의 이점**:
  - 이미 유스케이스 레이어가 구체 DB 모듈을 전혀 몰라도 계약 인터페이스를 바탕으로 동작하는 `CareRepositoryPort` Protocol을 소비하고 있으므로, **유스케이스 로직 및 비즈니스 코드 변경 없이** 다음 인프라 아댑터 전환만으로 DB 마이그레이션이 끝납니다.
- **세부 태스크**:
  - **PostgreSQL용 신규 어댑터 구현**: [NEW] `src/infrastructure/persistence/postgresql_care_repository.py`
    - `CareRepositoryPort` Protocol을 준수하도록 클래스 선언.
    - PostgreSQL 드라이버(`psycopg2` 또는 `asyncpg`) 커넥션 풀링 기법을 적용하여 7대 리포지토리 메서드 재구현.
  - **DDL 마이그레이션**: SQLite 테이블 스키마에 부합하는 PostgreSQL 물리 스키마 마이그레이션 DDL 스크립트 작성 및 적용.
  - **Composition Root 주입 변경**: `seed_data.py` 및 Streamlit entrypoint에서 `SQLiteCareRepository` 대신 `PostgreSQLCareRepository`를 인스턴스화하여 유스케이스 생성자에 주입.

---

## 9. ⚖️ Phase G: AI 거버넌스 및 Human-in-the-loop 운영 (AI Governance)

- **목표**: AI 오판에 의한 복지사 바이어스를 예방하고, 지속적으로 보완되는 행동 데이터 기반의 피드백 루프를 수립합니다.
- **세부 태스크**:
  - **정기 거버넌스 리뷰 위원회**: 분기별로 복지사가 기록한 '오탐 반려(REJECTED)' 피드백 사유 데이터를 추출하여 Double-StepScorer의 임계 임계치 영역(Z-score 가중치 등) 정합성 사후 조정.
  - **모델 재학습 피드백 루프 (Retraining Loop)**: 
    - 비식별화된 정상 생활 패턴 데이터를 누적 수집하여, 반기 1회 주기별로 `ModelTrainer`를 백그라운드 구동하여 `attention_rnn.pt` 가중치를 업데이트함.
    - 모델 교체 완료 시 `AttentionRNNModelCache.clear_cache()` 시그널을 호출해 핫 메모리의 기존 캐시 인스턴스를 무효화 및 동적 핫 리로딩 수행.

---

## 10. 📊 우선순위 매트릭스 (Priority Matrix)

상용화 안정성과 기술적 난이도를 종합 고려한 고도화 우선순위입니다.

| 우선순위 | 작업명 | 관련 Phase | 구현 난이도 | 영향 범위 | 기대 효과 |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | **실증 배포 안정화 및 Gemini Live 실측** | Phase A | 하 | 전체 | 실제 OpenAI/Gemini API key 기반 보고서 품질 확보 |
| **2** | **HTTPS 및 Reverse Proxy (TLS 1.3) 도입** | Phase C | 하 | 인프라 | 네트워크 구간 스니핑 전면 차단 (웹 보안 등급 확보) |
| **3** | **다중 복지사 계정 분리 및 세션 가드 (RBAC)** | Phase B | 중 | presentation | 단일 마스터 패스워드 극복 및 개인 책임성 격리 |
| **4** | **감사 로그 (`audit_logs`) 구축** | Phase D | 하 | infrastructure | 복지사 조치 사실에 대한 불변의 사후 감사 정합성 확보 |
| **5** | **PostgreSQL 영속성 어댑터 전환** | Phase F | 중 | infrastructure | 대용량 동시 트랜잭션 분산 수용 및 다중 지구 확장성 |
| **6** | **TECH-DEBT-04 훈련 루프 텐서 제로 카피 최적화**| Phase E | 중 | models | 대용량 시나리오 데이터 학습 속도 향상 및 메모리 절감 |
| **7** | **Human-in-the-loop 피드백 루프 정비** | Phase G | 상 | 거버넌스 | 복지사 오탐 피드백의 통계적 스코어러 수렴 모델화 |

---

## 11. 🏁 각 마일스톤의 완료 조건 (Milestone Criteria)

1. **Phase A (실증 안정화)**: Gemini API Key 환경변수 연동을 통한 라이브 생성 성공 및 Docker 컨테이너 내 헬스체크 통과.
2. **Phase B (RBAC)**: 대시보드 최초 화면에서 각 복지사별 ID/PW로 검증되고 담당 구역 데이터만 필터링 출력되며 30분 미활동 시 자동 세션 탈퇴 처리.
3. **Phase C (Web Security)**: SSL Labs 보안 테스트 기준 `A+` 등급 획득 및 TLS 1.3 핸드셰이크 고정 보장.
4. **Phase D (Audit & Logs)**: 복지사 피드백 기입 행위 직후 `audit_logs` 테이블에 조작 불가능한 형태로 행위자 ID 및 IP 주소가 기록됨.
5. **Phase E (Zero-Copy)**: PyTorch Profiler 계측 결과 학습 단계의 CUDA 메모리 해제 지연 및 GC 오버헤드가 기존 대비 30% 이상 감소.
6. **Phase F (DB Migration)**: PostgreSQL 어댑터를 연결한 상태에서 전체 26개 pytest 테스트가 소스코드 비즈니스 로직 수정 없이 통과.
7. **Phase G (Governance)**: 정기 검증 보고서 산출 및 반기별 `clear_cache()` 기반 딥러닝 가중치 무중단 핫 리로드 완료.

---

## 12. ⚠️ 남은 위험과 대응 전략 (Risks & Mitigation Strategies)

### 12.1. 외부 GenAI API 호출 레이턴시 지연
- **위험**: 상용 Gemini API 연동 시 네트워크 상태에 따라 리포트 산출이 최대 10~15초 소요되어 화면 지연이 일어날 수 있음.
- **대응**: 배치 분석은 복지사 대시보드 런타임 조회가 아닌, **백그라운드 자정 스케줄러 오케스트레이터 배치**에서 사전 구동되어 데이터를 SQLite/PostgreSQL에 적재 완료하므로 복지사 화면 렌더링 속도에는 지연 영향이 전혀 가지 않도록 격리 설계 완료됨.

### 12.2. SQLite 단일 파일 쓰기 락 충돌
- **위험**: 시범 지구가 5단지(노인 100명 이상) 수준으로 커질 경우 복지사의 다중 피드백 동시 기입 시 `database is locked` 예외 발생 가능.
- **대응**: 단일 파일 기반 SQLite를 사용 중일 때는 저널 모드를 WAL(Write-Ahead Logging)로 전환하고 타임아웃을 30초로 설정하여 예방하며, 단지 수 확장 임계 도달 시 즉각 **PostgreSQL 어댑터(Phase F)**로의 빠른 전환을 구비함.
