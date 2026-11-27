from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np

@dataclass
class ModelPredictionResult:
    predicted_probability: float # Risk probability between 0.0 and 1.0 (or NaN if uncalibrated)
    is_calibrated: bool
    risk_tier: str
    confidence_interval: Dict[str, float] = field(default_factory=lambda: {"lower": 0.0, "upper": 0.0})
    raw_logits: Optional[List[float]] = None
    status_message: str = "Model loaded"
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseMultimodalModel(ABC):
    """
    Abstract Base Class for all screening-support models.
    Supports Scikit-Learn, CatBoost, XGBoost, and PyTorch deep models.
    Enforces strict calibration & training status contracts.
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._is_trained = False
        self._is_calibrated = False

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def is_calibrated(self) -> bool:
        return self._is_calibrated

    @abstractmethod
    def load_weights(self, weights_path: str) -> bool:
        """Attempt to load trained weight artifact. Returns True if successful."""
        pass

    @abstractmethod
    def save_weights(self, weights_path: str) -> None:
        """Persist model checkpoint to disk."""
        pass

    @abstractmethod
    def predict_risk(self, features: np.ndarray) -> ModelPredictionResult:
        """
        Evaluate multimodal feature vector (1D array of length TOTAL_FEATURE_DIM).
        If uncalibrated / untrained, returns structured uncalibrated result
        WITHOUT generating fake clinical results.
        """
        pass

    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """Returns ordered list of feature identifiers expected by this model."""
        pass

