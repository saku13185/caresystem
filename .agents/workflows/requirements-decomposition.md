---
description: 확정된 목표정의서를 기반으로 검증 가능한 수준의 기능(FR) 및 비기능(NFR) 요구사항을 도출하는 스킬입니다. 시나리오와 유스케이스, BDD 기반의 수용 기준을 명세화합니다.
---

[필수 입력 문서] @docs/00_context_management/context_packet.md, @docs/01_goals/10_goal_definition_final.md
[출력 산출물] docs/02_requirements/20_requirements_final.md

[System Directive]
확정된 시스템 목표와 컨텍스트 제약조건을 준수하여 구현 가능한 요구사항 명세서를 작성하라.

유스케이스(Use Case): 기본 흐름, 대안 흐름, 예외 흐름(예: 데이터 결측 시 처리)을 명세하라.

기능 요구사항(FR): 시계열 합성 데이터 생성기(41개 ADL 활동 모사), AttentionRNN 기반 예측 오차의 Z-score 산출 로직, 박스플롯 임계치 초과 시 LLM 자연어 설명문 생성 기능을 엄격히 명세하라.

비기능 요구사항(NFR): 추론 시간, 데이터 무결성 기준, 윤리적 제약(LLM 출력을 의료적 최종 진단이 아닌 보조 지표로 제한)을 계측 가능한 수치로 정의하라.

수용 기준(Acceptance Criteria): Given-When-Then 형식의 BDD 수용 기준을 작성하라.

상태 관리 의무: 신규 기능 요건 및 품질 속성을 전역 상태에 동기화하라.

DECISIONS.md: 도출된 코어 FR/NFR ID 목록 확정 기록.

ASSUMPTIONS.md: 요구사항 정제 과정에서 임의 전제한 비즈니스 로직 가설 적재.

context_packet.md: 수용 기준 요약본을 패킷에 바인딩하여 동적 갱신.