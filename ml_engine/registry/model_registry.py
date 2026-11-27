from typing import Dict, List, Any, Optional
from ml_engine.interfaces.base_model import BaseMultimodalModel
from ml_engine.models.stacking_ensemble import StackingEnsembleScreeningModel
from ml_engine.models.toddler_questionnaire_model import ToddlerQuestionnaireModel
from ml_engine.models.random_forest_model import RandomForestScreeningModel
from ml_engine.models.xgboost_model import XGBoostScreeningModel
from ml_engine.models.catboost_model import CatBoostScreeningModel
from ml_engine.config import TOTAL_FEATURE_DIM

class ModelRegistry:
    """
    Central registry for multimodal ASD screening algorithms.
    Provides decoupled discovery, status inspection, and dynamic instantiation.
    """

    _models: Dict[str, BaseMultimodalModel] = {}

    @classmethod
    def initialize(cls) -> None:
        """Instantiate available model interfaces."""
        if not cls._models:
            cls._models["toddler_qchat"] = ToddlerQuestionnaireModel()
            cls._models["stacking_ensemble"] = StackingEnsembleScreeningModel()
            cls._models["random_forest"] = RandomForestScreeningModel()
            cls._models["xgboost"] = XGBoostScreeningModel()
            cls._models["catboost"] = CatBoostScreeningModel()
            try:
                from ml_engine.models.pytorch_fusion_net import PyTorchFusionScreeningModel
                cls._models["pytorch_fusion"] = PyTorchFusionScreeningModel()
            except ImportError:
                pass

    @classmethod
    def get_model(cls, name: str = "stacking_ensemble") -> BaseMultimodalModel:
        cls.initialize()
        clean_name = name.lower().strip()
        if clean_name not in cls._models:
            clean_name = "stacking_ensemble"
        return cls._models[clean_name]

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        cls.initialize()
        results = []
        for key, model in cls._models.items():
            results.append(cls.get_model_status(key))
        return results

    @classmethod
    def get_model_status(cls, name: str) -> Dict[str, Any]:
        cls.initialize()
        model = cls.get_model(name)
        weights_path = str(getattr(model, "weights_path", ""))
        checkpoint_found = hasattr(model, "weights_path") and model.weights_path.exists()

        family_map = {
            "toddler_qchat": "Toddler Q-CHAT Stacking Ensemble (12-36 Months)",
            "stacking_ensemble": "Stacking Meta-Classifier (RF + SVM + GB -> LR)",
            "random_forest": "Scikit-Learn Ensemble",
            "xgboost": "Gradient Boosted Trees (XGBoost)",
            "catboost": "Categorical & Gradient Boosted Trees (CatBoost)",
            "pytorch_fusion": "Deep Multimodal Cross-Modal Fusion (PyTorch)"
        }

        desc_map = {
            "toddler_qchat": "Calibrated stacking ensemble specifically trained on Q-CHAT-10 toddler dataset (12-36 months) with external Polish clinical cohort validation.",
            "stacking_ensemble": "Two-tier stacking ensemble combining Random Forest, Support Vector Machine, and Gradient Boosting with Logistic Regression meta-classifier.",
            "random_forest": "Standardized bagging ensemble of orthogonal decision trees aggregating multimodal indicators.",
            "xgboost": "Second-order gradient boosted tree ensemble with regularized loss optimization.",
            "catboost": "Symmetric decision tree booster with robust handling of tabular feature interactions.",
            "pytorch_fusion": "PyTorch deep late-fusion neural network with modality sub-branches and cross-modal attention head."
        }

        status_msg = (
            "Calibrated & Verified Checkpoint Loaded" if model.is_calibrated
            else "Modular Integration Ready: Checkpoint unmounted. Running in uncalibrated research mode."
        )

        return {
            "model_name": model.name,
            "model_key": name,
            "model_family": family_map.get(name, "ML Screener"),
            "is_trained": model.is_trained,
            "is_calibrated": model.is_calibrated,
            "checkpoint_found": checkpoint_found,
            "weights_path": weights_path if checkpoint_found else None,
            "input_feature_dim": TOTAL_FEATURE_DIM,
            "architecture_description": desc_map.get(name, "Multimodal screening model"),
            "supported_explainers": ["SHAP", "LIME"],
            "status_message": status_msg
        }

