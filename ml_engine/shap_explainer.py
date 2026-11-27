"""
NeuroScreen AI - SHAP Explainability Engine for CatBoost & Clinical Models
Implements genuine SHapley Additive exPlanations via shap.TreeExplainer.
Provides global feature rankings, local instance waterfall decompositions,
and clinically grounded narrative summaries.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import shap


class ClinicalSHAPExplainer:
    """
    Dedicated clinical SHAP engine for CatBoost and Tree Ensembles.
    """

    def __init__(self, model: Any, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer: Optional[shap.TreeExplainer] = None
        self.base_value: float = 0.5
        self._init_explainer()

    def _init_explainer(self) -> None:
        if self.model is not None:
            try:
                self.explainer = shap.TreeExplainer(self.model)
                ev = self.explainer.expected_value
                if isinstance(ev, (list, np.ndarray)):
                    self.base_value = float(ev[1]) if len(ev) > 1 else float(ev[0])
                else:
                    self.base_value = float(ev)
            except Exception:
                self.explainer = None

    def explain_instance(
        self,
        features_2d: np.ndarray,
        predicted_probability: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Explain a single child screening instance.
        """
        if self.explainer is None or self.model is None:
            return {
                "method": "SHAP",
                "base_value": 0.5,
                "prediction_value": predicted_probability,
                "status": "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED",
                "feature_importances": [],
                "positive_risk_drivers": [],
                "protective_factors": [],
                "summary_narrative": "SHAP explainability suspended: Valid calibrated model checkpoint is not initialized."
            }

        try:
            # shap_values shape: (1, n_features) or list
            raw_shap = self.explainer.shap_values(features_2d)
            if isinstance(raw_shap, list):
                phi = np.array(raw_shap[1][0] if len(raw_shap) > 1 else raw_shap[0][0])
            elif len(raw_shap.shape) == 2:
                phi = np.array(raw_shap[0])
            else:
                phi = np.array(raw_shap)

            feature_contributions = []
            positive_drivers = []
            protective_factors = []

            for i, name in enumerate(self.feature_names):
                val_contrib = float(phi[i])
                feature_val = float(features_2d[0, i]) if i < features_2d.shape[1] else None

                entry = {
                    "feature": name,
                    "contribution": round(val_contrib, 5),
                    "abs_contribution": round(abs(val_contrib), 5),
                    "feature_value": feature_val,
                    "direction": "Risk-Increasing (+)" if val_contrib > 0 else "Protective / Risk-Reducing (-)" if val_contrib < 0 else "Neutral"
                }
                feature_contributions.append(entry)
                if val_contrib > 0.005:
                    positive_drivers.append(entry)
                elif val_contrib < -0.005:
                    protective_factors.append(entry)

            feature_contributions.sort(key=lambda x: x["abs_contribution"], reverse=True)
            positive_drivers.sort(key=lambda x: x["contribution"], reverse=True)
            protective_factors.sort(key=lambda x: x["contribution"])

            # Narrative generation
            top_drivers = [d["feature"] for d in positive_drivers[:3]]
            top_protects = [p["feature"] for p in protective_factors[:2]]

            narrative_parts = []
            if top_drivers:
                narrative_parts.append(f"Primary factors driving predicted screening risk elevation: {', '.join(top_drivers)}.")
            if top_protects:
                narrative_parts.append(f"Observed typical responses moderating predicted risk: {', '.join(top_protects)}.")
            if not narrative_parts:
                narrative_parts.append("Observation items are balanced with neutral statistical contribution.")

            summary_narrative = " ".join(narrative_parts)

            return {
                "method": "SHAP (TreeExplainer)",
                "base_value": round(self.base_value, 4),
                "prediction_value": round(predicted_probability, 4) if predicted_probability is not None else None,
                "status": "EXPLAINABILITY_ACTIVE_CALIBRATED",
                "feature_importances": feature_contributions[:15],
                "positive_risk_drivers": positive_drivers[:6],
                "protective_factors": protective_factors[:6],
                "summary_narrative": summary_narrative
            }
        except Exception as e:
            return {
                "method": "SHAP",
                "base_value": 0.5,
                "prediction_value": predicted_probability,
                "status": f"EXPLAINABILITY_ERROR: {str(e)}",
                "feature_importances": [],
                "positive_risk_drivers": [],
                "protective_factors": [],
                "summary_narrative": f"SHAP calculation error: {str(e)}"
            }

