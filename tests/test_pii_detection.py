import sys
import os

# check_db.py 가 위치한 scratch 폴더 경로를 sys.path에 추가하여 모듈을 임포트합니다.
sys.path.append(os.path.abspath(r"C:\Users\Gram Pro360\.gemini\antigravity-ide\brain\da0db975-1396-45e1-a93f-6b64613c8f44\scratch"))

from check_db import is_pii_detected

def test_pii_false_positives():
    """
    [False Positive 검증]
    이탈, 이상 등 도메인 일반 단어나 조사 결합 어휘가 PII 누출로 오탐되지 않는지 검증합니다.
    """
    false_positives = [
        "이상",
        "이탈",
        "수면 이상",
        "외출 이탈",
        "활동 감소",
        "식사 변화",
        "위험 상태",
        "출력이 제한되었습니다.",
        "모든 패턴이 통계적 신뢰 범주 내에 머물러 있는 정상(NORMAL) 상태로 분류되었습니다.",
        "Sleep 활동 점유율 Low 이탈 (편차: -11.65%)",
        "Rest 활동 점유율 High 이탈 (편차: 11.94%)",
        "최근에 이상 패턴이 감지되었습니다.",
        "이전의 수면 패턴",
        "이후의 식사 기록",
        "이동량이 정상 범주입니다."
    ]
    for text in false_positives:
        assert not is_pii_detected(text), f"False Positive 오탐 발생: '{text}'"

def test_pii_true_positives():
    """
    [True Positive 검증]
    실명 노출(문맥 결합 및 경계 격리)이나 개인 식별 정보(전화번호, 이메일, 주민번호)가
    정확히 포착되는지 검증합니다.
    """
    true_positives = [
        "이름: 홍길동 어르신",
        "성명: 김민수",
        "보호자명: 박지영",
        "담당자명: 이서연",
        "환자명: 최도진",
        "성함: 김철수",
        "주민명: 박길동",
        "연락처: 010-1234-5678",
        "이메일은 user@test.com 입니다.",
        "주민등록번호 500101-1234567 기재됨.",
        "이름: 홍길동",
        "성명: 김민수",
        "보호자명: 박지영",
        "담당자명: 이서연"
    ]
    for text in true_positives:
        assert is_pii_detected(text), f"True Positive 검출 실패: '{text}'"
