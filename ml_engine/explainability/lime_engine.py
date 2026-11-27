from typing import Dict, Any, List
import numpy as np
from lime.lime_tabular import LimeTabularExplainer

from ml_engine.config import FEATURE_NAMES, FEATURE_MAP
from ml_engine.interfaces.base_explainer import BaseExplainer
from ml_engine.interfaces.base_model import BaseMultimodalModel

class LIMEExplanationEngine(BaseExplainer):
    """
    LIME (Local Interpretable Model-agnostic Explanations) Engine.
    Provides local surrogate linear models around the screening instance.
    Adheres strictly to clinical governance: feature attribution calculations are strictly
    suspended when models are untrained or uncalibrated to prevent fabricated explanations.
    """

    @property
    def explainer_type(self) -> str:
        return "LIME"

    def explain_instance(
        self,
        model: BaseMultimodalModel,
        feature_vector: np.ndarray,
        feature_names: List[str] = FEATURE_NAMES
    ) -> Dict[str, Any]:
        """
        Generates local surrogate linear explanation weights using LIME if model is trained.
        If untrained/uncalibrated, strictly suspends calculation and returns an empty array.
        """
        # Strict calibration & training gate
        if not (model.is_trained and model.is_calibrated):
            return {
                "method": "LIME",
                "status": "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED",
                "base_value": 0.50,
                "prediction_value": 0.50,
                "is_calibrated": False,
                "calibration_status_notice": (
                    "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED: Model checkpoint unmounted. "
                    "LIME local surrogate linear approximation is suspended until a trained model is mounted."
                ),
                "feature_importances": [],
                "modality_breakdown": {
                    "behavioral": 0.0,
                    "visual_gaze": 0.0,
                    "acoustic_prosody": 0.0
                },
                "summary_narrative": (
                    "Explainability analysis suspended. LIME local surrogate weights require a trained decision model. "
                    "In compliance with clinical governance, surrogate approximations are not generated for uncalibrated models."
                )
            }

        # Genuine LIME calculation for trained & calibrated models
        importances: List[Dict[str, Any]] = []
        base_value = 0.50
        predicted_value = 0.50

        try:
            background = np.tile(
                [FEATURE_MAP[f]["mean_norm"] for f in feature_names],
                (50, 1)
            ) + np.random.normal(0, 0.05, (50, len(feature_names)))

            explainer = LimeTabularExplainer(
                training_data=background,
                feature_names=feature_names,
                class_names=["Typical", "ASD Risk"],
                mode="classification"
            )

            def predict_fn(X: np.ndarray):
                preds = []
                for row in X:
                    res = model.predict_risk(row)
                    p = res.predicted_probability if res.is_calibrated else 0.5
                    preds.append([1.0 - p, p])
                return np.array(preds)

            exp = explainer.explain_instance(
                data_row=feature_vector,
                predict_fn=predict_fn,
                num_features=len(feature_names),
                num_samples=150
            )

            exp_map = dict(exp.as_list())
            raw_attributions = np.zeros(len(feature_names), dtype=np.float32)
            for i, feat_id in enumerate(feature_names):
                for k, val in exp_map.items():
                    if feat_id in k:
                        raw_attributions[i] = val
                        break

            pred_res = model.predict_risk(feature_vector)
            predicted_value = pred_res.predicted_probability if pred_res.is_calibrated else base_value

        except Exception as exc:
            return {
                "method": "LIME",
                "status": "EXPLAINABILITY_ERROR",
                "base_value": 0.50,
                "prediction_value": 0.50,
                "is_calibrated": True,
                "calibration_status_notice": f"LIME execution error: {str(exc)}",
                "feature_importances": [],
                "modality_breakdown": {"behavioral": 0.0, "visual_gaze": 0.0, "acoustic_prosody": 0.0},
                "summary_narrative": f"LIME calculation could not complete on checkpoint: {str(exc)}"
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

        top_names = [f["display_name"] for f in importances[:2]] if len(importances) >= 2 else []
        narrative = (
            f"LIME local surrogate linear analysis completed. Decision boundaries in this patient instance's "
            f"neighborhood are most sensitive to: {', '.join(top_names)}."
        )

        return {
            "method": "LIME",
            "status": "EXPLAINABILITY_ACTIVE_CALIBRATED",
            "base_value": round(base_value, 4),
            "prediction_value": round(predicted_value, 4),
            "is_calibrated": True,
            "calibration_status_notice": "Verified LIME Surrogate Linear Approximation",
            "feature_importances": importances,
            "modality_breakdown": modality_breakdown,
            "summary_narrative": narrative
        }
