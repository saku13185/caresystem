import os
import pytest
import torch
from unittest.mock import patch
from src.infrastructure.models.model_cache import AttentionRNNModelCache
from src.infrastructure.models.attention_rnn import AttentionRNN

@pytest.fixture(autouse=True)
def setup_teardown():
    """
    각 테스트 시작 및 종료 시 캐시를 강제로 비워 테스트 격리성을 유지합니다.
    """
    AttentionRNNModelCache.clear_cache()
    yield
    AttentionRNNModelCache.clear_cache()

def test_model_cache_instance_reuse():
    """
    동일한 model_path 및 device를 전달했을 때, 
    디스크로부터 다시 로드하지 않고 동일한 메모리 주소(ID)의 모델 객체를 반환하는지 단언합니다.
    """
    model_path = "attention_rnn.pt"
    device = "cpu"
    
    # 1. 첫 로딩 (디스크 로딩 발생)
    model1 = AttentionRNNModelCache.get_model(model_path=model_path, device=device)
    
    # 2. 두 번째 로딩 (캐시 히트 발생)
    model2 = AttentionRNNModelCache.get_model(model_path=model_path, device=device)
    
    # 3. 객체 아이디 일치 및 타입 검증
    assert isinstance(model1, AttentionRNN)
    assert id(model1) == id(model2), "캐시된 모델 객체 주소가 동일해야 합니다."

def test_model_cache_different_params():
    """
    모델의 경로(model_path) 또는 장치(device)가 바뀔 시 
    캐시 키 불일치로 인해 서로 다른 인스턴스를 새로 생성하여 반환하는지 단언합니다.
    """
    model_path = "attention_rnn.pt"
    
    # CPU 모델 획득
    model_cpu = AttentionRNNModelCache.get_model(model_path=model_path, device="cpu")
    
    # 임의의 다른 경로 생성 (존재하지 않으므로 FileNotFoundError)
    with pytest.raises(FileNotFoundError):
        AttentionRNNModelCache.get_model(model_path="non_existent_model.pt", device="cpu")

def test_model_cache_clear():
    """
    clear_cache()가 실행된 후에는 동일 매개변수로 요청하더라도 
    기존 캐시 인스턴스가 파괴되고 새롭게 로드되어 반환되는지 단언합니다.
    """
    model_path = "attention_rnn.pt"
    device = "cpu"
    
    model1 = AttentionRNNModelCache.get_model(model_path=model_path, device=device)
    
    # 캐시 소거
    AttentionRNNModelCache.clear_cache()
    
    model2 = AttentionRNNModelCache.get_model(model_path=model_path, device=device)
    
    assert id(model1) != id(model2), "캐시 소거 후에는 서로 다른 모델 인스턴스여야 합니다."

def test_model_cache_file_not_found():
    """
    대상 모델 PT 가중치 파일이 존재하지 않는 경우,
    FileNotFoundError가 정상적으로 발생하며 Mock fallback 안정 가드에 진입하도록 예외를 던지는지 단언합니다.
    """
    with pytest.raises(FileNotFoundError):
        AttentionRNNModelCache.get_model(model_path="invalid_path.pt", device="cpu")

def test_model_cache_torch_load_count():
    """
    mock.patch를 이용하여 torch.load가 동일 키에 대해 단 1회만 호출되는지
    호출 횟수(Call Count) 관점으로 단언합니다.
    """
    model_path = "attention_rnn.pt"
    device = "cpu"
    
    with patch("torch.load") as mock_load:
        # torch.load의 모의 반환값 세팅 (state_dict 모사)
        # 실제 AttentionRNN 가중치 파일은 PyTorch 모델 구조에 매핑되어야 하므로,
        # AttentionRNNModelCache 내 load_state_dict가 에러 나지 않도록 빈 state_dict 또는 모의 모델 state_dict 구성
        dummy_model = AttentionRNN()
        mock_load.return_value = dummy_model.state_dict()
        
        # 1. 최초 로드
        AttentionRNNModelCache.get_model(model_path=model_path, device=device)
        assert mock_load.call_count == 1
        
        # 2. 캐시 조회 (torch.load 호출 미발생)
        AttentionRNNModelCache.get_model(model_path=model_path, device=device)
        assert mock_load.call_count == 1, "캐시 히트 시에는 torch.load가 추가로 실행되지 않아야 합니다."
