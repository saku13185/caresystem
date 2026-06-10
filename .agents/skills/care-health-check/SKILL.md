---
name: care-health-check
description: |
  스마트시티 독거노인 안심 돌봄 AI 에이전트 시스템의 종합 상태를 점검하는 스킬입니다.
  pytest 전체 실행, DB 데이터 확인, 환경변수 바인딩 확인, 모델 파일 존재 여부,
  미사용 파일 감지, DIP 아키텍처 위반 여부를 순서대로 점검하고 결과를 표로 보고합니다.
---

# Care System Health Check Skill

## 목적
배포 전 또는 장애 발생 시 시스템 전반의 상태를 한 번에 점검합니다.

## 점검 항목

| # | 점검 항목 | 합격 기준 |
|---|-----------|-----------|
| 1 | pytest 전체 통과 | 26 passed, 0 failed |
| 2 | DB 주민 데이터 존재 | 1건 이상 |
| 3 | 환경변수 MASTER_PASSWORD_HASH | 설정됨 (None 아님) |
| 4 | 환경변수 DATABASE_PATH | 설정됨 또는 기본값 care_system.db |
| 5 | 환경변수 MODEL_PATH | 설정됨 또는 기본값 attention_rnn.pt |
| 6 | attention_rnn.pt 파일 존재 | 파일 크기 > 0 |
| 7 | DIP 위반 없음 | usecase에 DatabaseConnector 직접 import 없음 |
| 8 | .env 파일 존재 | .env 파일이 프로젝트 루트에 있음 |

## 실행 순서

### Step 1 — pytest 전체 실행

```powershell
.venv\Scripts\python -m pytest --tb=short -q
```

`26 passed` 가 아닐 경우 실패한 테스트명과 traceback을 보고합니다.

### Step 2 — 환경 일괄 점검

```powershell
.venv\Scripts\python -c "
import sys, os
sys.path.append('src')
from dotenv import load_dotenv
load_dotenv(override=False)

checks = {}

# 환경변수 확인
checks['MASTER_PASSWORD_HASH'] = '✅ 설정됨' if os.environ.get('MASTER_PASSWORD_HASH') else '❌ 미설정'
checks['DATABASE_PATH'] = f'✅ {os.environ.get(\"DATABASE_PATH\", \"care_system.db (기본값)\")}' 
checks['MODEL_PATH'] = f'✅ {os.environ.get(\"MODEL_PATH\", \"attention_rnn.pt (기본값)\")}'

# 파일 존재 확인
model_path = os.environ.get('MODEL_PATH', 'attention_rnn.pt')
checks['attention_rnn.pt'] = f'✅ 존재 ({os.path.getsize(model_path):,} bytes)' if os.path.exists(model_path) else '❌ 없음'
checks['.env 파일'] = '✅ 존재' if os.path.exists('.env') else '❌ 없음'

# DB 데이터 확인
try:
    from src.infrastructure.persistence.db_connector import DatabaseConnector
    db_path = os.environ.get('DATABASE_PATH', 'care_system.db')
    db = DatabaseConnector(db_path)
    rows = db.fetch_all_residents()
    checks['DB 주민 데이터'] = f'✅ {len(rows)}건'
except Exception as e:
    checks['DB 주민 데이터'] = f'❌ 오류: {e}'

for k, v in checks.items():
    print(f'{k:30s}: {v}')
"
```

### Step 3 — DIP 위반 검사

```powershell
.venv\Scripts\python -m pytest tests/test_dip_ports.py::test_ast_check_zero_direct_db_connector_imports -v
```

### Step 4 — 결과 보고

각 점검 항목 결과를 표로 정리하여 보고합니다.

- 모든 항목 ✅ → **"시스템 정상 — 배포 가능"** 
- ❌ 항목 존재 → 항목별 수정 방법 안내

## 자동 수정 가이드

| 문제 | 해결 방법 |
|------|-----------|
| DB 주민 데이터 없음 | `.venv\Scripts\python -m src.infrastructure.persistence.seed_data` 실행 |
| MASTER_PASSWORD_HASH 미설정 | `.env`에 `MASTER_PASSWORD_HASH=<해시값>` 추가. `care-password-reset` 스킬 참조 |
| attention_rnn.pt 없음 | 모델 학습: `.venv\Scripts\python -m src.infrastructure.models.train_pipeline` |
| pytest 실패 | 실패 traceback을 분석하여 원인 수정 후 재실행 |
| DIP 위반 | `src/usecases/` 내에서 `DatabaseConnector` 직접 import 제거, `CareRepositoryPort` 사용 |
