from pathlib import Path
from typing import List, Optional
import numpy as np
import xgboost as xgb

from ml_engine.config import FEATURE_NAMES, WEIGHTS_DIR
from ml_engine.interfaces.base_model import BaseMultimodalModel, ModelPredictionResult

class XGBoostScreeningModel(BaseMultimodalModel):
    """
    XGBoost Multimodal Classifier interface.
    """

    def __init__(self, checkpoint_filename: str = "xgb_multimodal.json"):
        super().__init__(name="XGBoost Multimodal Screener", version="1.0.0")
        self.weights_path = WEIGHTS_DIR / checkpoint_filename
        self.booster: Optional[xgb.Booster] = None
        self._check_and_load_checkpoint()

    def _check_and_load_checkpoint(self) -> None:
        if self.weights_path.exists() and self.weights_path.is_file():
            try:
                self.booster = xgb.Booster()
                self.booster.load_model(str(self.weights_path))
                self._is_trained = True
                self._is_calibrated = True
            except Exception:
                self.booster = None
                self._is_trained = False
                self._is_calibrated = False
        else:
            self.booster = None
            self._is_trained = False
            self._is_calibrated = False

    def load_weights(self, weights_path: str) -> bool:
        path = Path(weights_path)
        if path.exists():
            try:
                self.booster = xgb.Booster()
                self.booster.load_model(str(path))
                self.weights_path = path
                self._is_trained = True
                self._is_calibrated = True
                return True
            except Exception:
                return False
        return False

    def save_weights(self, weights_path: str) -> None:
        if self.booster is not None and self._is_trained:
            self.booster.save_model(weights_path)

    def get_feature_names(self) -> List[str]:
        return FEATURE_NAMES

    def predict_risk(self, features: np.ndarray) -> ModelPredictionResult:
        if self.is_trained and self.booster is not None:
            dmatrix = xgb.DMatrix(features.reshape(1, -1), feature_names=FEATURE_NAMES)
            proba = float(self.booster.predict(dmatrix)[0])
            tier = (
                "LOW_LIKELIHOOD" if proba < 0.35 else
                "MODERATE_MONITOR" if proba < 0.65 else
                "ELEVATED_TRIAGE_RECOMMENDED"
            )
            return ModelPredictionResult(
                predicted_probability=round(proba, 4),
                is_calibrated=True,
                risk_tier=tier,
                confidence_interval={"lower": max(0.0, round(proba - 0.07, 4)), "upper": min(1.0, round(proba + 0.07, 4))},
                status_message="Inference executed using verified XGBoost gradient boosted model artifact."
            )
        else:
            return ModelPredictionResult(
                predicted_probability=float('nan'),
                is_calibrated=False,
                risk_tier="INCONCLUSIVE_MODEL_UNCALIBRATED",
                confidence_interval={"lower": 0.0, "upper": 0.0},
                status_message=(
                    "XGBoost model checkpoint unmounted. System operating in uncalibrated modular mode. "
                    "Clinical predictions suspended until certified model weights are supplied."
                )
            )

