"""
NeuroScreen AI - Top-level Model Registry
Exposes available research models, baseline models, and interfaces.
"""

from typing import Dict, Any, List
from ml_engine.registry.model_registry import ModelRegistry as CoreModelRegistry
from ml_engine.prediction_service import ResearchPredictionService


class ResearchModelRegistry:
    """
    Unified discovery and metadata provider for research models (Paper 1 & Paper 2).
    """

    @classmethod
    def list_available_models(cls) -> List[Dict[str, Any]]:
        pred_service = ResearchPredictionService.get_instance()
        meta = pred_service.metadata

        models_list = [
            {
                "key": "catboost",
                "name": "CatBoost (Paper 1, 2024)",
                "family": "Gradient Boosting (CatBoost)",
                "paper": "Paper 1 (2024): Well-Baby Electronic Data",
                "is_trained": pred_service.is_model_ready("catboost"),
                "is_primary": True,
                "youden_threshold": meta.get("catboost", {}).get("youden_threshold", 0.5),
                "cv_roc_auc": meta.get("catboost", {}).get("cv_evaluation", {}).get("mean_roc_auc"),
                "test_roc_auc": meta.get("catboost", {}).get("test_evaluation_youden_threshold", {}).get("roc_auc"),
                "test_sensitivity": meta.get("catboost", {}).get("test_evaluation_youden_threshold", {}).get("sensitivity"),
                "test_specificity": meta.get("catboost", {}).get("test_evaluation_youden_threshold", {}).get("specificity")
            },
            {
                "key": "random_forest",
                "name": "Random Forest (Paper 2, 2022)",
                "family": "Decision Tree Ensemble",
                "paper": "Paper 2 (2022): Medical Claims Data",
                "is_trained": pred_service.is_model_ready("random_forest"),
                "is_primary": False,
                "cv_roc_auc": meta.get("random_forest", {}).get("cv_evaluation", {}).get("mean_roc_auc"),
                "test_roc_auc": meta.get("random_forest", {}).get("test_evaluation", {}).get("roc_auc"),
                "test_auprc": meta.get("random_forest", {}).get("test_evaluation", {}).get("auprc"),
                "test_f1": meta.get("random_forest", {}).get("test_evaluation", {}).get("f1_score")
            },
            {
                "key": "lasso_logistic",
                "name": "LASSO Logistic Regression (Paper 2, 2022)",
                "family": "L1 Regularized Linear Model",
                "paper": "Paper 2 (2022): Medical Claims Data",
                "is_trained": pred_service.is_model_ready("lasso_logistic"),
                "is_primary": False,
                "selected_features_count": meta.get("lasso_logistic", {}).get("lasso_selected_features_count"),
                "cv_roc_auc": meta.get("lasso_logistic", {}).get("cv_evaluation", {}).get("mean_roc_auc"),
                "test_roc_auc": meta.get("lasso_logistic", {}).get("test_evaluation", {}).get("roc_auc"),
                "test_auprc": meta.get("lasso_logistic", {}).get("test_evaluation", {}).get("auprc"),
                "test_f1": meta.get("lasso_logistic", {}).get("test_evaluation", {}).get("f1_score")
            }
        ]
        return models_list

