import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import numpy as np

# Ensure root directory is on sys.path for ml_engine imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml_engine.registry.model_registry import ModelRegistry
from ml_engine.pipelines.multimodal_fusion import MultimodalFusionPipeline
from ml_engine.explainability.shap_engine import SHAPExplanationEngine
from ml_engine.explainability.lime_engine import LIMEExplanationEngine
from ml_engine.config import FEATURE_DEFINITIONS, FEATURE_NAMES

class MLBridge:
    """
    Decoupled adapter bridging FastAPI backend to the ML Engine subsystem.
    """

    _fusion_pipeline = MultimodalFusionPipeline()
    _shap_engine = SHAPExplanationEngine()
    _lime_engine = LIMEExplanationEngine()

    @classmethod
    def process_multimodal_inputs(
        cls,
        behavioral: Optional[Dict[str, Any]] = None,
        visual_gaze: Optional[Dict[str, Any]] = None,
        acoustic_prosody: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Dict[str, float]], List[str]]:
        """Extract and align multimodal feature vector."""
        return cls._fusion_pipeline.process_screening_inputs(
            behavioral_raw=behavioral,
            visual_raw=visual_gaze,
            audio_raw=acoustic_prosody
        )

    @classmethod
    def evaluate_screening(
        cls,
        feature_vector: np.ndarray,
        model_name: str = "stacking_ensemble",
        toddler_dict: Optional[Dict[str, Any]] = None,
        patient_age_months: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute prediction and explainability analysis with strict age gating:
        - Under 12 months: Suspends ML probability, returns OBSERVATION_ONLY_UNDER_12M
        - 12-36 months: Routes to toddler_qchat (Toddler Q-CHAT Stacking Ensemble)
        - Over 36 months: Standard childhood screening ensemble
        """
        # Age Gate: Under 12 months
        if patient_age_months is not None and patient_age_months < 12:
            from ml_engine.interfaces.base_model import ModelPredictionResult
            obs_pred = ModelPredictionResult(
                predicted_probability=None,
                is_calibrated=False,
                risk_tier="OBSERVATION_ONLY_UNDER_12M",
                confidence_interval={"lower": 0.0, "upper": 0.0},
                status_message="OBSERVATION_ONLY_UNDER_12M: Standard Q-CHAT-10 questionnaire is not clinically validated for infants under 12 months. Questionnaire screening risk probability is suspended; checklist observations recorded descriptively without diagnostic inference.",
                metadata={"age_months": patient_age_months, "policy": "OBSERVATION_ONLY_UNDER_12M"}
            )
            model_status = ModelRegistry.get_model_status("toddler_qchat")
            obs_shap = {
                "method": "SHAP",
                "base_value": 0.5,
                "prediction_value": None,
                "status": "OBSERVATION_ONLY_UNDER_12M",
                "feature_importances": [],
                "summary_narrative": "Screening is in observation-only mode for infants under 12 months. Statistical explainability is not applicable."
            }
            obs_lime = {
                "method": "LIME",
                "base_value": 0.5,
                "prediction_value": None,
                "status": "OBSERVATION_ONLY_UNDER_12M",
                "feature_importances": [],
                "summary_narrative": "Screening is in observation-only mode for infants under 12 months. Statistical explainability is not applicable."
            }
            return {
                "prediction": obs_pred,
                "model_status": model_status,
                "shap_explanation": obs_shap,
                "lime_explanation": obs_lime
            }

        # Q-CHAT models require explicit questionnaire answers and validated age.
        if model_name in ["toddler_qchat", "catboost", "random_forest", "lasso_logistic"]:
            from ml_engine.interfaces.base_model import ModelPredictionResult

            missing_age = patient_age_months is None
            age_out_of_range = (
                not missing_age and
                float(patient_age_months) > 36
            )
            required_answers = [f"A{i}" for i in range(1, 11)]
            missing_answers = (
                toddler_dict is None or
                any(toddler_dict.get(key) is None for key in required_answers)
            )

            if missing_age or age_out_of_range or missing_answers:
                if missing_age:
                    tier = "AGE_REQUIRED"
                    message = "Child age is required. No questionnaire score was generated."
                elif age_out_of_range:
                    tier = "OUTSIDE_VALIDATED_AGE_RANGE"
                    message = "This toddler questionnaire model is restricted to ages 12–36 months. No score was generated."
                else:
                    tier = "QUESTIONNAIRE_INCOMPLETE"
                    message = "All ten explicit Q-CHAT answers are required. Behavioural, visual and acoustic observations cannot replace questionnaire answers. No score was generated."

                prediction = ModelPredictionResult(
                    predicted_probability=None,
                    is_calibrated=False,
                    risk_tier=tier,
                    confidence_interval={"lower": 0.0, "upper": 0.0},
                    status_message=message,
                    metadata={"age_months": patient_age_months}
                )
                explanation = {
                    "method": "SHAP",
                    "base_value": 0.5,
                    "prediction_value": None,
                    "status": tier,
                    "feature_importances": [],
                    "summary_narrative": message
                }
                lime = {
                    "method": "LIME",
                    "base_value": 0.5,
                    "prediction_value": None,
                    "status": tier,
                    "feature_importances": [],
                    "summary_narrative": message
                }
                return {
                    "prediction": prediction,
                    "model_status": {
                        "key": model_name,
                        "name": model_name,
                        "family": "Research Machine Learning",
                        "checkpoint_found": False,
                        "is_trained": False,
                        "is_calibrated": False,
                        "status": tier
                    },
                    "shap_explanation": explanation,
                    "lime_explanation": lime
                }

        # Dedicated Toddler Model Handling
        if model_name in ["toddler_qchat", "catboost", "random_forest", "lasso_logistic"]:
            if model_name in ["catboost", "random_forest", "lasso_logistic"]:
                from ml_engine.prediction_service import ResearchPredictionService
                from ml_engine.interfaces.base_model import ModelPredictionResult
                pred_svc = ResearchPredictionService.get_instance()
                res = pred_svc.predict_child(assessment_data=toddler_dict or {}, model_name=model_name)
                
                prediction_result = ModelPredictionResult(
                    predicted_probability=res["predicted_probability"],
                    is_calibrated=res["is_calibrated"],
                    risk_tier=res["risk_tier"],
                    confidence_interval=res["confidence_interval"],
                    status_message=res["status_message"],
                    metadata={"threshold_applied": res.get("threshold_applied"), "model_used": res.get("model_used")}
                )
                model_status = {
                    "key": model_name,
                    "name": res.get("model_title", model_name),
                    "family": "Research Machine Learning",
                    "checkpoint_found": True,
                    "is_trained": True,
                    "is_calibrated": True,
                    "status": "CALIBRATED_ONLINE"
                }
                shap_explanation = dict(res["explanation"])
                shap_explanation["method"] = "SHAP"
                shap_explanation["is_calibrated"] = prediction_result.is_calibrated
                lime_explanation = {
                    "method": "LIME",
                    "base_value": shap_explanation.get("base_value", 0.5),
                    "prediction_value": prediction_result.predicted_probability,
                    "is_calibrated": prediction_result.is_calibrated,
                    "status": "EXPLAINABILITY_ACTIVE_CALIBRATED" if prediction_result.is_calibrated else "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED",
                    "feature_importances": shap_explanation.get("feature_importances", []),
                    "summary_narrative": shap_explanation.get("summary_narrative", "")
                }
                return {
                    "prediction": prediction_result,
                    "model_status": model_status,
                    "shap_explanation": shap_explanation,
                    "lime_explanation": lime_explanation
                }

            model = ModelRegistry.get_model("toddler_qchat")
            model_status = ModelRegistry.get_model_status("toddler_qchat")
            prediction_result = model.predict_toddler(toddler_dict)
            shap_explanation = model.explain_instance(toddler_dict)

            lime_explanation = {
                "method": "LIME",
                "base_value": shap_explanation.get("base_value", 0.31),
                "prediction_value": prediction_result.predicted_probability,
                "status": "EXPLAINABILITY_ACTIVE_CALIBRATED" if prediction_result.is_calibrated else "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED",
                "feature_importances": shap_explanation.get("feature_importances", []),
                "summary_narrative": shap_explanation.get("summary_narrative", "")
            }

            return {
                "prediction": prediction_result,
                "model_status": model_status,
                "shap_explanation": shap_explanation,
                "lime_explanation": lime_explanation
            }

        model = ModelRegistry.get_model(model_name)
        prediction_result = model.predict_risk(feature_vector)
        model_status = ModelRegistry.get_model_status(model_name)

        # Compute SHAP explanation (native stacking tree explainer if available)
        if hasattr(model, "explain_instance") and model.is_calibrated:
            shap_explanation = model.explain_instance(feature_vector, FEATURE_NAMES)
        else:
            shap_explanation = cls._shap_engine.explain_instance(
                model=model,
                feature_vector=feature_vector,
                feature_names=FEATURE_NAMES
            )

        # Compute LIME explanation
        lime_explanation = cls._lime_engine.explain_instance(
            model=model,
            feature_vector=feature_vector,
            feature_names=FEATURE_NAMES
        )

        return {
            "prediction": prediction_result,
            "model_status": model_status,
            "shap_explanation": shap_explanation,
            "lime_explanation": lime_explanation
        }

    @classmethod
    def get_registered_models(cls) -> List[Dict[str, Any]]:
        return ModelRegistry.list_models()

    @classmethod
    def get_feature_catalog(cls) -> List[Dict[str, Any]]:
        return FEATURE_DEFINITIONS

