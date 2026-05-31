---
description: 전체 요구사항 중 첫 번째 스프린트에서 구현할 MVP 범위를 확정하는 스킬입니다. 반드시 포함할 범위(Must)와 명시적 제외 범위(Won't)를 철저히 분리하여 스코프 비대화를 제어합니다.
---

[필수 입력 문서] @docs/02_requirements/20_requirements_final.md
[출력 산출물] docs/02_requirements/06_mvp_scope.md

[System Directive]
요구사항 명세서를 검토하여 MoSCoW 방법론 기반으로 개발 범위를 동결하라.

스코프 제어: Must(시뮬레이터, AttentionRNN 훈련/추론, LLM 프롬프팅 파이프라인, Streamlit 대시보드), Won't(실제 물리 센서 연동, 고도화된 회원 인증, 모바일 앱 패키징)를 분리하라.

범위 부활 방지: 제외 범위가 차후 설계 및 코딩 단계에서 임의 추가되지 않도록 강력한 스코프 가드레일을 선언하라.

상태 관리 의무: 범위 결정의 기술적 근거를 상태 관리에 동기화하라.

DECISIONS.md: MVP Must/Won't 스코프 맵을 최종 확정 레코드로 등록.

context_packet.md: Current Stage를 'Phase 2 완료'로 갱신하고 제외 범위 제약조건을 컨텍스트 페일로드에 동결 주입.