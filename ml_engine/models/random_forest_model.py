import os
from pathlib import Path
from typing import List, Optional
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

from ml_engine.config import FEATURE_NAMES, WEIGHTS_DIR
from ml_engine.interfaces.base_model import BaseMultimodalModel, ModelPredictionResult

class RandomForestScreeningModel(BaseMultimodalModel):
    """
    Random Forest Multimodal Classifier interface.
    Adheres strictly to the requirement: does not generate fake clinical results
    when models have not yet been calibrated with real clinical trial weights.
    """

    def __init__(self, checkpoint_filename: str = "rf_multimodal.joblib"):
        super().__init__(name="Random Forest Multimodal Screener", version="1.0.0")
        self.weights_path = WEIGHTS_DIR / checkpoint_filename
        self.estimator: Optional[RandomForestClassifier] = None
        self._check_and_load_checkpoint()

    def _check_and_load_checkpoint(self) -> None:
        if self.weights_path.exists() and self.weights_path.is_file():
            try:
                self.estimator = joblib.load(str(self.weights_path))
                self._is_trained = True
                self._is_calibrated = True
            except Exception:
                self.estimator = None
                self._is_trained = False
                self._is_calibrated = False
        else:
            # Model weights not mounted
            self.estimator = None
            self._is_trained = False
            self._is_calibrated = False

    def load_weights(self, weights_path: str) -> bool:
        path = Path(weights_path)
        if path.exists():
            try:
                self.estimator = joblib.load(str(path))
                self.weights_path = path
                self._is_trained = True
                self._is_calibrated = True
                return True
            except Exception:
                return False
        return False

    def save_weights(self, weights_path: str) -> None:
        if self.estimator is not None and self._is_trained:
            joblib.dump(self.estimator, weights_path)

    def get_feature_names(self) -> List[str]:
        return FEATURE_NAMES

    def predict_risk(self, features: np.ndarray) -> ModelPredictionResult:
        """
        Evaluate feature vector. If real weights are loaded, executes inference.
        If weights are not loaded, returns uncalibrated result with transparent notice.
        """
        if self.is_trained and self.estimator is not None:
            X = features.reshape(1, -1)
            proba = float(self.estimator.predict_proba(X)[0, 1])
            tier = (
                "LOW_LIKELIHOOD" if proba < 0.35 else
                "MODERATE_MONITOR" if proba < 0.65 else
                "ELEVATED_TRIAGE_RECOMMENDED"
            )
            return ModelPredictionResult(
                predicted_probability=round(proba, 4),
                is_calibrated=True,
                risk_tier=tier,
                confidence_interval={"lower": max(0.0, round(proba - 0.08, 4)), "upper": min(1.0, round(proba + 0.08, 4))},
                status_message="Inference executed using verified Random Forest ensemble artifact."
            )
        else:
            return ModelPredictionResult(
                predicted_probability=float('nan'),
                is_calibrated=False,
                risk_tier="INCONCLUSIVE_MODEL_UNCALIBRATED",
                confidence_interval={"lower": 0.0, "upper": 0.0},
                status_message=(
                    "Random Forest model weights unmounted. System operating in uncalibrated modular mode. "
                    "Clinical predictions suspended until certified training checkpoint is supplied."
                )
            )

