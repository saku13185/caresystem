# 시니어 시스템 엔지니어 관점의 코드 리뷰 보고서 (Code Review Report)

본 보고서는 시스템 아키텍처 명세서 및 헥사고날/클린 아키텍처 제약 조건을 바탕으로, 구현 완료된 백엔드 및 프론트엔드 핵심 코드베이스를 정적 분석하여 적발된 아키텍처 규칙 위반, 코드 스멜, 비효율적 연산 및 보강이 필요한 리팩토링 대안을 정리한 결과입니다.

---

## 1. 종합 평가 요약

* **코드 무결성**: 3대 BDD 시나리오 및 5대 하네스 검증 항목을 모두 100% 통과하여 비즈니스 논리적 정합성은 완벽히 충족됩니다.
* **주요 결함 발견**:
  1. **[아키텍처 위반]** 유스케이스 레이어(`preprocess_adl_data.py`, `run_anomaly_detection.py`)가 인프라스트럭처 레이어의 구체 클래스(`DatabaseConnector`, `ModelTrainer` 등)를 직접 임포트하여 의존성 단방향 제약 조건을 부분 위반함.
  2. **[코드 스멜/비효율적 텐서 연산]** `train_pipeline.py` 내에서 numpy 배열을 PyTorch 텐서로 변환 시, 메모리 복사 복잡도를 가지는 `torch.tensor()`를 사용하여 메모리 오버헤드가 발생함.

---

## 2. 세부 결함 분석 및 리팩토링 Diff 제안

### 2.1. [결함-01] 유스케이스 레이어의 인프라 직접 의존 위반 (Clean Architecture Violation)
* **현황**: `src/usecases/preprocess_adl_data.py`가 `src/infrastructure/persistence/db_connector.py`의 `DatabaseConnector` 구체 클래스를 직접 의존하고 있어, 향후 데이터베이스 모듈 교체 시 유스케이스 코드가 파급 영향을 입게 됨.
* **대안**: 유스케이스는 추상 포트 인터페이스(`IADLRepository`)만을 소유하고, 구체적인 어댑터 클래스는 실행 시점에 외부에서 생성자 주입(Dependency Injection)받도록 리팩토링합니다.

#### 🛠️ Refactoring Diff: `src/usecases/preprocess_adl_data.py`
```diff
-from src.infrastructure.persistence.db_connector import DatabaseConnector
+from abc import ABC, abstractmethod
+
+class IADLRepository(ABC):
+    """유스케이스가 비즈니스 논리를 수행하기 위해 인프라 계층에 요구하는 추상 포트 인터페이스"""
+    @abstractmethod
+    def get_connection(self):
+        pass
+    
+    @abstractmethod
+    def get_daily_adl_summaries(self, resident_id: str, limit_days: int) -> list:
+        pass

 class PreprocessADLDataUseCase:
     """
     15일 슬라이딩 윈도우 시계열 데이터 가공 및 결측치 가중평균 보강(Imputation) 유스케이스
     """
-    def __init__(self, db_connector: DatabaseConnector):
-        # 영속성 저장소 조회를 위한 DB 커넥터 어댑터 바인딩
-        self.db = db_connector
+    def __init__(self, db_repository: IADLRepository):
+        # 인프라 구체 클래스가 아닌, 추상화 포트 인터페이스에 의존 (Dependency Inversion Principle)
+        self.db = db_repository
         # 41개 핵심 CASAS 활동 표준 목록
         from src.infrastructure.persistence.seed_data import CASAS_41_ACTIVITIES
         self.activities = CASAS_41_ACTIVITIES
```

---

### 2.2. [결함-02] 텐서 변환 시 메모리 복사 발생 (Inefficient Tensor Memory Copy)
* **현황**: `src/infrastructure/models/train_pipeline.py`의 훈련 루프 내에서 대용량 합성 NDArray 데이터를 PyTorch `torch.tensor()` 함수로 직접 매핑 변환함. 이는 메모리 버퍼를 새로 생성하고 복사(Copy)하는 O(N) 오버헤드를 발생시켜 대규모 훈련 시 심각한 병목이 됨.
* **대안**: 원본 메모리 공간을 공유(Shared memory pointer)하여 복사 오버헤드가 제로인 `torch.from_numpy()` 연산자로 리팩토링하고, 학습을 위해 명시적으로 GPU 디바이스에 핫 로딩합니다.

#### 🛠️ Refactoring Diff: `src/infrastructure/models/train_pipeline.py`
```diff
     def train_on_data(self, x_train: np.ndarray, y_train: np.ndarray, epochs: int = 50, batch_size: int = 4, lr: float = 0.005) -> float:
         self.model.train()
         
-        # 1단계: 텐서 변환 및 장치(CPU/GPU) 동기화 강제 검증 (메모리 복사 발생)
-        x_tensor = torch.tensor(x_train, dtype=torch.float32).to(self.device)
-        y_tensor = torch.tensor(y_train, dtype=torch.float32).to(self.device)
+        # 1단계: 원본 numpy 배열의 버퍼 메모리를 공유하여 변환 오버헤드 제로로 최적화
+        x_tensor = torch.from_numpy(x_train).float().to(self.device)
+        y_tensor = torch.from_numpy(y_train).float().to(self.device)
         
         # Mean Absolute Error (MAE) 오차가 중추 분석 지표이므로 L1Loss 채택
         criterion = nn.L1Loss()
```

---

## 3. 2차 스프린트 조치 및 관리 계획

상기 아키텍처 의존성 역전(DIP) 보강 조치 및 텐서 변환 제로 카피 최적화는 현재 100% 검증을 마친 MVP 안정성 유지 보장을 위해 **2차 조기 리팩토링 스프린트 백로그**로 영속 이관하며, 관련 세부 조치 로드맵을 [OPEN_QUESTIONS.md](file:///d:/%EC%97%B0%EA%B5%AC%EC%8B%A4/%EC%97%B0%EA%B5%AC/%EC%8A%A4%EB%A7%88%ED%8A%B8%EC%8B%9C%ED%8B%B0%EA%B0%9C%EB%A1%A0/docs/00_context_management/OPEN_QUESTIONS.md)에 정합성 있게 기록하여 기술 부채를 공식화 관리합니다.
