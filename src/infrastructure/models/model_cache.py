import os
import torch
import threading
from typing import Dict, Tuple, Optional
from src.infrastructure.models.attention_rnn import AttentionRNN

class AttentionRNNModelCache:
    """
    AttentionRNN 모델 인스턴스를 (model_path, device) 키 조합으로 인메모리 캐싱하여
    반복적인 디스크 I/O 및 torch.load 오버헤드를 방지하는 스레드 세이프 싱글톤 캐시 클래스.
    """
    _lock = threading.Lock()
    _cache: Dict[Tuple[str, str], AttentionRNN] = {}

    @classmethod
    def get_model(cls, model_path: Optional[str] = None, device: str = "cpu") -> AttentionRNN:
        """
        주어진 경로와 장치(device)에 알맞은 캐시된 모델을 반환합니다.
        캐시 히트가 발생하지 않으면 디스크에서 새로 로드하여 캐시합니다.
        """
        # 1. 모델 경로 해결 (환경변수 MODEL_PATH 우선 적용)
        resolved_path = model_path or os.environ.get("MODEL_PATH", "attention_rnn.pt")
        cache_key = (resolved_path, device)

        with cls._lock:
            # 2. 캐시 히트 검사
            if cache_key in cls._cache:
                print(f"[AttentionRNNModelCache] Reusing cached AttentionRNN model for key: {cache_key}")
                return cls._cache[cache_key]

            # 3. 모델 파일 존재 유무 체크
            if not os.path.exists(resolved_path):
                raise FileNotFoundError(f"Model file not found at: {resolved_path}")

            # 4. 디스크로부터 가중치 최초 로딩
            print(f"[AttentionRNNModelCache] Loading model from disk: {resolved_path} ({device})")
            
            # 모델 생성 및 CPU/GPU 디바이스 매핑
            model = AttentionRNN()
            model.load_state_dict(torch.load(resolved_path, map_location=torch.device(device)))
            
            # 모델을 평가 모드(eval)로 고정
            model.eval()
            
            # 5. 캐시에 보관
            cls._cache[cache_key] = model
            return model

    @classmethod
    def clear_cache(cls):
        """
        테스트 환경 초기화 및 가중치 업데이트 시 전체 캐시 딕셔너리를 소거합니다.
        """
        with cls._lock:
            cls._cache.clear()
            print("[AttentionRNNModelCache] Cache cleared.")
