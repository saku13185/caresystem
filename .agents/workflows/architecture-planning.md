---
description: 시스템의 모듈 경계, 데이터 흐름, 컴포넌트 간 상호작용 및 디렉토리 구조를 구조화하는 아키텍처 설계 스킬입니다. 레이어 간 의존성 방향을 설정합니다.
---

[필수 입력 문서] @docs/03_design/04_domain_model.md, @docs/00_context_management/context_packet.md
[출력 산출물] docs/03_design/05_architecture.md

[System Directive]
도메인 모델과 비기능 요구사항을 만족하는 청정 아키텍처(Clean/Hexagonal Architecture)를 설계하라.

서브시스템 분리: Simulator, DataPreprocessor, AIEngine(AttentionRNN 및 Statistical Scorer), LLMAgent, Dashboard 간의 경계와 I/O 프로토콜을 정의하라.

파이프라인 시각화: 데이터 수집부터 자연어 리포트 출력까지의 흐름을 Mermaid 시퀀스 다이어그램으로 작성하라. 폴더 트리 구조를 명시하라.

상태 관리 의무: 아키텍처 제약 조건을 전역 컨텍스트에 동기화하라.

DECISIONS.md: 아키텍처 패턴 유형, 계층 간 의존성 규칙, 외부 API 연동 방식 기록.

OPEN_QUESTIONS.md: 시계열 윈도우(15일) 버퍼 관리 방식 등 설계 상 발생한 기술 부채 적재.

context_packet.md: 아키텍처 가이드라인을 제약조건 항목에 주입하여 최신화.