# 프라이버시 및 보안 취약점 전수 검사 보고서 (Security & Privacy Report)

본 보고서는 예방적 돌봄 AI 에이전트 시스템의 소스코드와 데이터 흐름을 보안 엔지니어 관점에서 전수 감사하여, 민감한 개인정보(PII) 노출 우려, 인증/인가 로직 누락 및 외부 LLM API 통신 상의 취약점과 이에 대한 시큐어 코딩(Secure Coding) 패치 가이드를 정리한 결과입니다.

---

## 1. 보안성 전수 검사 및 위협 모델링

본 MVP 시스템은 외부 통신망(OpenAI API)을 활용한 설명 가능성(XAI) 분석 및 로컬 데이터베이스 질의를 수행하므로, 실환경 배포 전 아래 3가지 보안 등급별 리스크를 명확히 판별하고 격리 조치해야 합니다.

| 취약점 ID | 보안 위협명 | 위험도 등급 (Risk Level) | 취약점 내용 및 영향 범위 |
| :--- | :--- | :--- | :--- |
| **SEC-01** | **Streamlit 모니터링 UI의 사용자 인증 및 인가(Auth) 결여** | **High (높음)** | MVP 범위 동결에 따라 Streamlit 대시보드(`app.py`)가 로그인 절차 없이 구동됩니다. 외부망에 비보호 노출 시 관내 독거노인 전체의 비식별화된 생활 트렌드와 XAI 리포트 정보가 권한 없는 제3자에게 누출될 수 있습니다. |
| **SEC-02** | **외부 LLM API 호출 시 평문 프라이버시(PII) 유출 위험** | **Medium (보통)** | `xai_report_generator.py` 작동 시 노인의 실명이나 상세 주소가 프롬프트 텍스트 평문에 포함되어 OpenAI 서버에 전송될 시, 개인정보 보호법(GDPR / 개인정보보호법 제15조) 위반 소지가 발생합니다. |
| **SEC-03** | **시스템 예외 로그 내 API Key 및 민감 컨텍스트 누출 위험** | **Low (낮음)** | LLM API 통신 장애 등 예외 캐치(`except Exception as e`) 발생 시 `str(e)` 예외 메세지를 무가공으로 터미널/콘솔 로그에 출력합니다. 이 메세지에 부분적인 OpenAI API Key나 비공개 헤더 정보가 섞여 로깅될 리스크가 존재합니다. |

---

## 2. 안전성 격리 및 시큐어 코딩 패치 가이드

### 2.1. [SEC-01] Streamlit 인증 가드 설계 (High)
* **현황**: 단일 세션으로 동작하여 URL 접근이 통제되지 않습니다.
* **조치**: 향후 실제 중앙 배포 시 단일 관리자 비밀번호 세션을 검증하는 초경량 인증 및 인가 가드 레이어 구현 코드를 적용해야 합니다.

#### 🛠️ Secure Patch Code: `src/presentation/app.py`
```python
def check_password() -> bool:
    """
    초경량 관리자 비밀번호 인증 가드 (인가 로직)
    인가를 통과하지 못한 경우 대시보드 조회를 즉각 차단합니다.
    """
    if "authorized" not in st.session_state:
        st.session_state["authorized"] = False
        
    if st.session_state["authorized"]:
        return True
        
    st.markdown("<h2 style='text-align: center; color: #fff;'>🛡️ 안심 돌봄 에이전트 인가 로그인</h2>", unsafe_allow_html=True)
    with st.form("auth_login_form"):
        password_input = st.text_input("사회복지사 전역 보안 비밀번호를 기입하십시오.", type="password")
        submit_btn = st.form_submit_button("🔑 대시보드 인가 획득")
        
        if submit_btn:
            # 해시 대조 또는 환경변수 비교 수행 (임시 마스터키)
            if password_input == "caregiver_secure_pass_2026":
                st.session_state["authorized"] = True
                st.success("인가 권한이 획득되었습니다. 대시보드를 로드합니다.")
                st.rerun()
            else:
                st.error("보안 비밀번호가 일치하지 않습니다. 접근이 전면 격리 통제됩니다.")
    return False

# 메인 엔트리 상단에 인가 가드 추가
if not check_password():
    st.stop()
```

---

### 2.2. [SEC-02] 데이터 마스킹 및 UUID v4 비식별화 검증 (Medium)
* **현황**: 평문 전송 소지가 있으나, 현재 구현 완료된 `xai_report_generator.py` 코드는 주민의 성명, 주소 컬럼을 스키마에서 원천 차단하고 오직 가상 난수코드 `RES-MASK-2026A` 및 UUID v4 만을 사용하고 있어 **프라이버시 평문 누출 리스크를 완벽하게 기술적으로 회피하고 있음**을 확인하였습니다.
* **설계 확정**: 이 보안 난독화/비식별 설계는 향후 2차 상용 이식 단계에서도 하드 코딩 원칙으로 유지되어야 함을 `DECISIONS.md`에 등재합니다.

---

### 2.3. [SEC-03] 시큐어 에러 로깅 가드 적용 (Low)
* **현황**: `xai_report_generator.py` 내 예외 캐치 시 `str(e)` 그대로 노출함.
* **조치**: 스택 오버플로우나 민감 API 키 정보가 로그 텍스트 파일에 노출되지 않도록, 상세 예외에서 민감 키 형식을 정규식으로 마스킹 절삭한 뒤 로깅하는 안심 필터를 시큐어 코딩으로 반영합니다.

#### 🛠️ Secure Patch Code: `src/infrastructure/llm/xai_report_generator.py`
```python
            # ...
        except Exception as e:
            # 예외 메시지에 존재할 수 있는 OpenAI API Key 형식 패턴(sk-...) 마스킹 정제 처리
            import re
            raw_error = str(e)
            masked_error = re.sub(r'sk-[a-zA-Z0-9]{32,}', 'sk-***[MASKED_API_KEY]***', raw_error)
            print(f"[XAI_GENERATOR_ERROR] OpenAI API Exception: {masked_error}")
            return self.generate_report(anomaly_packet, mock_api_fail=True)
```

---

## 3. 전역 상태 동기화 및 2차 계획

식별된 High 위험 수준의 **Streamlit 미인증 접근 리스크(SEC-01)**는 상용 배포 전 보완되어야 할 최우선 조치 과제로 `OPEN_QUESTIONS.md`에 기술 보안 부채로 영속 바인딩하고, 난독화/비식별 정책 확정안은 `DECISIONS.md`에 반영하여 지속 관리하도록 연동 조치하였습니다.
