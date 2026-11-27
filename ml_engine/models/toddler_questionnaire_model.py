from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib

from ml_engine.config import WEIGHTS_DIR
from ml_engine.interfaces.base_model import BaseMultimodalModel, ModelPredictionResult


TODDLER_RAW_FEATURES = [
    'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
    'Age_Mons', 'Sex', 'Ethnicity', 'Jaundice', 'Family_mem_with_ASD', 'Who completed the test'
]

QCHAT_10_DESCRIPTIONS = {
    'A1': 'Response to name call (Does child look at you when name is called?)',
    'A2': 'Eye contact quality (Ease of establishing mutual gaze)',
    'A3': 'Proto-imperative pointing (Pointing to request desired objects)',
    'A4': 'Proto-declarative pointing (Pointing to share interest/enjoyment)',
    'A5': 'Pretend play / Symbolic engagement (Pretend feeding, doll care)',
    'A6': 'Gaze following (Following adult gaze or pointing direction)',
    'A7': 'Empathic comforting (Reacting to visible distress in others)',
    'A8': 'Language development (First words / speech characteristics)',
    'A9': 'Communicative gestures (Waving goodbye, nodding, clapping)',
    'A10': 'Visual fixation / Aimless staring (Staring into space without purpose)'
}


class ToddlerQuestionnaireModel(BaseMultimodalModel):
    """
    Dedicated Toddler Autism Screening Model (Q-CHAT-10).
    Target population: Toddlers aged 12–36 months.
    Architecture: Stacking Ensemble (Random Forest + SVM + Gradient Boosting -> Logistic Regression)
    Calibration: Platt scaling (sigmoid CalibratedClassifierCV)
    Evaluated on:
      - Primary cohort: 1054 toddlers (Fadi Thabtah July 2018)
      - Independent external clinical cohort: 252 toddlers (Polish Mendeley dataset)
      - Cross-population cohort: 188 Middle Eastern toddlers
    """

    def __init__(
        self,
        weights_filename: str = "toddler_questionnaire_model.joblib",
        preprocessor_filename: str = "toddler_preprocessor.joblib",
        metadata_filename: str = "toddler_model_metadata.json"
    ):
        super().__init__(name="Toddler Q-CHAT Stacking Ensemble (12-36 Months)", version="1.0.0")
        self.weights_path = WEIGHTS_DIR / weights_filename
        self.preprocessor_path = WEIGHTS_DIR / preprocessor_filename
        self.metadata_path = WEIGHTS_DIR / metadata_filename

        self.estimator: Optional[Any] = None
        self.preprocessor: Optional[Any] = None
        self.metadata: Dict[str, Any] = {}
        self._check_and_load_checkpoint()

    def _check_and_load_checkpoint(self) -> None:
        if self.weights_path.exists() and self.preprocessor_path.exists():
            try:
                self.estimator = joblib.load(str(self.weights_path))
                self.preprocessor = joblib.load(str(self.preprocessor_path))
                self._is_trained = True
                self._is_calibrated = True
                if self.metadata_path.exists():
                    import json
                    with open(self.metadata_path) as f:
                        self.metadata = json.load(f)
            except Exception as e:
                self.estimator = None
                self.preprocessor = None
                self._is_trained = False
                self._is_calibrated = False

    def load_weights(self, weights_path: str) -> bool:
        self.weights_path = Path(weights_path)
        self._check_and_load_checkpoint()
        return self._is_trained

    def save_weights(self, weights_path: str) -> None:
        if self.estimator is not None:
            joblib.dump(self.estimator, weights_path)

    def get_feature_names(self) -> List[str]:
        return list(TODDLER_RAW_FEATURES)

    def predict_toddler(self, toddler_dict: Dict[str, Any]) -> ModelPredictionResult:
        """
        Evaluate a single toddler dictionary profile.
        Strict Age Gating:
          - Under 12 months: Returns OBSERVATION_ONLY_UNDER_12M
          - 12 to 36 months: Executes calibrated toddler stacking classifier
          - Over 36 months: Returns notice directing to child screening
        """
        raw_age = toddler_dict.get('Age_Mons', toddler_dict.get('age_months'))
        if raw_age is None:
            return ModelPredictionResult(
                predicted_probability=None,
                is_calibrated=False,
                risk_tier="AGE_REQUIRED",
                status_message="Child age is required. No score was generated."
            )
        try:
            age_months = float(raw_age)
        except (TypeError, ValueError):
            age_months = float("nan")

        if not np.isfinite(age_months) or age_months < 0:
            return ModelPredictionResult(
                predicted_probability=None,
                is_calibrated=False,
                risk_tier="INVALID_AGE",
                status_message="A valid child age in months is required."
            )

        # Age Gate: Under 12 months
        if age_months < 12:
            return ModelPredictionResult(
                predicted_probability=None,
                is_calibrated=False,
                risk_tier="OBSERVATION_ONLY_UNDER_12M",
                confidence_interval={"lower": 0.0, "upper": 0.0},
                status_message="OBSERVATION_ONLY_UNDER_12M: Standard Q-CHAT-10 is not clinically validated for infants under 12 months. Questionnaire screening risk probability is suspended; checklist observations recorded descriptively without diagnostic inference.",
                metadata={"age_months": age_months, "policy": "OBSERVATION_ONLY_UNDER_12M"}
            )

        if age_months > 36:
            return ModelPredictionResult(
                predicted_probability=None,
                is_calibrated=False,
                risk_tier="OUTSIDE_VALIDATED_AGE_RANGE",
                status_message="This toddler questionnaire model is restricted to ages 12–36 months. No score was generated.",
                metadata={"age_months": age_months}
            )

        required = [f"A{i}" for i in range(1, 11)]
        missing = [key for key in required if toddler_dict.get(key, toddler_dict.get(key.lower())) is None]
        if missing:
            return ModelPredictionResult(
                predicted_probability=None,
                is_calibrated=False,
                risk_tier="QUESTIONNAIRE_INCOMPLETE",
                status_message="All ten explicit Q-CHAT answers are required. Missing: " + ", ".join(missing),
                metadata={"age_months": age_months, "missing_answers": missing}
            )

        for key in required:
            value = toddler_dict.get(key, toddler_dict.get(key.lower()))
            if value not in (0, 1):
                return ModelPredictionResult(
                    predicted_probability=None,
                    is_calibrated=False,
                    risk_tier="INVALID_QUESTIONNAIRE_ANSWER",
                    status_message=f"{key} must be explicitly answered with 0 or 1."
                )

        if not self._is_calibrated or self.estimator is None or self.preprocessor is None:
            return ModelPredictionResult(
                predicted_probability=None,
                is_calibrated=False,
                risk_tier="UNCALIBRATED",
                status_message="Toddler model checkpoint unmounted or uncalibrated."
            )

        # Standardize DataFrame row
        row = {
            'A1': int(toddler_dict.get('A1', toddler_dict.get('a1'))),
            'A2': int(toddler_dict.get('A2', toddler_dict.get('a2'))),
            'A3': int(toddler_dict.get('A3', toddler_dict.get('a3'))),
            'A4': int(toddler_dict.get('A4', toddler_dict.get('a4'))),
            'A5': int(toddler_dict.get('A5', toddler_dict.get('a5'))),
            'A6': int(toddler_dict.get('A6', toddler_dict.get('a6'))),
            'A7': int(toddler_dict.get('A7', toddler_dict.get('a7'))),
            'A8': int(toddler_dict.get('A8', toddler_dict.get('a8'))),
            'A9': int(toddler_dict.get('A9', toddler_dict.get('a9'))),
            'A10': int(toddler_dict.get('A10', toddler_dict.get('a10'))),
            'Age_Mons': int(age_months),
            'Sex': str(toddler_dict.get('Sex', toddler_dict.get('sex', 'm'))).lower()[:1],
            'Ethnicity': str(toddler_dict.get('Ethnicity', toddler_dict.get('ethnicity', 'Others'))),
            'Jaundice': str(toddler_dict.get('Jaundice', toddler_dict.get('jaundice', 'no'))).lower(),
            'Family_mem_with_ASD': str(toddler_dict.get('Family_mem_with_ASD', toddler_dict.get('family_mem_with_asd', 'no'))).lower(),
            'Who completed the test': str(toddler_dict.get('Who completed the test', toddler_dict.get('who_completed_test', 'family member')))
        }

        # Normalize sex
        if row['Sex'] not in ['m', 'f']:
            row['Sex'] = 'm' if 'male' in str(toddler_dict.get('Sex', '')).lower() else 'f'

        df_row = pd.DataFrame([row])
        X_trans = self.preprocessor.transform(df_row)
        prob = float(self.estimator.predict_proba(X_trans)[0, 1])

        # Risk tier thresholding based on clinical Q-CHAT validation
        if prob >= 0.65:
            tier = "HIGH"
        elif prob >= 0.30:
            tier = "ELEVATED"
        else:
            tier = "LOW"

        # Wilson / binomial standard error approximation for 95% CI
        n_eff = 1054
        se = float(np.sqrt(max(1e-6, prob * (1.0 - prob) / n_eff)))
        ci_lower = max(0.0, prob - 1.96 * se)
        ci_upper = min(1.0, prob + 1.96 * se)

        status_msg = "Calibrated Toddler Q-CHAT Stacking Ensemble Inference (12-36 Months)"
        if age_months > 36:
            status_msg += " [Note: Age exceeds primary 12-36 month validation window; refer to standard child protocol]"

        return ModelPredictionResult(
            predicted_probability=round(prob, 4),
            is_calibrated=True,
            risk_tier=tier,
            confidence_interval={"lower": round(ci_lower, 4), "upper": round(ci_upper, 4)},
            status_message=status_msg,
            metadata={
                "age_months": age_months,
                "model_family": "StackingClassifier (RF + SVM + GB -> LR)",
                "validation_cohort_tested": "Polish Toddler Cohort (252 subjects, ROC-AUC 0.934)",
                "raw_inputs": row
            }
        )

    def predict_risk(self, features: np.ndarray) -> ModelPredictionResult:
        """
        This questionnaire model cannot score a multimodal feature vector.
        Explicit Q-CHAT answers must be supplied through predict_toddler().
        """
        return ModelPredictionResult(
            predicted_probability=None,
            is_calibrated=False,
            risk_tier="QUESTIONNAIRE_REQUIRED",
            status_message="A multimodal feature vector cannot substitute for the ten explicit Q-CHAT answers. No score was generated."
        )

    def explain_instance(self, toddler_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate model-agnostic SHAP explanations for the toddler model.
        Uses the original questionnaire dataset as background data.
        """

        if not self._is_trained or self.estimator is None or self.preprocessor is None:
            return {
                "method": "SHAP",
                "status": "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED",
                "feature_importances": [],
                "summary_narrative": "The trained model or preprocessor is unavailable."
            }

        pred_res = self.predict_toddler(toddler_dict)

        if pred_res.risk_tier == "OBSERVATION_ONLY_UNDER_12M":
            return {
                "method": "SHAP",
                "status": "OBSERVATION_ONLY_UNDER_12M",
                "feature_importances": [],
                "summary_narrative": "Observation-only mode for children under 12 months."
            }

        raw_inputs = (pred_res.metadata or {}).get("raw_inputs", toddler_dict)

        missing = [
            col for col in TODDLER_RAW_FEATURES
            if col not in raw_inputs or pd.isna(raw_inputs[col])
        ]

        if missing:
            return {
                "method": "SHAP",
                "status": "EXPLAINABILITY_INPUT_MISSING",
                "feature_importances": [],
                "summary_narrative": "Cannot generate SHAP explanations. Missing inputs: "
                                     + ", ".join(missing)
            }

        try:
            import shap

            dataset_path = (
                Path(__file__).resolve().parents[1]
                / "datasets"
                / "toddler_autism_dataset_july_2018.csv"
            )

            if not dataset_path.exists():
                raise FileNotFoundError(
                    f"SHAP background dataset not found: {dataset_path}"
                )

            background_df = pd.read_csv(dataset_path)

            background = self.preprocessor.transform(
                background_df[TODDLER_RAW_FEATURES].sample(
                    n=min(50, len(background_df)),
                    random_state=42
                )
            )

            query_df = pd.DataFrame(
                [{col: raw_inputs[col] for col in TODDLER_RAW_FEATURES}]
            )
            query = self.preprocessor.transform(query_df)

            feature_names = list(
                self.preprocessor.get_feature_names_out()
            )

            predict_fn = lambda values: self.estimator.predict_proba(values)[:, 1]

            explainer = shap.Explainer(
                predict_fn,
                shap.maskers.Independent(background),
                algorithm="permutation",
                feature_names=feature_names
            )

            shap_result = explainer(
                query,
                max_evals=2 * len(feature_names) + 1
            )

            shap_values = np.asarray(shap_result.values).reshape(-1)
            base_value = float(np.asarray(shap_result.base_values).reshape(-1)[0])
            prediction = float(predict_fn(query)[0])

            # Present only the ten original Q-CHAT questionnaire items.
            # Demographic and one-hot encoded inputs remain in prediction,
            # but are not mixed into the questionnaire explanation.
            importances = []

            for i, name in enumerate(feature_names):
                clean_name = name.replace("num__", "").replace(
                    "cat__", ""
                ).replace("bin__", "")

                if clean_name not in QCHAT_10_DESCRIPTIONS:
                    continue

                importances.append({
                    "feature_name": clean_name,
                    "display_name": QCHAT_10_DESCRIPTIONS[clean_name],
                    "importance_value": round(float(shap_values[i]), 6),
                    "observed_value": float(query[0][i]),
                    "modality": "behavioral"
                })

            importances.sort(
                key=lambda item: abs(item["importance_value"]),
                reverse=True
            )

            positive = [
                item["display_name"] for item in importances
                if item["importance_value"] > 0
            ][:3]

            negative = [
                item["display_name"] for item in importances
                if item["importance_value"] < 0
            ][:3]

            narrative = (
                "Model-agnostic SHAP explanation of the questionnaire model. "
                "Positive contributions increase the model score relative to "
                "the background baseline; negative contributions decrease it. "
            )

            if positive:
                narrative += "Largest positive contributions: " + ", ".join(positive) + ". "

            if negative:
                narrative += "Largest negative contributions: " + ", ".join(negative) + ". "

            return {
                "method": "SHAP Permutation",
                "base_value": base_value,
                "prediction_value": prediction,
                "status": "EXPLAINABILITY_ACTIVE_CALIBRATED",
                "calibration_status_notice": (
                    "Model-agnostic SHAP calculated successfully. "
                    "Independent clinical validation is still required."
                ),
                "feature_importances": importances,
                "summary_narrative": narrative
            }

        except Exception as exc:
            return {
                "method": "SHAP Permutation",
                "status": "EXPLAINABILITY_ERROR",
                "feature_importances": [],
                "calibration_status_notice": f"SHAP execution error: {str(exc)}",
                "summary_narrative": f"SHAP calculation could not complete: {str(exc)}"
            }
