import getpass
import sys
import os

# 모듈 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.presentation.auth_guard import hash_password

def main():
    print("==============================================================================")
    print("스마트시티 독거노인 안심 돌봄 AI 에이전트 시스템 - 마스터 패스워드 해시 생성 도구")
    print("==============================================================================")
    print("이 도구는 .env 파일 내의 MASTER_PASSWORD_HASH 변수에 입력할 ")
    print("PBKDF2-SHA256 규격 단방향 암호화 해시값을 안전하게 생성합니다.")
    print("")
    
    try:
        # 터미널에서 화면 노출 없이 입력 획득
        password = getpass.getpass("설정할 마스터 비밀번호 입력: ")
        if not password:
            print("오류: 비밀번호는 비어있을 수 없습니다.")
            sys.exit(1)
            
        password_confirm = getpass.getpass("비밀번호 확인 입력: ")
        if password != password_confirm:
            print("오류: 비밀번호가 서로 일치하지 않습니다. 다시 실행해 주십시오.")
            sys.exit(1)
            
        # 해시 생성 (기본 260,000회 반복 적용)
        hashed = hash_password(password)
        
        print("\n[생성 완료]")
        print("아래 줄 전체를 복사하여 프로젝트 루트 디렉토리의 .env 파일에 추가해 주십시오:")
        print("------------------------------------------------------------------------------")
        print(f"MASTER_PASSWORD_HASH={hashed}")
        print("------------------------------------------------------------------------------")
        print("주의: 위 해시값만으로 복호화된 평문 비밀번호를 알아내는 것은 불가능합니다.")
        
    except KeyboardInterrupt:
        print("\n작업이 중단되었습니다.")
        sys.exit(0)

if __name__ == "__main__":
    main()
