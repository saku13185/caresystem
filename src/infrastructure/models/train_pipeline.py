import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from typing import Tuple
from src.infrastructure.models.attention_rnn import AttentionRNN

class ModelTrainer:
    """
    AttentionRNN 모델 학습 및 학습된 가중치(.pt) 영속 저장 파이프라인
    """
    def __init__(self, model_save_path: str = "attention_rnn.pt"):
        self.model_save_path = model_save_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AttentionRNN().to(self.device)

    def train_on_data(self, x_train: np.ndarray, y_train: np.ndarray, epochs: int = 50, batch_size: int = 4, lr: float = 0.005) -> float:
        """
        넘파이 데이터셋을 받아 PyTorch 모델을 학습시키고 손실값을 반환합니다.
        x_train 형상: (NumSamples, 15, 41)
        y_train 형상: (NumSamples, 41)
        """
        self.model.train()
        
        # 1단계: 텐서 변환 및 장치(CPU/GPU) 동기화 강제 검증
        x_tensor = torch.tensor(x_train, dtype=torch.float32).to(self.device)
        y_tensor = torch.tensor(y_train, dtype=torch.float32).to(self.device)
        
        # Mean Absolute Error (MAE) 오차가 중추 분석 지표이므로 L1Loss 채택
        criterion = nn.L1Loss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        
        dataset_size = x_train.shape[0]
        final_loss = 0.0
        
        # 2단계: 배치 단위 훈련 루프 실행
        for epoch in range(epochs):
            indices = np.arange(dataset_size)
            np.random.shuffle(indices)
            
            epoch_loss = 0.0
            num_batches = int(np.ceil(dataset_size / batch_size))
            
            for b in range(num_batches):
                batch_idx = indices[b * batch_size : (b + 1) * batch_size]
                if len(batch_idx) == 0:
                    continue
                    
                x_batch = x_tensor[batch_idx]
                y_batch = y_tensor[batch_idx]
                
                optimizer.zero_grad()
                predictions, _ = self.model(x_batch)
                
                loss = criterion(predictions, y_batch)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                
            final_loss = epoch_loss / num_batches
            
        # 3단계: 학습 완료된 모델 파라미터를 영속성 .pt 파일로 안전 저장
        torch.save(self.model.state_dict(), self.model_save_path)
        return final_loss

    def load_model(self) -> None:
        """
        저장된 가중치를 핫 로딩하여 추론 준비 상태로 세팅합니다.
        """
        if os.path.exists(self.model_save_path):
            self.model.load_state_dict(torch.load(self.model_save_path, map_location=self.device))
            self.model.eval()
        else:
            raise FileNotFoundError(f"모델 가중치 파일 {self.model_save_path}이(가) 존재하지 않습니다.")
            
    def predict(self, x_input: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        15일치 ADL 입력을 받아 16일 차 예측치 및 Attention 가중치를 추론합니다.
        입력: x_input (Batch, 15, 41)
        """
        self.model.eval()
        with torch.no_grad():
            x_tensor = torch.tensor(x_input, dtype=torch.float32).to(self.device)
            predictions, attention_weights = self.model(x_tensor)
            
            # 장치 락 해제 및 넘파이 배열 변환
            return predictions.cpu().numpy(), attention_weights.cpu().numpy()
