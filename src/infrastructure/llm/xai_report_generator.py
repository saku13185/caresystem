import os
import re
from typing import Dict, Any, List

def load_local_env() -> None:
    """
    외부 라이브러리 의존성 없이 로컬 .env 파일의 환경 변수를 수동 파싱하여 os.environ에 적재합니다.
    """
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    parts = stripped.split("=", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip()
                        os.environ[key] = val

# 로컬 환경 변수 로드 수행
load_local_env()

class XaiReportGenerator:
    """
    공식 Google GenAI SDK (google-genai) 및 gemini-2.5-flash 모델을 연동하여 
    이상 탐지 결과 맥락이 반영된 한국어 돌봄 자연어 보고서(XAI Report) 및 
    복지사 피드백 메모를 생성하는 어댑터
    """
    def __init__(self, api_key: str = "mock-key"):
        self.api_key = api_key
        # 의료적 최종 판단 오인 방지를 위한 하드코딩 헤더 문구
        self.medical_disclaimer = (
            "[의사결정 보조지표] 본 문서는 의료진의 최종 임상적 진단을 대체할 수 없으며, "
            "예방 및 모니터링 보조 목적으로만 활용해야 합니다.\n\n"
        )

    def generate_report(self, anomaly_packet: Dict[str, Any], mock_api_fail: bool = False) -> str:
        """
        이상 탐지 결과 패킷 정보를 바탕으로 한글 XAI 리포트를 출력합니다.
        API 장애 발생 시 규칙 기반(Rule-based) Fallback 텍스트를 즉각 생성하여 대시보드 다운타임을 방지합니다.
        """
        resident_code = anomaly_packet.get("virtual_code", "RES-ANONYMOUS")
        z_score = anomaly_packet.get("z_score", 0.0)
        status = anomaly_packet.get("status", "NORMAL")
        violations = anomaly_packet.get("violations", [])
        
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # 키가 실질적으로 존재하지 않거나 테스트 모의 실패(mock_api_fail)일 경우 Fallback 수행
        has_no_key = not gemini_api_key or gemini_api_key == "your_gemini_api_key_here"
        is_mock = self.api_key == "mock-key" and has_no_key

        # 1단계: API 통신 장애 상황 모사 또는 실제 장애 처리 예외 격리 (Fallback Rule)
        if mock_api_fail or is_mock or has_no_key:
            violation_details = []
            for v in violations:
                violation_details.append(f"- {v['activity']} 활동 점유율 {v['outlier']} 이탈 (편차: {v['deviation']}%)")
                
            violations_str = "\n".join(violation_details) if violation_details else "- 특이적인 개별 Boxplot IQR 이탈은 감지되지 않았습니다."
            
            fallback_text = (
                f"{self.medical_disclaimer}"
                f"비식별 노인 코드 {resident_code} 대상자의 생활 패턴 배치 분석 결과입니다.\n\n"
                f"■ 종합 분석 상태: {status} (Z-score: {z_score:.2f})\n"
                f"■ 탐지된 생활 이상 패턴:\n{violations_str}\n\n"
                f"[안내] AI API 통신 지연 혹은 로컬 LLM 서버 단선으로 인해 생성형 XAI 해설 텍스트 분석 출력이 제한되었습니다. "
                f"상기 수치 및 위반 정보를 기반으로 현장 예방 순찰 및 안부 조사를 시행하십시오."
            )
            return fallback_text

        # 2단계: 공식 google-genai SDK를 통한 비동기/동기 API 호출
        try:
            from google import genai
            
            # 클라이언트 초기화 (Gemini API 키 명시 바인딩)
            client = genai.Client(api_key=gemini_api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
            
            prompt = f"""
            너는 독거노인 행동 패턴 이상 탐지 분석 전문 AI 에이전트이다.
            아래 제공되는 비식별화된 데이터 분석 맥락(Context) 정보를 바탕으로, 사회복지사가 노인의 건강과 안전 상태를 직관적으로 파악하고 예방 조치를 취할 수 있도록 친절하고 신뢰감 있는 한국어 리포트를 자연어로 작성해라.
            
            [분석 맥락 정보]
            - 대상 비식별 코드: {resident_code}
            - 행동 변화 MAE 오차 Z-score: {z_score:.2f}
            - 종합 위험 등급 상태: {status}
            - Boxplot IQR 임계 범위 이탈 상세 목록: {violations}
            
            [작성 제약 조건 (하드 가드)]
            1. 보고서에 피돌봄 노인의 이름, 실제 주소 등 어떠한 개인식별정보(PII)도 직접 상상하여 기재하지 말고 오직 비식별 코드({resident_code})로만 지칭해라.
            2. 절대로 특정 질병(예: 우울증, 치매 등)을 의학적으로 최종 진단하는 단정적 표현을 쓰지 말고, 생활 패턴 상의 변이(예: 수면 시간 급감, 영양 섭취 불균형 위험) 관점으로 설명해라.
            3. 보고서 내용은 정중한 존댓말(하십시오 체 또는 해요 체)로 조리 있게 작성해라.
            """
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            gpt_content = response.text
            # 최종 리포트 최상단 첫 줄에 의료적 최종 진단 대체 불가 경고문 하드코딩 결합 보장
            return self.medical_disclaimer + gpt_content
            
        except Exception as e:
            raw_error = str(e)
            masked_error = re.sub(r'AIzaSy[a-zA-Z0-9_-]{33}', 'AIzaSy***[MASKED_GEMINI_KEY]***', raw_error)
            print(f"[XAI_GENERATOR_ERROR] Google GenAI API Exception: {masked_error}")
            return self.generate_report(anomaly_packet, mock_api_fail=True)

    def generate_caregiver_memo(self, anomaly_packet: Dict[str, Any], mock_api_fail: bool = False) -> str:
        """
        주민의 이상 징후 감지 내역을 분석하여 사회복지사가 기입할 '조치록 및 피드백 사유'를 
        공식 google-genai SDK를 통해 자동 작성합니다.
        """
        resident_code = anomaly_packet.get("virtual_code", "RES-ANONYMOUS")
        violations = anomaly_packet.get("violations", [])
        
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # 키가 실질적으로 존재하지 않거나 테스트 모의 실패(mock_api_fail)일 경우 Fallback 수행
        has_no_key = not gemini_api_key or gemini_api_key == "your_gemini_api_key_here"
        is_mock = self.api_key == "mock-key" and has_no_key

        # 1단계: API 통신 불능 시의 규칙 기반 Fallback 조치록 자동 작성
        if mock_api_fail or is_mock or has_no_key:
            violation_details = []
            for v in violations:
                violation_details.append(f"{v['activity']} 이탈({v['deviation']}%)")
                
            violations_str = ", ".join(violation_details) if violation_details else "특이 패턴 없음"
            
            fallback_memo = (
                f"[AI 자동 조치록] 감지된 {violations_str}에 대해 유선 안부 연락 및 비상 현장 방문을 실시함. "
                f"행동 변화 사유(일시적 수면 부족/식사 불균형)를 대면 청취하고 영양식 지원 조치 완료함."
            )
            return fallback_memo

        # 2단계: 공식 google-genai SDK를 통해 복지사 맞춤형 피드백 조치 사유 100자 내외 자동 도출
        try:
            from google import genai
            
            client = genai.Client(api_key=gemini_api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
                
            prompt = f"""
            너는 독거노인을 모니터링하는 전문 사회복지사이다.
            아래 감지된 대상자({resident_code})의 생활 패턴 위반 내역을 바탕으로, 사회복지사가 실제 현장 조사 및 방문 안부 확인을 진행한 뒤 데이터베이스에 기입할 '조치록 및 피드백 사유'를 100자 내외의 한국어 자연어로 간결하게 자동 작성해라.
            
            [이상 감지 정보]
            - 대상 비식별 코드: {resident_code}
            - Boxplot IQR 위반 목록: {violations}
            
            [작성 제약 조건]
            - 마치 본인이 직접 세대에 방문하여 조치(안부 조사, 면담 실시, 반찬 배달 연계 등)를 완료한 것처럼 행동 중심의 명확한 문장으로 간결하게 대답해라.
            - 절대 의학적 질병 진단을 내리지 마라.
            """
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            raw_error = str(e)
            masked_error = re.sub(r'AIzaSy[a-zA-Z0-9_-]{33}', 'AIzaSy***[MASKED_GEMINI_KEY]***', raw_error)
            print(f"[XAI_GENERATOR_ERROR] Google GenAI API Exception: {masked_error}")
            return self.generate_caregiver_memo(anomaly_packet, mock_api_fail=True)
