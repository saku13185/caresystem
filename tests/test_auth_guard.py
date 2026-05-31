import os
import pytest
from unittest.mock import patch
from src.presentation.auth_guard import (
    hash_password,
    verify_password,
    get_master_password_hash
)

def test_verify_correct_password():
    """
    올바른 비밀번호와 PBKDF2-SHA256 해시를 전달했을 때
    검증이 성공(True)하는지 단언합니다.
    """
    password = "secret_password"
    hashed = hash_password(password, salt="staticsalt123", iterations=1000)
    
    assert verify_password(password, hashed) is True

def test_verify_incorrect_password():
    """
    잘못된 비밀번호를 전달했을 때
    검증이 실패(False)하는지 단언합니다.
    """
    password = "secret_password"
    hashed = hash_password(password, salt="staticsalt123", iterations=1000)
    
    assert verify_password("wrong_password", hashed) is False

def test_invalid_hash_format():
    """
    잘못된 해시 포맷(pbkdf2_sha256 헤더가 없거나 $ 개수가 어긋남)을 전달했을 때
    ValueError 예외가 발생하는지 단언합니다.
    """
    # pbkdf2_sha256 헤더 누락
    with pytest.raises(ValueError, match="Invalid hash format"):
        verify_password("password", "sha256$1000$salt$hashhex")
        
    # $ 구분자 개수 미달
    with pytest.raises(ValueError, match="Invalid hash format structure"):
        verify_password("password", "pbkdf2_sha256$1000$salt")

def test_different_salt_combinations():
    """
    동일한 비밀번호더라도 서로 다른 salt 또는 iteration 조합으로 해싱되었을 때
    각각 개별 해시 문자열과 올바르게 일치하는지 단언합니다.
    """
    password = "test_password"
    
    hashed_salt1 = hash_password(password, salt="saltA", iterations=1000)
    hashed_salt2 = hash_password(password, salt="saltB", iterations=2000)
    
    assert verify_password(password, hashed_salt1) is True
    assert verify_password(password, hashed_salt2) is True
    assert hashed_salt1 != hashed_salt2, "서로 다른 salt/iteration 조합은 해시가 달라야 합니다."

def test_get_master_password_hash_none():
    """
    환경변수 MASTER_PASSWORD_HASH가 설정되어 있지 않고 st.secrets도 비어있을 때
    None을 반환하는지 단언합니다.
    """
    with patch.dict(os.environ, {}, clear=True):
        # st.secrets에 대한 patch를 적용하여 Streamlit secrets도 회피
        with patch("streamlit.secrets", {}):
            hash_val = get_master_password_hash()
            assert hash_val is None
