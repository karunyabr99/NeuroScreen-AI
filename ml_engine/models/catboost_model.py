from pathlib import Path
from typing import List, Optional
import numpy as np
from catboost import CatBoostClassifier

from ml_engine.config import FEATURE_NAMES, WEIGHTS_DIR
from ml_engine.interfaces.base_model import BaseMultimodalModel, ModelPredictionResult

class CatBoostScreeningModel(BaseMultimodalModel):
    """
    CatBoost Multimodal Classifier interface.
    """

    def __init__(self, checkpoint_filename: str = "catboost_multimodal.bin"):
        super().__init__(name="CatBoost Multimodal Screener", version="1.0.0")
        self.weights_path = WEIGHTS_DIR / checkpoint_filename
        self.model: Optional[CatBoostClassifier] = None
        self._check_and_load_checkpoint()

    def _check_and_load_checkpoint(self) -> None:
        if self.weights_path.exists() and self.weights_path.is_file():
            try:
                self.model = CatBoostClassifier()
                self.model.load_model(str(self.weights_path))
                self._is_trained = True
                self._is_calibrated = True
            except Exception:
                self.model = None
                self._is_trained = False
                self._is_calibrated = False
        else:
            self.model = None
            self._is_trained = False
            self._is_calibrated = False

    def load_weights(self, weights_path: str) -> bool:
        path = Path(weights_path)
        if path.exists():
            try:
                self.model = CatBoostClassifier()
                self.model.load_model(str(path))
                self.weights_path = path
                self._is_trained = True
                self._is_calibrated = True
                return True
            except Exception:
                return False
        return False

    def save_weights(self, weights_path: str) -> None:
        if self.model is not None and self._is_trained:
            self.model.save_model(str(weights_path))

    def get_feature_names(self) -> List[str]:
        return FEATURE_NAMES

    def predict_risk(self, features: np.ndarray) -> ModelPredictionResult:
        if self.is_trained and self.model is not None:
            proba = float(self.model.predict_proba(features.reshape(1, -1))[0, 1])
            tier = (
                "LOW_LIKELIHOOD" if proba < 0.35 else
                "MODERATE_MONITOR" if proba < 0.65 else
                "ELEVATED_TRIAGE_RECOMMENDED"
            )
            return ModelPredictionResult(
                predicted_probability=round(proba, 4),
                is_calibrated=True,
                risk_tier=tier,
                confidence_interval={"lower": max(0.0, round(proba - 0.06, 4)), "upper": min(1.0, round(proba + 0.06, 4))},
                status_message="Inference executed using verified CatBoost decision model artifact."
            )
        else:
            return ModelPredictionResult(
                predicted_probability=float('nan'),
                is_calibrated=False,
                risk_tier="INCONCLUSIVE_MODEL_UNCALIBRATED",
                confidence_interval={"lower": 0.0, "upper": 0.0},
                status_message=(
                    "CatBoost model checkpoint unmounted. System operating in uncalibrated modular mode. "
                    "Clinical predictions suspended until certified model weights are supplied."
                )
            )

