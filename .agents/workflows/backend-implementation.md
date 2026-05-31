---
description: 구현 지시서를 기반으로 가상 ADL 데이터 생성기, AttentionRNN 시계열 예측 엔진, Z-score 분류 파이프라인 및 에러 로깅을 포함한 백엔드 코드를 구현하는 스킬입니다.
---

[필수 입력 문서] @docs/04_tasks_and_prompts/task_{ID}_prompt.md (백엔드 작업)
[출력 산출물] src/ 하위 소스코드 파일 생성 및 수정

[System Directive]
백엔드 엔지니어로서 제공된 작업 지시서를 바탕으로 서버 로직을 구현하라.

핵심 연산 구현: src/data_simulator.py에 41개 활동 정상/이상 패턴 합성 스크립트를, src/attention_rnn.py에 15일 윈도우 기반 다음날 예측 PyTorch 모델 및 Z-score 계산 수식을 수학적 무결성을 담아 구현하라.

안정성 확보: 예외 상황에 대비한 표준 Try-Catch 프레임워크 및 파이프라인 로깅 코드를 강제 탑재하라.

상태 관리 의무: 구현 도중 발생한 예외적인 예외 코드나 타협점을 동기화하라.

DECISIONS.md: 핵심 하이퍼파라미터 및 손실 함수 규격 명세 추가 기록.

OPEN_QUESTIONS.md: 리팩토링이 필요한 코드 스멜이나 기술 부채 등록.