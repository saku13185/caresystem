---
description: 요구사항을 충족하기 위한 시스템 내 핵심 비즈니스 객체와 도메인 용어 사전(Ubiquitous Language)을 정립하는 스킬입니다. 물리 스키마 진입 전 비즈니스 개념 모델을 수립합니다.
---

[필수 입력 문서] @docs/00_context_management/context_packet.md, @docs/02_requirements/20_requirements_final.md
[출력 산출물] docs/03_design/04_domain_model.md

[System Directive]
요구사항을 바탕으로 도메인 주도 설계(DDD) 기반의 개념적 도메인 모델을 수립하라.

개념 도출: 시스템을 구성하는 핵심 엔터티(Resident, SensorEvent, DailyADLSummary, AnomalyReport, CaregiverAlert) 및 애그리거트 루트를 식별하라.

비즈니스 제약: 각 엔터티 간의 연관 관계(1:N, N:M)와 생명주기 의존성, 속성 구조를 명세하라. 특정 벤더의 DB 기술에 종속된 물리적 컬럼 스펙은 작성하지 마라.

상태 관리 의무: 도메인 개념 확정안을 전역 상태에 연동하라.

DECISIONS.md: 도메인 애그리거트 경계 및 비즈니스 용어 확정 기록.

context_packet.md: Mermaid 기반의 도메인 모델 다이어그램을 패킷에 갱신 주입.