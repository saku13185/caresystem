import os
import pytest
import shutil
from unittest.mock import MagicMock
from src.infrastructure.persistence.db_connector import DatabaseConnector
from src.usecases.ports.care_repository import CareRepositoryPort
from src.usecases.run_anomaly_detection import RunAnomalyDetectionUseCase

def test_database_path_env_override(monkeypatch, tmp_path):
    """
    DATABASE_PATH 환경변수가 설정되어 있을 때, 해당 경로에 데이터베이스 디렉터리 및 파일이
    동적으로 생성되는지 검증합니다.
    """
    temp_db_dir = tmp_path / "subdir"
    temp_db_path = temp_db_dir / "temp_care_system.db"
    
    # 1. 환경 변수 주입
    monkeypatch.setenv("DATABASE_PATH", str(temp_db_path))
    
    # 2. 커넥터 인스턴스화 (경로 인자를 생략하여 환경변수를 참조하도록 유도)
    db = DatabaseConnector()
    
    # 3. 검증: 지정된 경로에 디렉터리 및 파일이 실제로 생성되었는지 단언
    assert os.path.exists(str(temp_db_path))
    assert db.db_path == str(temp_db_path)
    
    # 4. 정리
    db.get_connection().close()

def test_database_path_default_fallback(monkeypatch):
    """
    DATABASE_PATH 환경변수가 비어있을 때, 기본값인 'care_system.db'를 사용하는지 검증합니다.
    """
    # 1. 환경 변수 제거
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    
    # 2. 커넥터 인스턴스화
    db = DatabaseConnector()
    
    # 3. 검증
    assert db.db_path == "care_system.db"
    
    # 4. 정리
    db.get_connection().close()

def test_model_path_env_override(monkeypatch):
    """
    MODEL_PATH 환경변수가 설정되어 있을 때, RunAnomalyDetectionUseCase가 해당 경로를 사용하는지 검증합니다.
    """
    test_path = "models/custom_attention_rnn.pt"
    
    # 1. 환경 변수 주입
    monkeypatch.setenv("MODEL_PATH", test_path)
    
    # 2. 유스케이스 인스턴스화 (Mock repository 주입)
    mock_repo = MagicMock(spec=CareRepositoryPort)
    usecase = RunAnomalyDetectionUseCase(mock_repo)
    
    # 3. 검증
    assert usecase.model_path == test_path

def test_model_path_default_fallback(monkeypatch):
    """
    MODEL_PATH 환경변수가 비어있을 때, 기본값인 'attention_rnn.pt'를 사용하는지 검증합니다.
    """
    # 1. 환경 변수 제거
    monkeypatch.delenv("MODEL_PATH", raising=False)
    
    # 2. 유스케이스 인스턴스화 (Mock repository 주입)
    mock_repo = MagicMock(spec=CareRepositoryPort)
    usecase = RunAnomalyDetectionUseCase(mock_repo)
    
    # 3. 검증
    assert usecase.model_path == "attention_rnn.pt"
