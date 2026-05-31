---
description: 분해된 개별 태스크를 에이전트가 코딩 중 환각 없이 완벽하게 단일 기능 구현을 수행할 수 있도록 유도하는 전용 상세 구현 지시서(Prompt)를 작성하는 스킬입니다.
---

[필수 입력 문서] @docs/04_tasks_and_prompts/07_task_breakdown.md, @docs/00_context_management/context_packet.md
[출력 산출물] docs/04_tasks_and_prompts/task_{ID}_prompt.md

[System Directive]
지정된 특정 Task ID에 대해 에이전트 코딩용 프롬프트 명세서를 작성하라.

맥락 격리: 해당 모듈이 수행해야 할 아키텍처적 목적, 입력 조건, 출력 형식, 수정 대상 파일 범위를 엄격하게 제한하라.

기술 스펙 주입: 입출력 파라미터 구조, 에러 처리 표준 규칙, 수용 기준(Acceptance Criteria)을 명시하라. 에이전트가 생각 없이 그대로 복사하여 실행 가능한 명령어 구조로 작성하라.

상태 관리 의무: 지시서 작성 과정에서 발생한 잔여 의문이나 임시 조치를 동기화하라.

OPEN_QUESTIONS.md: 외부 라이브러리 버전 제약 등 구현 전 확인 사항 추가.