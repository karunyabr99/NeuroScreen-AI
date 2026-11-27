"""
NeuroScreen AI - Configurable Feature Mapping & Clinical Alignment System
Maps varying questionnaire column formats, clinical variables, and assessment inputs
to standardized model feature schemas. Explicitly accounts for research paper feature availability.
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd


# Canonical Feature Schema for Toddler Screening
CANONICAL_FEATURES = {
    "binary_items": [f"A{i}" for i in range(1, 11)],
    "numerical_items": ["Age_Mons"],
    "categorical_items": ["Sex", "Ethnicity", "Jaundice", "Family_mem_with_ASD", "Who completed the test"]
}

# Aliases for flexible CSV header & assessment payload resolution
FEATURE_ALIASES = {
    "A1": ["a1", "qchat_1", "item_1", "q1", "a1_score", "social_smile_or_name"],
    "A2": ["a2", "qchat_2", "item_2", "q2", "a2_score", "eye_contact"],
    "A3": ["a3", "qchat_3", "item_3", "q3", "a3_score", "pointing_protoimperative"],
    "A4": ["a4", "qchat_4", "item_4", "q4", "a4_score", "pointing_protodeclarative"],
    "A5": ["a5", "qchat_5", "item_5", "q5", "a5_score", "pretend_play"],
    "A6": ["a6", "qchat_6", "item_6", "q6", "a6_score", "gaze_following"],
    "A7": ["a7", "qchat_7", "item_7", "q7", "a7_score", "empathy_comforting"],
    "A8": ["a8", "qchat_8", "item_8", "q8", "a8_score", "language_first_words"],
    "A9": ["a9", "qchat_9", "item_9", "q9", "a9_score", "gestures_waving"],
    "A10": ["a10", "qchat_10", "item_10", "q10", "a10_score", "visual_staring"],
    "Age_Mons": ["age_mons", "age_months", "age", "child_age", "months"],
    "Sex": ["sex", "gender"],
    "Ethnicity": ["ethnicity", "race", "ethnic_group"],
    "Jaundice": ["jaundice", "neonatal_jaundice", "born_with_jaundice"],
    "Family_mem_with_ASD": ["family_mem_with_asd", "family_asd", "asd_relative", "family_history_asd"],
    "Who completed the test": ["who completed the test", "who_completed_test", "completed_by", "assessor"]
}

# Transparent comparison of features across research literature vs Toddler Screening Dataset
PAPER_FEATURE_COMPARISON = {
    "paper_1_well_baby_2024": {
        "title": "A Prediction Model of Autism Spectrum Diagnosis from Well-Baby Electronic Data Using Machine Learning (2024)",
        "available_in_dataset": [
            "Age at encounter (Age_Mons)", "Sex at birth (Sex)", "Jaundice diagnosis history",
            "Family history of ASD", "Behavioral milestones (A1-A10 equivalent developmental items)"
        ],
        "unavailable_in_dataset": [
            "Birth weight percentile", "Head circumference trajectory",
            "Gestational age in weeks", "APGAR scores", "Maternal age at delivery",
            "Frequency of pediatric well-child visits"
        ],
        "methodology_adopted": "CatBoost gradient boosting, 3-fold stratified cross-validation, Youden J index optimal thresholding, SHAP explainability."
    },
    "paper_2_medical_claims_2022": {
        "title": "Early Detection of Autism Spectrum Disorder in Young Children with Machine Learning Using Medical Claims Data (2022)",
        "available_in_dataset": [
            "Chronological age in months", "Sex", "Family medical history of neurodevelopmental conditions"
        ],
        "unavailable_in_dataset": [
            "ICD-10 clinical diagnostic codes", "Outpatient pediatric billing encounters",
            "Inpatient hospital admissions", "Prescription drug claims codes"
        ],
        "methodology_adopted": "LASSO Logistic Regression (L1 penalty feature selection), Random Forest with Gini importance, Standardized numerical pipeline, AUPRC (PR-AUC) and ROC-AUC evaluation."
    }
}


class FeatureMapper:
    """
    Standardizes raw input dictionaries or DataFrames into the canonical feature schema.
    """

    @classmethod
    def resolve_column_mapping(cls, available_columns: List[str]) -> Tuple[Dict[str, str], List[str]]:
        """
        Map available columns to canonical schema. Returns (mapping, missing_canonical_keys).
        """
        mapping: Dict[str, str] = {}
        col_lower_map = {c.strip().lower(): c for c in available_columns}

        for canonical, aliases in FEATURE_ALIASES.items():
            # Check exact match
            if canonical in available_columns:
                mapping[canonical] = canonical
                continue
            # Check lowercase
            if canonical.lower() in col_lower_map:
                mapping[canonical] = col_lower_map[canonical.lower()]
                continue
            # Check aliases
            found = False
            for alias in aliases:
                if alias.lower() in col_lower_map:
                    mapping[canonical] = col_lower_map[alias.lower()]
                    found = True
                    break

        all_canonical = (
            CANONICAL_FEATURES["binary_items"] +
            CANONICAL_FEATURES["numerical_items"] +
            CANONICAL_FEATURES["categorical_items"]
        )
        missing = [c for c in all_canonical if c not in mapping]

        return mapping, missing

    @classmethod
    def map_dataframe(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Remap DataFrame columns to canonical names.
        """
        mapping, missing = cls.resolve_column_mapping(list(df.columns))
        inverse_mapping = {v: k for k, v in mapping.items()}
        renamed_df = df.rename(columns=inverse_mapping)

        report = {
            "mapped_features_count": len(mapping),
            "missing_features": missing,
            "column_mapping": mapping,
            "paper_feature_comparison": PAPER_FEATURE_COMPARISON
        }
        return renamed_df, report

    @classmethod
    def map_single_instance(cls, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single input dictionary (e.g. from frontend assessment) to canonical format.
        """
        normalized: Dict[str, Any] = {}

        for canonical, aliases in FEATURE_ALIASES.items():
            val = None
            if canonical in instance:
                val = instance[canonical]
            elif canonical.lower() in instance:
                val = instance[canonical.lower()]
            else:
                for alias in aliases:
                    if alias in instance:
                        val = instance[alias]
                        break
                    elif alias.lower() in instance:
                        val = instance[alias.lower()]
                        break

            # Defaults if missing
            if val is None:
                if canonical in CANONICAL_FEATURES["binary_items"]:
                    val = 0
                elif canonical == "Age_Mons":
                    val = 24
                elif canonical == "Sex":
                    val = "m"
                elif canonical == "Ethnicity":
                    val = "Others"
                elif canonical in ["Jaundice", "Family_mem_with_ASD"]:
                    val = "no"
                elif canonical == "Who completed the test":
                    val = "family member"

            normalized[canonical] = val

        # Type normalization
        for b in CANONICAL_FEATURES["binary_items"]:
            normalized[b] = int(normalized[b])
        normalized["Age_Mons"] = float(normalized["Age_Mons"])
        normalized["Sex"] = str(normalized["Sex"]).lower()[:1]
        if normalized["Sex"] not in ["m", "f"]:
            normalized["Sex"] = "m"

        return normalized

