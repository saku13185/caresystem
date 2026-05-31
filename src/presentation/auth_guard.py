import os
import hashlib
import hmac
import secrets
import streamlit as st
from typing import Optional

def hash_password(password: str, salt: Optional[str] = None, iterations: int = 260000) -> str:
    """
    비밀번호를 PBKDF2-SHA256 알고리즘을 사용해 단방향 해시화합니다.
    출력 규격: pbkdf2_sha256$<iterations>$<salt>$<hash_hex>
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # pbkdf2_hmac을 이용하여 해시 유도
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", 
        password.encode("utf-8"), 
        salt.encode("utf-8"), 
        iterations
    )
    hash_hex = hash_bytes.hex()
    return f"pbkdf2_sha256${iterations}${salt}${hash_hex}"

def verify_password(password: str, hash_str: str) -> bool:
    """
    입력 비밀번호와 PBKDF2-SHA256 해시 문자열을 안전하게 대조합니다.
    형식 오류 시 ValueError를 발생시킵니다.
    """
    if not hash_str or not hash_str.startswith("pbkdf2_sha256$"):
        raise ValueError("Invalid hash format. Expected PBKDF2-SHA256 format (pbkdf2_sha256$<iterations>$<salt>$<hash>).")
        
    parts = hash_str.split("$")
    if len(parts) != 4:
        raise ValueError("Invalid hash format structure. Missing iteration, salt, or hash parts.")
        
    _, iterations_str, salt, hash_hex = parts
    
    try:
        iterations = int(iterations_str)
    except ValueError:
        raise ValueError("Invalid iteration count. Must be an integer.")
        
    # 동일한 파라미터로 입력 패스워드 재해싱
    computed_hash = hash_password(password, salt=salt, iterations=iterations)
    computed_hash_hex = computed_hash.split("$")[-1]
    
    # hmac.compare_digest를 이용한 타이밍 공격 방지 안전 비교
    return hmac.compare_digest(computed_hash_hex, hash_hex)

def get_master_password_hash() -> Optional[str]:
    """
    환경 변수 또는 Streamlit st.secrets(있을 경우)로부터 마스터 패스워드 해시를 로드합니다.
    """
    # 1. os.environ 조회
    hash_val = os.environ.get("MASTER_PASSWORD_HASH")
    if hash_val:
        return hash_val
        
    # 2. st.secrets 조회 (Streamlit Cloud 배포 등을 위한 Fallback)
    try:
        if hasattr(st, "secrets") and "MASTER_PASSWORD_HASH" in st.secrets:
            return st.secrets["MASTER_PASSWORD_HASH"]
    except Exception:
        pass
        
    return None

def require_master_password():
    """
    마스터 패스워드 기반의 접근 제어 가드를 적용합니다.
    인증되지 않은 사용자의 경우 로그인 화면을 띄우고 st.stop()으로 하단 본문 렌더링을 차단합니다.
    """
    # 1. 세션 상태 초기화
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # 2. 이미 인증 완료된 경우: 사이드바에 로그아웃 버튼 제공
    if st.session_state["authenticated"]:
        # 사이드바 하단부에 로그아웃 배치
        if st.sidebar.button("🔓 로그아웃 (Logout)"):
            st.session_state["authenticated"] = False
            st.rerun()
        return

    # 3. 인증 미완료된 경우: 마스터 패스워드 해시 확인
    master_hash = get_master_password_hash()
    
    # 해시 미구성 시 보안 위험을 알리고 즉시 차단
    if not master_hash:
        st.error("🚨 **보안 경고 (Security Warning)**")
        st.info("시스템 관리 보안 설정이 아직 비활성화되어 있습니다. 관리자 환경 설정에서 `MASTER_PASSWORD_HASH` 환경 변수를 바인딩해 주십시오.")
        st.stop()

    # 4. 로그인 폼 화면 렌더링
    st.markdown("<h2 style='text-align: center; color: #fff;'>🛡️ 안심 돌봄 관리자 포털 인증</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a0aec0;'>피돌봄 노인의 스마트홈 일상생활 위험 정보 접근을 위해 마스터 패스워드를 입력해 주십시오.</p>", unsafe_allow_html=True)
    
    # 화면 가운데 로그인을 위한 컬럼 배치
    col_l, col_c, col_r = st.columns([1, 2, 1])
    
    with col_c:
        with st.form("login_form"):
            password_input = st.text_input("마스터 패스워드 (Master Password)", type="password", help="발급받은 시스템 비밀번호를 입력하십시오.")
            submit_button = st.form_submit_button("🔑 관리포트 로그인")
            
            if submit_button:
                if not password_input:
                    st.warning("비밀번호를 입력해 주십시오.")
                else:
                    try:
                        is_correct = verify_password(password_input, master_hash)
                        if is_correct:
                            st.session_state["authenticated"] = True
                            st.success("인증에 성공하였습니다. 대시보드로 진입합니다...")
                            st.rerun()
                        else:
                            st.error("비밀번호가 일치하지 않습니다. 다시 시도해 주십시오.")
                    except Exception as e:
                        st.error(f"인증 처리 오류: {str(e)}")

    # 5. 미인증 상태이므로 하단 대시보드 본문 실행을 무조건 차단
    st.stop()
