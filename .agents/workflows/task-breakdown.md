---
description: 설계된 아키텍처를 독립적으로 개발 및 검증 가능한 최소 백로그 단위(Task)로 분할하는 스킬입니다. 작업 간 Blocker 및 선후 의존 관계를 논리적으로 매핑합니다.
---

[필수 입력 문서] @docs/00_context_management/context_packet.md, @docs/03_design/05_architecture.md
[출력 산출물] docs/04_tasks_and_prompts/07_task_breakdown.md

[System Directive]
전체 아키텍처를 스프린트 백로그 수준의 세부 개발 작업으로 분해하라.

작업 세분화: 데이터 시뮬레이터(Task 1), 전처리 및 AttentionRNN(Task 2), Z-score 판단 및 LLM 연동(Task 3), 웹 대시보드(Task 4)로 명확히 분할하라.

의존성 맵: 각 작업의 Blocker 선후 관계와 병렬 작업 가능 여부를 매핑하여 마크다운 표(Table) 구조로 출력하라.

상태 관리 의무: 개발 스케줄링 리스크를 상태 관리에 동기화하라.

DECISIONS.md: 개발 시퀀스 및 스프린트 백로그 마일스톤 기록.

context_packet.md: Current Stage를 'Phase 4 - 작업 분해 완료'로 마킹하고 태스크 맵 요약본 주입.