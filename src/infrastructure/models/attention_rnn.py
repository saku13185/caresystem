import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

class AttentionRNN(nn.Module):
    """
    15일 슬라이딩 윈도우 기반 다음 날(16일 차) 41개 ADL 점유비를 예측하고
    각 날짜의 중요도를 추출하는 Self-Attention GRU 신경망 아키텍처
    """
    def __init__(self, input_dim: int = 41, hidden_dim: int = 64, output_dim: int = 41):
        super(AttentionRNN, self).__init__()
        self.hidden_dim = hidden_dim
        
        # 1단계: 순방향 GRU 레이어 정의 (시점 데이터 흐름 포착)
        # 입력 차원: 41 (활동 수), 은닉 상태 차원: 64
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        
        # 2단계: Self-Attention 연산용 피드포워드 레이어 정의
        # 각 시간 스텝의 은닉 상태(hidden state)를 스칼라 스코어로 변환
        self.attention_fc = nn.Linear(hidden_dim, 1)
        
        # 3단계: 최종 점유율 예측 출력을 위한 선형 투영 레이어 정의
        # 어텐션 가중합이 적용된 컨텍스트 벡터(64차원)를 최종 예측 차원(41차원)으로 매핑
        self.output_fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        순방향 추론 루틴
        입력: x (Batch, 15, 41)
        반환: (Batch, 41) 크기의 16일 차 예측치 및 (Batch, 15) 크기의 Attention 가중치
        """
        # GRU 구동 -> 모든 시간 스텝의 은닉 상태 출력 획득
        # rnn_out 형상: (Batch, 15, 64)
        rnn_out, _ = self.gru(x)
        
        # 각 시간 스텝의 은닉 상태에 대해 어텐션 스코어 연산
        # scores 형상: (Batch, 15, 1)
        scores = self.attention_fc(rnn_out)
        
        # 15일 타임스텝 방향으로 Softmax를 수행하여 확률 분포(가중치)로 변환
        # attention_weights 형상: (Batch, 15, 1)
        attention_weights = F.softmax(scores, dim=1)
        
        # 각 은닉 상태 벡터에 어텐션 가중치를 곱하고 합산하여 단일 컨텍스트 벡터 획득
        # context_vector 형상: (Batch, 64)
        context_vector = torch.sum(rnn_out * attention_weights, dim=1)
        
        # 최종 41개 점유비 예측 수행
        # predictions 형상: (Batch, 41)
        predictions = self.output_fc(context_vector)
        
        # 어텐션 맵 시각화를 위해 가중치 벡터 차원 축소 (Batch, 15)
        flat_attention_weights = attention_weights.squeeze(2)
        
        return predictions, flat_attention_weights
