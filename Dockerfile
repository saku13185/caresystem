# 1단계: 경량 공식 Python 3.12-slim 베이스 이미지 채택
FROM python:3.12-slim

# 2단계: 시스템 빌드 패키지 최소화 설치 및 디렉토리 생성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# 3단계: 애플리케이션 의존성 설치 (캐시 레이어 활성화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4단계: 소스코드 복사 및 환경변수 노출 설정
COPY src/ ./src/
COPY care_system.db .

# Streamlit 기본 구동 포트 노출 (8501)
EXPOSE 8501

# PYTHONPATH 환경변수 고정 설정 (의존성 모듈 탐색 경로 보장)
ENV PYTHONPATH=/app

# 5단계: 컨테이너 실행 보안 설정 (Non-root user 권장 정책 준수)
RUN useradd -m careuser && chown -r careuser:careuser /app
USER careuser

# 6단계: Streamlit 서버 실행 커맨드 지정 (다크 테마 기본 활성화 가이드 적용)
CMD ["streamlit", "run", "src/presentation/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
