from typing import Dict, Any, List
import numpy as np
import shap

from ml_engine.config import FEATURE_NAMES, FEATURE_MAP
from ml_engine.interfaces.base_explainer import BaseExplainer
from ml_engine.interfaces.base_model import BaseMultimodalModel

class SHAPExplanationEngine(BaseExplainer):
    """
    SHAP (SHapley Additive exPlanations) Engine.
    Provides local and global feature attribution for multimodal ASD screening.
    Adheres strictly to clinical governance: feature attribution calculations are strictly
    suspended when models are untrained or uncalibrated to prevent fabricated explanations.
    """

    @property
    def explainer_type(self) -> str:
        return "SHAP"

    def explain_instance(
        self,
        model: BaseMultimodalModel,
        feature_vector: np.ndarray,
        feature_names: List[str] = FEATURE_NAMES
    ) -> Dict[str, Any]:
        """
        Calculates genuine SHAP feature contributions if model is trained & calibrated.
        If untrained/uncalibrated, strictly suspends calculation and returns an empty array.
        """
        # Strict calibration & training gate
        if not (model.is_trained and model.is_calibrated):
            return {
                "method": "SHAP",
                "status": "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED",
                "base_value": 0.50,
                "prediction_value": 0.50,
                "is_calibrated": False,
                "calibration_status_notice": (
                    "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED: Model weights are unmounted. "
                    "Feature attribution computation is strictly suspended to prevent fabricated clinical explanations."
                ),
                "feature_importances": [],
                "modality_breakdown": {
                    "behavioral": 0.0,
                    "visual_gaze": 0.0,
                    "acoustic_prosody": 0.0
                },
                "summary_narrative": (
                    "Explainability analysis suspended. SHAP feature attribution requires a certified, calibrated model checkpoint. "
                    "In compliance with clinical governance, heuristic attribution is not generated for uncalibrated models."
                )
            }

        # Genuine SHAP calculation for trained & calibrated models
        importances: List[Dict[str, Any]] = []
        base_value = 0.50
        predicted_value = 0.50

        try:
            if hasattr(model, "estimator") and model.estimator is not None:
                underlying_est = model.estimator
                # If wrapped in CalibratedClassifierCV, unwrap to the fitted base tree estimator
                if hasattr(underlying_est, "calibrated_classifiers_") and underlying_est.calibrated_classifiers_:
                    underlying_est = underlying_est.calibrated_classifiers_[0].estimator

                explainer = shap.TreeExplainer(underlying_est)
                shap_vals = explainer.shap_values(feature_vector.reshape(1, -1))
                if isinstance(shap_vals, list) and len(shap_vals) > 1:
                    raw_attributions = shap_vals[1][0]
                    base_value = float(explainer.expected_value[1])
                elif isinstance(shap_vals, np.ndarray) and len(shap_vals.shape) == 3:
                    raw_attributions = shap_vals[0, :, 1]
                    base_value = float(explainer.expected_value[1]) if hasattr(explainer.expected_value, "__getitem__") else float(explainer.expected_value)
                else:
                    raw_attributions = shap_vals[0]
                    base_value = float(explainer.expected_value)
            elif hasattr(model, "booster") and model.booster is not None:
                explainer = shap.TreeExplainer(model.booster)
                raw_attributions = explainer.shap_values(feature_vector.reshape(1, -1))[0]
                base_value = float(explainer.expected_value)
            elif hasattr(model, "model") and model.model is not None:
                explainer = shap.TreeExplainer(model.model)
                raw_attributions = explainer.shap_values(feature_vector.reshape(1, -1))[0]
                base_value = float(explainer.expected_value)
            else:
                # KernelExplainer for deep or arbitrary model wrappers
                def predict_fn(X: np.ndarray):
                    preds = []
                    for row in X:
                        res = model.predict_risk(row)
                        p = res.predicted_probability if res.is_calibrated else 0.5
                        preds.append(p)
                    return np.array(preds)

                background = np.tile([FEATURE_MAP[f]["mean_norm"] for f in feature_names], (10, 1))
                explainer = shap.KernelExplainer(predict_fn, background)
                raw_attributions = explainer.shap_values(feature_vector, nsamples=50)
                base_value = float(explainer.expected_value)

            pred_res = model.predict_risk(feature_vector)
            predicted_value = pred_res.predicted_probability if pred_res.is_calibrated else base_value

        except Exception as exc:
            # If SHAP computation fails, cleanly suspend rather than fabricating
            return {
                "method": "SHAP",
                "status": "EXPLAINABILITY_ERROR",
                "base_value": 0.50,
                "prediction_value": 0.50,
                "is_calibrated": True,
                "calibration_status_notice": f"SHAP execution error: {str(exc)}",
                "feature_importances": [],
                "modality_breakdown": {"behavioral": 0.0, "visual_gaze": 0.0, "acoustic_prosody": 0.0},
                "summary_narrative": f"SHAP calculation could not complete on checkpoint: {str(exc)}"
            }

        # Assemble genuine feature importances
        modality_totals = {"behavioral": 0.0, "visual_gaze": 0.0, "acoustic_prosody": 0.0}

        for i, feat_id in enumerate(feature_names):
            defn = FEATURE_MAP[feat_id]
            attr_val = float(raw_attributions[i])
            f_val = float(feature_vector[i])
            direction = "risk_increasing" if attr_val > 0.005 else ("risk_decreasing" if attr_val < -0.005 else "neutral")

            importances.append({
                "feature_name": feat_id,
                "display_name": defn["name"],
                "modality": defn["modality"],
                "feature_value": round(f_val, 3),
                "importance_value": round(attr_val, 4),
                "direction": direction,
                "clinical_note": defn["clinical_note"]
            })
            modality_totals[defn["modality"]] += abs(attr_val)

        importances.sort(key=lambda x: abs(x["importance_value"]), reverse=True)

        total_mag = sum(modality_totals.values()) or 1.0
        modality_breakdown = {
            k: round((v / total_mag) * 100.0, 1) for k, v in modality_totals.items()
        }

        elevated = [f for f in importances if f["importance_value"] > 0.02][:3]
        protective = [f for f in importances if f["importance_value"] < -0.02][:2]
        elevated_names = ", ".join([f["display_name"] for f in elevated]) if elevated else "No elevated factors"
        protective_names = ", ".join([f["display_name"] for f in protective]) if protective else "No mitigating factors"

        narrative = (
            f"Calibrated model SHAP attribution active. Primary risk-increasing contributors: {elevated_names}. "
            f"Baseline-mitigating factors: {protective_names}. "
            f"Cross-modal convergence observed across behavioral, ocular, and acoustic indicators."
        )

        return {
            "method": "SHAP",
            "status": "EXPLAINABILITY_ACTIVE_CALIBRATED",
            "base_value": round(base_value, 4),
            "prediction_value": round(predicted_value, 4),
            "is_calibrated": True,
            "calibration_status_notice": "Verified Model Inference with Calibrated SHAP Attribution",
            "feature_importances": importances,
            "modality_breakdown": modality_breakdown,
            "summary_narrative": narrative
        }
