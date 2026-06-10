---
name: care-password-reset
description: |
  스마트시티 독거노인 안심 돌봄 AI 에이전트 시스템의 마스터 패스워드를 재설정하는 스킬입니다.
  새 패스워드로 PBKDF2-SHA256 해시를 생성하고 .env 파일의 MASTER_PASSWORD_HASH를 업데이트합니다.
  패스워드를 잊었거나 정기 교체가 필요할 때 사용합니다.
---

# Care System Password Reset Skill

## 목적
`MASTER_PASSWORD_HASH` 환경 변수를 새로운 패스워드에 대응하는 PBKDF2-SHA256 해시로 업데이트합니다.

## 실행 순서

### Step 1 — 새 패스워드 입력 받기
사용자에게 새로 설정할 패스워드를 물어봅니다.
- 최소 8자 이상 권장
- 영문자 + 숫자 혼합 권장
- 단순 패스워드(예: `1234`, `admin`)는 경고

### Step 2 — 해시 생성

아래 Python 코드로 새 해시를 생성합니다. `NEW_PASSWORD` 자리에 실제 패스워드를 넣습니다.

```powershell
.venv\Scripts\python -c "
import sys, os
sys.path.append('src')
from src.presentation.auth_guard import hash_password
pw = 'NEW_PASSWORD'
hashed = hash_password(pw)
print('MASTER_PASSWORD_HASH=' + hashed)
"
```

### Step 3 — .env 파일 업데이트

생성된 해시값으로 `.env` 파일의 `MASTER_PASSWORD_HASH` 행을 교체합니다.

```
MASTER_PASSWORD_HASH=pbkdf2_sha256$260000$<새 salt>$<새 해시>
```

### Step 4 — 검증

새 패스워드가 올바르게 등록됐는지 확인합니다.

```powershell
.venv\Scripts\python -c "
import sys, os
sys.path.append('src')
from dotenv import load_dotenv
load_dotenv(override=True)
from src.presentation.auth_guard import verify_password, get_master_password_hash
stored = get_master_password_hash()
result = verify_password('NEW_PASSWORD', stored)
print('검증 결과:', '✅ 성공' if result else '❌ 실패')
"
```

### Step 5 — Streamlit 재시작

패스워드 변경 후 실행 중인 Streamlit을 재시작해야 새 해시가 적용됩니다.

```powershell
# 실행 중인 Streamlit 종료 후 재시작
.venv\Scripts\python -m streamlit run src/presentation/app.py --server.port 8501 --browser.gatherUsageStats false
```

## 주의사항
- 패스워드 평문은 절대 `.env`에 저장하지 마세요. 해시만 저장합니다.
- `.env` 파일은 `.gitignore`에 포함되어 있어야 합니다. 확인: `git check-ignore -v .env`
- Docker 환경에서는 `docker-compose.yml`의 `env_file` 또는 `-e` 옵션으로 주입하세요.
- 패스워드를 분실한 경우 이 스킬로 새 패스워드로 덮어쓸 수 있습니다.

## 현재 기본 설정 (참고)
| 항목 | 값 |
|------|-----|
| 현재 기본 패스워드 | `care1234` |
| 해시 알고리즘 | PBKDF2-SHA256 |
| 반복 횟수 | 260,000회 |
