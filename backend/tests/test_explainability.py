import sys
from pathlib import Path
import pytest
import numpy as np
from sklearn.ensemble import RandomForestClassifier

backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

from ml_engine.registry.model_registry import ModelRegistry
from ml_engine.explainability.shap_engine import SHAPExplanationEngine
from ml_engine.explainability.lime_engine import LIMEExplanationEngine
from ml_engine.models.random_forest_model import RandomForestScreeningModel
from ml_engine.config import TOTAL_FEATURE_DIM, FEATURE_NAMES

def test_explainability_untrained_suspension():
    """Verify that untrained/uncalibrated models strictly suspend SHAP and LIME and return empty importances."""
    model = RandomForestScreeningModel(checkpoint_filename="nonexistent_checkpoint.joblib")
    assert model.is_trained is False
    assert model.is_calibrated is False

    vec = np.ones(TOTAL_FEATURE_DIM, dtype=np.float32)

    shap_engine = SHAPExplanationEngine()
    shap_res = shap_engine.explain_instance(model, vec)

    assert shap_res["status"] == "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED"
    assert shap_res["feature_importances"] == []
    assert shap_res["is_calibrated"] is False
    assert "strictly suspended" in shap_res["calibration_status_notice"]
    assert shap_res["modality_breakdown"] == {"behavioral": 0.0, "visual_gaze": 0.0, "acoustic_prosody": 0.0}

    lime_engine = LIMEExplanationEngine()
    lime_res = lime_engine.explain_instance(model, vec)

    assert lime_res["status"] == "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED"
    assert lime_res["feature_importances"] == []
    assert lime_res["is_calibrated"] is False
    assert "suspended" in lime_res["calibration_status_notice"]

def test_explainability_trained_genuine_execution():
    """Verify that when a calibrated model is available, genuine SHAP and LIME explanations execute."""
    model = RandomForestScreeningModel()

    # Fit a genuine RandomForest on synthetic feature data for test verification
    np.random.seed(42)
    X_train = np.random.randn(40, TOTAL_FEATURE_DIM).astype(np.float32)
    y_train = np.random.choice([0, 1], size=40)
    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X_train, y_train)

    model.estimator = rf
    model._is_trained = True
    model._is_calibrated = True

    vec = X_train[0]

    # Test genuine SHAP execution
    shap_engine = SHAPExplanationEngine()
    shap_res = shap_engine.explain_instance(model, vec)

    assert shap_res["status"] == "EXPLAINABILITY_ACTIVE_CALIBRATED"
    assert shap_res["is_calibrated"] is True
    assert len(shap_res["feature_importances"]) == TOTAL_FEATURE_DIM
    assert isinstance(shap_res["base_value"], float)
    assert sum(shap_res["modality_breakdown"].values()) > 95.0 # Total ~100%

    # Test genuine LIME execution
    lime_engine = LIMEExplanationEngine()
    lime_res = lime_engine.explain_instance(model, vec)

    assert lime_res["status"] == "EXPLAINABILITY_ACTIVE_CALIBRATED"
    assert lime_res["is_calibrated"] is True
    assert len(lime_res["feature_importances"]) == TOTAL_FEATURE_DIM

