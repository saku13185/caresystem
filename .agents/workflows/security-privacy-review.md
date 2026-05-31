---
description: 구현 코드 상에서 발생할 수 있는 인가(Authorization) 누락, 입력값 정화 부재, 민감 데이터(개인정보, 독거노인 행동 로그)의 평문 유출 취약점을 추적하고 수정 코드를 제공하는 보안 리뷰 스킬입니다.
---

[필수 입력 문서] @docs/00_context_management/context_packet.md, 백엔드/DB 구현 코드
[출력 산출물] docs/05_verification/security_report.md

[System Directive]
보안 엔지니어로서 소스코드의 취약점과 프라이버시 침해 리스크를 전수 검사하라.

보안성 검사: LLM API 요청 시 민감 정보 마스킹 처리 여부, 가상 데이터 전송 인터페이스의 인젝션(Injection) 방어 상태, 로그 파일 내 평문 노출 여부를 체크하라.

위협 모델링: 위험 취약점 등급(High/Medium/Low)에 따라 리포트를 분류 작성하고 즉각 적용 가능한 시큐어 코딩(Secure Coding) 가이드를 제공하라.

상태 관리 의무: 보안 제약 사실을 컨텍스트에 기록하라.

DECISIONS.md: 보안 검토를 통과한 특정 인가 로직 및 난독화 암호화 정책 확정 기록.