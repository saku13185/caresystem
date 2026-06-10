---
name: care-startup
description: |
  스마트시티 독거노인 안심 돌봄 AI 에이전트 시스템을 기동하는 스킬입니다.
  DB 시드 데이터 존재 여부를 확인하고, 필요 시 seed_data를 실행한 뒤 Streamlit 대시보드를 8501 포트에 기동합니다.
  기동 후 브라우저 접속 URL과 로그인 정보를 안내합니다.
---

# Care System Startup Skill

## 목적
스마트시티 독거노인 안심 돌봄 AI 에이전트 시스템의 Streamlit 대시보드를 안전하게 기동합니다.

## 실행 순서

### Step 1 — 환경 확인
프로젝트 루트가 올바른지 확인합니다.
- 작업 디렉토리: `c:\Users\Gram Pro360\.gemini\antigravity-ide\scratch\care_system`
- `.venv` 디렉토리가 존재하는지 확인합니다.
- `.env` 파일이 존재하는지, `MASTER_PASSWORD_HASH`가 설정되어 있는지 확인합니다.

### Step 2 — DB 데이터 확인 및 시드 실행
아래 명령으로 DB에 주민 데이터가 있는지 확인합니다.

```powershell
.venv\Scripts\python -c "
import sys; sys.path.append('src')
from src.infrastructure.persistence.db_connector import DatabaseConnector
db = DatabaseConnector()
rows = db.fetch_all_residents()
print(f'DB 주민 수: {len(rows)}')
"
```

주민 수가 0이거나 DB 파일이 없으면 시드를 실행합니다.

```powershell
.venv\Scripts\python -m src.infrastructure.persistence.seed_data
```

### Step 3 — Streamlit 대시보드 기동

```powershell
.venv\Scripts\python -m streamlit run src/presentation/app.py --server.port 8501 --browser.gatherUsageStats false
```

### Step 4 — 기동 완료 안내
기동 완료 후 사용자에게 다음 정보를 안내합니다.

| 항목 | 내용 |
|------|------|
| **접속 URL** | http://localhost:8501 |
| **로그인 패스워드** | .env의 MASTER_PASSWORD_HASH에 대응하는 패스워드 (기본값: `care1234`) |
| **종료 방법** | 터미널에서 `Ctrl + C` |

## 주의사항
- `port 8501`이 이미 사용 중이면 `--server.port 8502` 등으로 변경합니다.
- `.env` 파일에 `MASTER_PASSWORD_HASH`가 없으면 로그인 화면이 비활성화 상태로 표시됩니다.
- Docker로 실행하는 경우 이 스킬 대신 `docker-compose up` 을 사용합니다.
