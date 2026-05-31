import torch
import pytest
from src.infrastructure.models.attention_rnn import AttentionRNN

def test_attention_rnn_dimensions():
    """
    [BDD Scenario 2 검증]
    Given: 15일 슬라이딩 윈도우 데이터셋 (1, 15, 41) 준비 완료
    When: AttentionRNN 모델 입력 후 순방향 연산 수행
    Then: 16일 차 예측치 (1, 41) 및 Attention 가중치 (1, 15) 정상 출력 검증
    """
    # Given
    batch_size = 1
    window_size = 15
    features = 41
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 모델 정의 및 장치 업로드
    model = AttentionRNN(input_dim=features, hidden_dim=64).to(device)
    # 가상의 입력 시계열 텐서 생성
    dummy_input = torch.randn(batch_size, window_size, features).to(device)
    
    # When
    predictions, attention_weights = model(dummy_input)
    
    # Then
    # 41개 차원의 다음날 점유비 예측 형태 체크
    assert predictions.shape == (batch_size, features), f"Expected predictions shape {(batch_size, features)}, got {predictions.shape}"
    # 15일에 대한 가중 기여도 맵 형태 체크
    assert attention_weights.shape == (batch_size, window_size), f"Expected attention weights shape {(batch_size, window_size)}, got {attention_weights.shape}"
