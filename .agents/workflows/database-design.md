---
description: 도메인 모델과 아키텍처에 정의된 데이터 흐름을 충족하기 위한 물리적 데이터베이스 스키마를 설계하는 스킬입니다. 무결성 제약조건과 데이터 보존 정책을 정의합니다.
---

[필수 입력 문서] @docs/03_design/05_architecture.md
[출력 산출물] docs/03_design/database_schema.md

[System Directive]
물리적 스키마 전략을 설계하라.

릴레이션 명세: CASAS 가상 원시 로그 테이블 및 일별 전처리 요약(ADL Dedication %) 테이블의 스펙(컬럼명, 데이터 타입, NULL 여부, PK/FK 제약)을 정의하라.

최적화: 조회 성능 개선을 위한 인덱스(Index) 배치 전략을 수립하라. 전체 스키마 구조를 Mermaid erDiagram으로 시각화하라.

상태 관리 의무: 스키마 확정안을 컨텍스트에 동기화하라.

DECISIONS.md: 시계열 데이터 저장 구조 및 보존/삭제 정책 기록.

context_packet.md: 물리 데이터 스펙 요약본을 패킷에 반영.