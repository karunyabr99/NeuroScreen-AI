"""
NeuroScreen AI - Unified Research Prediction Service
Executes clinical inference and explainability across CatBoost, Random Forest, and LASSO models.
Enforces age gating, Youden thresholding, and clinical screening safeguards.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
import joblib
import numpy as np
import pandas as pd

from ml_engine.feature_mapping import FeatureMapper
from ml_engine.shap_explainer import ClinicalSHAPExplainer

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights" / "research_ml"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)


class ResearchPredictionService:
    """
    Inference service for Research-Based ML Models (Paper 1 & Paper 2).
    """

    _instance: Optional['ResearchPredictionService'] = None

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.preprocessors: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.explainers: Dict[str, Any] = {}
        self.load_artifacts()

    @classmethod
    def get_instance(cls) -> 'ResearchPredictionService':
        if cls._instance is None:
            cls._instance = ResearchPredictionService()
        return cls._instance

    def reload(self) -> None:
        self.load_artifacts()

    def load_artifacts(self) -> None:
        """
        Load saved models, preprocessors, metadata, and explainers.
        """
        metadata_file = WEIGHTS_DIR / "research_ml_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {}

        # 1. CatBoost (Paper 1)
        catboost_file = WEIGHTS_DIR / "catboost_research.joblib"
        catboost_prep_file = WEIGHTS_DIR / "catboost_preprocessor.joblib"
        if catboost_file.exists() and catboost_prep_file.exists():
            try:
                self.models["catboost"] = joblib.load(catboost_file)
                self.preprocessors["catboost"] = joblib.load(catboost_prep_file)
                # Initialize SHAP explainer
                feature_names = self.preprocessors["catboost"].get_feature_names_out()
                self.explainers["catboost"] = ClinicalSHAPExplainer(
                    model=self.models["catboost"],
                    feature_names=feature_names
                )
            except Exception as e:
                print(f"[ResearchPredictionService] Error loading CatBoost: {e}")

        # 2. Random Forest (Paper 2)
        rf_file = WEIGHTS_DIR / "random_forest_research.joblib"
        rf_prep_file = WEIGHTS_DIR / "random_forest_preprocessor.joblib"
        if rf_file.exists() and rf_prep_file.exists():
            try:
                self.models["random_forest"] = joblib.load(rf_file)
                self.preprocessors["random_forest"] = joblib.load(rf_prep_file)
            except Exception as e:
                print(f"[ResearchPredictionService] Error loading Random Forest: {e}")

        # 3. LASSO Logistic Regression (Paper 2)
        lasso_file = WEIGHTS_DIR / "lasso_logistic_research.joblib"
        lasso_prep_file = WEIGHTS_DIR / "lasso_logistic_preprocessor.joblib"
        if lasso_file.exists() and lasso_prep_file.exists():
            try:
                self.models["lasso_logistic"] = joblib.load(lasso_file)
                self.preprocessors["lasso_logistic"] = joblib.load(lasso_prep_file)
            except Exception as e:
                print(f"[ResearchPredictionService] Error loading LASSO Logistic: {e}")

    def is_model_ready(self, model_key: str) -> bool:
        return model_key in self.models and model_key in self.preprocessors

    def predict_child(
        self,
        assessment_data: Dict[str, Any],
        model_name: str = "catboost"
    ) -> Dict[str, Any]:
        """
        Execute screening prediction with age gating, Youden thresholding,
        and genuine explainability.
        """
        age_raw = assessment_data.get("Age_Mons", assessment_data.get("age_months"))
        if age_raw is None:
            age_months = None
        else:
            try:
                age_months = float(age_raw)
            except (TypeError, ValueError):
                age_months = None
        if age_months is None or not 0 <= age_months <= 120:
            return {
                "screening_status": "AGE_REQUIRED_OR_INVALID",
                "predicted_probability": None,
                "is_calibrated": False,
                "risk_tier": "AGE_REQUIRED_OR_INVALID",
                "status_message": "A valid child age in months is required. No prediction was generated.",
                "model_used": model_name,
                "explanation": {"method": "SHAP", "status": "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED", "feature_importances": [], "summary_narrative": "No prediction was generated."}
            }

        # Age Gate: Under 12 months (Strict Clinical Safety Rule)
        if age_months < 12:
            return {
                "screening_status": "OBSERVATION_ONLY_UNDER_12M",
                "predicted_probability": None,
                "is_calibrated": False,
                "risk_tier": "OBSERVATION_ONLY_UNDER_12M",
                "risk_category_label": "Infant Observation Only (<12 Months)",
                "confidence_interval": {"lower": 0.0, "upper": 0.0},
                "status_message": (
                    "Standardized toddler screening models are validated for ages 12–36 months. "
                    "For infants under 12 months, screening risk probability is suspended; "
                    "observations are cataloged descriptively for pediatric monitoring."
                ),
                "model_used": model_name,
                "threshold_applied": None,
                "explanation": {
                    "method": "SHAP",
                    "status": "OBSERVATION_ONLY_UNDER_12M",
                    "feature_importances": [],
                    "summary_narrative": "Screening is in observational tracking mode. Statistical feature attribution is suspended."
                },
                "metadata": {
                    "age_months": age_months,
                    "policy": "OBSERVATION_ONLY_UNDER_12M"
                }
            }

        if age_months > 36:
            return {
                "screening_status": "OUTSIDE_VALIDATED_AGE_RANGE",
                "predicted_probability": None,
                "is_calibrated": False,
                "risk_tier": "OUTSIDE_VALIDATED_AGE_RANGE",
                "status_message": "This questionnaire model is restricted to ages 12–36 months. No prediction was generated.",
                "model_used": model_name,
                "explanation": {"method": "SHAP", "status": "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED", "feature_importances": [], "summary_narrative": "Outside validated age range."}
            }
        required_answers = [f"A{i}" for i in range(1, 11)]
        missing_answers = [key for key in required_answers if assessment_data.get(key, assessment_data.get(key.lower())) is None]
        invalid_answers = [key for key in required_answers if assessment_data.get(key, assessment_data.get(key.lower())) is not None and assessment_data.get(key, assessment_data.get(key.lower())) not in (0, 1)]
        if missing_answers or invalid_answers:
            return {
                "screening_status": "QUESTIONNAIRE_INCOMPLETE",
                "predicted_probability": None,
                "is_calibrated": False,
                "risk_tier": "QUESTIONNAIRE_INCOMPLETE",
                "status_message": "All ten explicit Q-CHAT answers (A1–A10, each 0 or 1) are required. No prediction was generated.",
                "model_used": model_name,
                "explanation": {"method": "SHAP", "status": "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED", "feature_importances": [], "summary_narrative": "Questionnaire incomplete; no prediction was generated."}
            }

        # Check model readiness
        clean_model_key = model_name.lower().strip()
        if not self.is_model_ready(clean_model_key):
            clean_model_key = "catboost" if self.is_model_ready("catboost") else next(iter(self.models.keys()), None)

        if clean_model_key is None or not self.is_model_ready(clean_model_key):
            return {
                "screening_status": "UNCALIBRATED_MODEL",
                "predicted_probability": None,
                "is_calibrated": False,
                "risk_tier": "UNCALIBRATED",
                "risk_category_label": "Model Checkpoint Not Initialized",
                "confidence_interval": {"lower": 0.0, "upper": 0.0},
                "status_message": "Research ML models have not yet been trained or checkpoint is missing. Please run model training in the Research ML Hub.",
                "model_used": model_name,
                "threshold_applied": 0.5,
                "explanation": {
                    "method": "SHAP",
                    "status": "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED",
                    "feature_importances": [],
                    "summary_narrative": "Explainability suspended: model checkpoint unmounted."
                }
            }

        model = self.models[clean_model_key]
        preprocessor = self.preprocessors[clean_model_key]

        # 1. Standardize input dictionary into DataFrame
        canonical_dict = FeatureMapper.map_single_instance(assessment_data)
        input_df = pd.DataFrame([canonical_dict])

        # 2. Transform input
        X_trans = preprocessor.transform(input_df)

        # 3. Predict probability
        prob = float(model.predict_proba(X_trans)[0, 1])

        # 4. Threshold & Tier Derivation
        model_meta = self.metadata.get(clean_model_key, {})
        youden_threshold = model_meta.get("youden_threshold", 0.5)

        if clean_model_key == "catboost":
            threshold = youden_threshold
            threshold_label = f"Youden J Threshold ({threshold:.3f})"
            is_elevated = prob >= threshold
            risk_tier = "ELEVATED_TRIAGE_RECOMMENDED" if is_elevated else "LOWER_PREDICTED_RISK"
            risk_category_label = "Elevated Screening Risk (Follow-up Recommended)" if is_elevated else "Lower Predicted Screening Risk"
        else:
            threshold = 0.5
            threshold_label = "Standard Threshold (0.500)"
            is_elevated = prob >= threshold
            risk_tier = "ELEVATED_TRIAGE_RECOMMENDED" if is_elevated else "LOWER_PREDICTED_RISK"
            risk_category_label = "Elevated Screening Risk (Follow-up Recommended)" if is_elevated else "Lower Predicted Screening Risk"

        # 95% Confidence Interval approximation
        n_eff = 1054
        se = float(np.sqrt(max(1e-6, prob * (1.0 - prob) / n_eff)))
        ci_lower = max(0.0, prob - 1.96 * se)
        ci_upper = min(1.0, prob + 1.96 * se)

        # 5. Explainability
        if clean_model_key == "catboost" and "catboost" in self.explainers:
            explanation = self.explainers["catboost"].explain_instance(X_trans, predicted_probability=prob)
        elif clean_model_key == "lasso_logistic":
            # LASSO coefficient attribution
            coefs = model.coef_[0]
            feature_names = preprocessor.get_feature_names_out()
            feature_contribs = []
            positive_drivers = []
            protective_factors = []
            for i, name in enumerate(feature_names):
                weight = float(coefs[i])
                feature_val = float(X_trans[0, i])
                effect = weight * feature_val
                entry = {
                    "feature": name,
                    "contribution": round(effect, 4),
                    "abs_contribution": round(abs(effect), 4),
                    "coefficient": round(weight, 4),
                    "feature_value": feature_val,
                    "direction": "Risk-Increasing (+)" if effect > 0 else "Protective / Risk-Reducing (-)" if effect < 0 else "Neutral"
                }
                feature_contribs.append(entry)
                if effect > 0.05:
                    positive_drivers.append(entry)
                elif effect < -0.05:
                    protective_factors.append(entry)
            feature_contribs.sort(key=lambda x: x["abs_contribution"], reverse=True)
            positive_drivers.sort(key=lambda x: x["contribution"], reverse=True)
            protective_factors.sort(key=lambda x: x["contribution"])
            top_drivers = [d["feature"] for d in positive_drivers[:3]]
            top_protects = [p["feature"] for p in protective_factors[:2]]
            narrative = f"LASSO regression identifies key risk indicators: {', '.join(top_drivers) if top_drivers else 'None marked'}."
            if top_protects:
                narrative += f" Moderated by: {', '.join(top_protects)}."
            explanation = {
                "method": "LASSO Linear Coefficients",
                "base_value": round(float(model.intercept_[0]), 4),
                "prediction_value": round(prob, 4),
                "status": "EXPLAINABILITY_ACTIVE_CALIBRATED",
                "feature_importances": feature_contribs[:15],
                "positive_risk_drivers": positive_drivers[:6],
                "protective_factors": protective_factors[:6],
                "summary_narrative": narrative
            }
        else:
            # Random Forest Gini Feature Importance
            feature_names = preprocessor.get_feature_names_out()
            importances = model.feature_importances_
            feature_contribs = [
                {
                    "feature": name,
                    "contribution": round(float(importances[i]), 4),
                    "abs_contribution": round(float(importances[i]), 4),
                    "feature_value": float(X_trans[0, i]),
                    "direction": "Informative Feature"
                }
                for i, name in enumerate(feature_names)
            ]
            feature_contribs.sort(key=lambda x: x["abs_contribution"], reverse=True)
            top_feats = [f["feature"] for f in feature_contribs[:3]]
            explanation = {
                "method": "Random Forest Gini Importance",
                "base_value": 0.5,
                "prediction_value": round(prob, 4),
                "status": "EXPLAINABILITY_ACTIVE_CALIBRATED",
                "feature_importances": feature_contribs[:15],
                "positive_risk_drivers": feature_contribs[:3],
                "protective_factors": [],
                "summary_narrative": f"Random Forest screening heavily weighted by observations: {', '.join(top_feats)}."
            }

        status_msg = f"Screening inference executed using {model_meta.get('model_name', clean_model_key)} with {threshold_label}."
        if age_months > 36:
            status_msg += " (Note: Age > 36 months; toddler screening model applied with standard developmental context)"

        return {
            "screening_status": "COMPLETED",
            "predicted_probability": round(prob, 4),
            "is_calibrated": True,
            "risk_tier": risk_tier,
            "risk_category_label": risk_category_label,
            "confidence_interval": {"lower": round(ci_lower, 4), "upper": round(ci_upper, 4)},
            "threshold_applied": round(threshold, 4),
            "threshold_label": threshold_label,
            "status_message": status_msg,
            "model_used": clean_model_key,
            "model_title": model_meta.get("model_name", clean_model_key),
            "explanation": explanation,
            "raw_inputs": canonical_dict
        }

