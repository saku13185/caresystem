---
name: care-test
description: |
  스마트시티 독거노인 안심 돌봄 AI 에이전트 시스템의 pytest 테스트를 실행하는 스킬입니다.
  전체 26건 테스트를 실행하고 결과를 카테고리별로 요약 보고합니다.
  실패한 테스트가 있으면 원인을 분석하고 수정 방향을 제안합니다.
---

# Care System Test Runner Skill

## 목적
프로젝트의 26개 pytest 테스트를 실행하고 결과를 보고합니다.

## 테스트 구성

| 파일 | 테스트 수 | 검증 내용 |
|------|-----------|-----------|
| `test_auth_guard.py` | 5건 | PBKDF2 패스워드 해시·검증 |
| `test_dip_ports.py` | 2건 | DIP 위반 AST 정적 검사 + FakeRepository |
| `test_env_paths.py` | 4건 | DATABASE_PATH / MODEL_PATH 환경변수 연동 |
| `test_harness.py` | 5건 | 데이터·모델·위험도·XAI·윤리 5대 검증 |
| `test_model_cache.py` | 5건 | 싱글톤 캐시 재사용·로드 횟수 검증 |
| `test_models.py` | 1건 | AttentionRNN 텐서 형상 검증 |
| `test_pii_detection.py` | 2건 | PII 오탐 제로 + 실명 검출 |
| `test_usecases.py` | 2건 | 전처리·이상탐지 유스케이스 통합 |

## 실행 순서

### Step 1 — 전체 테스트 실행

```powershell
.venv\Scripts\python -m pytest -v --tb=short
```

### Step 2 — 결과 해석
- **전체 통과**: `26 passed` → 정상 상태로 보고
- **일부 실패**: 실패한 테스트 이름과 traceback을 분석하여 원인과 수정 방향 제안
- **import 오류**: 의존 패키지 누락 또는 모듈 경로 문제로 판단, 해결 방법 안내

### Step 3 — 카테고리별 단독 실행 (필요 시)

```powershell
# DIP 아키텍처 검사만
.venv\Scripts\python -m pytest tests/test_dip_ports.py -v

# 보안 인증만
.venv\Scripts\python -m pytest tests/test_auth_guard.py -v

# 5대 하네스 검증만
.venv\Scripts\python -m pytest tests/test_harness.py -v

# 모델 캐시만
.venv\Scripts\python -m pytest tests/test_model_cache.py -v

# 키워드 검색
.venv\Scripts\python -m pytest -k "pii" -v
```

## 주의사항
- `attention_rnn.pt` 모델 파일이 프로젝트 루트에 없으면 `test_harness.py`가 실패합니다.
- `care_system.db`가 없으면 `test_usecases.py`가 임시 DB를 생성하고 테스트 후 삭제합니다. 정상 동작입니다.
- `MASTER_PASSWORD_HASH` 환경변수가 없어도 `test_auth_guard.py`는 통과합니다 (해당 케이스를 직접 테스트함).
