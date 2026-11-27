"""
Comprehensive Test Suite for Research-Based Autism Screening ML System
Validates Paper 1 (2024) CatBoost, Paper 2 (2022) Random Forest & LASSO,
Leakage Prevention, Youden Thresholding, SHAP Explainability, and Backend APIs.
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from ml_engine.data_loader import DatasetLoader
from ml_engine.leakage_audit import LeakageAuditor
from ml_engine.preprocessing import ClinicalDataPreprocessor
from ml_engine.model_evaluation import compute_clinical_metrics, compute_youden_threshold
from ml_engine.train_catboost import CatBoostTrainer
from ml_engine.train_random_forest import RandomForestTrainer
from ml_engine.train_logistic_regression import LassoLogisticRegressionTrainer
from ml_engine.prediction_service import ResearchPredictionService


DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "ml_engine" / "datasets" / "toddler_autism_dataset_july_2018.csv"


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def dataset_df():
    assert DATASET_PATH.exists(), f"Dataset not found at {DATASET_PATH}"
    return DatasetLoader.load_csv(DATASET_PATH)


# =============================================================================
# 1. DATASET LOADER & SCHEMA INSPECTOR TESTS
# =============================================================================

def test_dataset_loader_and_schema_inspection(dataset_df):
    assert len(dataset_df) == 1054
    assert len(dataset_df.columns) == 19

    inspection = DatasetLoader.inspect_dataset(dataset_df)
    assert inspection["row_count"] == 1054
    assert inspection["column_count"] == 19
    assert inspection["identified_target"] == "Class/ASD Traits"
    assert "Case_No" in inspection["id_columns"]
    assert "Qchat-10-Score" in inspection["leakage_columns"]
    assert inspection["class_balance"]["counts"]["Yes"] == 728
    assert inspection["class_balance"]["counts"]["No"] == 326
    assert len(inspection["preview"]) <= 10


# =============================================================================
# 2. TARGET LEAKAGE AUDIT TESTS
# =============================================================================

def test_target_leakage_audit_drops_leakage_columns(dataset_df):
    sanitized_df, audit_summary = LeakageAuditor.audit_and_clean(
        dataset_df, target_col="Class/ASD Traits"
    )

    # Must drop Case_No and Qchat-10-Score
    assert "Case_No" in audit_summary["dropped_columns"]
    assert "Qchat-10-Score" in audit_summary["dropped_columns"]
    assert "Case_No" not in sanitized_df.columns
    assert "Qchat-10-Score" not in sanitized_df.columns

    # Must preserve legitimate questionnaire items and demographics
    for i in range(1, 11):
        assert f"A{i}" in sanitized_df.columns
    assert "Age_Mons" in sanitized_df.columns
    assert "Sex" in sanitized_df.columns
    assert "Ethnicity" in sanitized_df.columns

    # Check audit explanations
    reasons = [r["issue"] for r in audit_summary["audit_records"]]
    assert "ARBITRARY_IDENTIFIER" in reasons
    assert "DETERMINISTIC_TARGET_LEAKAGE" in reasons


# =============================================================================
# 3. PREPROCESSING & FOLD ISOLATION TESTS
# =============================================================================

def test_preprocessing_strict_fold_isolation(dataset_df):
    sanitized_df, _ = LeakageAuditor.audit_and_clean(dataset_df, "Class/ASD Traits")
    X = sanitized_df.drop(columns=["Class/ASD Traits"])

    preprocessor = ClinicalDataPreprocessor(scale_numerical=True)
    # Split into train and test
    X_train = X.iloc[:800]
    X_test = X.iloc[800:]

    # Fit strictly on train
    preprocessor.fit(X_train)
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)

    assert X_train_trans.shape[0] == 800
    assert X_test_trans.shape[0] == 254
    assert X_train_trans.shape[1] == X_test_trans.shape[1]
    assert len(preprocessor.get_feature_names_out()) == X_train_trans.shape[1]
    # No NaNs in transformed output
    assert not np.isnan(X_train_trans).any()
    assert not np.isnan(X_test_trans).any()


# =============================================================================
# 4. YOUDEN J STATISTIC DERIVATION TESTS
# =============================================================================

def test_youden_threshold_calculation():
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])

    res = compute_youden_threshold(y_true, y_prob)
    assert 0.4 < res["optimal_threshold"] <= 0.6
    assert res["youden_j"] == 1.0
    assert res["sensitivity_at_threshold"] == 1.0
    assert res["specificity_at_threshold"] == 1.0


# =============================================================================
# 5. MODEL A: CATBOOST (PAPER 1, 2024) TESTS
# =============================================================================

def test_catboost_paper_1_training_and_shap(dataset_df):
    sanitized_df, _ = LeakageAuditor.audit_and_clean(dataset_df, "Class/ASD Traits")
    X = sanitized_df.drop(columns=["Class/ASD Traits"])
    y = sanitized_df["Class/ASD Traits"].str.strip().str.lower().isin(["yes", "1"]).astype(int)

    X_train, X_test = X.iloc[:843], X.iloc[843:]
    y_train, y_test = y.iloc[:843], y.iloc[843:]

    trainer = CatBoostTrainer(iterations=60, depth=3, learning_rate=0.1, random_seed=42)
    results = trainer.train_and_evaluate(X_train, y_train, X_test, y_test)

    # 3-Fold CV
    assert results["cv_evaluation"]["folds"] == 3
    assert results["cv_evaluation"]["mean_roc_auc"] > 0.95

    # Youden threshold
    assert 0.1 <= results["youden_threshold"] <= 0.9

    # Test evaluation
    test_metrics = results["test_evaluation_youden_threshold"]
    assert test_metrics["roc_auc"] > 0.95
    assert test_metrics["sensitivity"] > 0.90
    assert test_metrics["specificity"] > 0.90

    # Genuine SHAP
    shap_summary = results["shap_summary"]
    assert len(shap_summary["top_features"]) > 0
    assert shap_summary["top_features"][0]["mean_abs_shap"] > 0.0


# =============================================================================
# 6. MODEL B: RANDOM FOREST (PAPER 2, 2022) TESTS
# =============================================================================

def test_random_forest_paper_2_training(dataset_df):
    sanitized_df, _ = LeakageAuditor.audit_and_clean(dataset_df, "Class/ASD Traits")
    X = sanitized_df.drop(columns=["Class/ASD Traits"])
    y = sanitized_df["Class/ASD Traits"].str.strip().str.lower().isin(["yes", "1"]).astype(int)

    X_train, X_test = X.iloc[:843], X.iloc[843:]
    y_train, y_test = y.iloc[:843], y.iloc[843:]

    trainer = RandomForestTrainer(n_estimators=50, max_depth=5, min_samples_split=4, random_seed=42)
    results = trainer.train_and_evaluate(X_train, y_train, X_test, y_test)

    assert results["cv_evaluation"]["mean_roc_auc"] > 0.90
    assert results["test_evaluation"]["roc_auc"] > 0.90
    assert results["test_evaluation"]["auprc"] > 0.90
    assert len(results["feature_importance"]) > 0


# =============================================================================
# 7. MODEL C: LASSO LOGISTIC REGRESSION (PAPER 2, 2022) TESTS
# =============================================================================

def test_lasso_logistic_paper_2_feature_selection(dataset_df):
    sanitized_df, _ = LeakageAuditor.audit_and_clean(dataset_df, "Class/ASD Traits")
    X = sanitized_df.drop(columns=["Class/ASD Traits"])
    y = sanitized_df["Class/ASD Traits"].str.strip().str.lower().isin(["yes", "1"]).astype(int)

    X_train, X_test = X.iloc[:843], X.iloc[843:]
    y_train, y_test = y.iloc[:843], y.iloc[843:]

    trainer = LassoLogisticRegressionTrainer(C=0.5, penalty="l1", solver="liblinear", random_seed=42)
    results = trainer.train_and_evaluate(X_train, y_train, X_test, y_test)

    assert results["cv_evaluation"]["mean_roc_auc"] > 0.90
    assert results["test_evaluation"]["roc_auc"] > 0.90
    # Verifies LASSO feature selection: non-zero coefficients
    assert 0 < results["lasso_selected_features_count"] <= results["total_initial_features"]
    assert len(results["lasso_selected_features"]) == results["lasso_selected_features_count"]


# =============================================================================
# 8. PREDICTION SERVICE & AGE GATING SAFEGUARD TESTS
# =============================================================================

def test_prediction_service_age_gating_safeguard():
    ps = ResearchPredictionService.get_instance()

    # Case A: Infant under 12 months (e.g. 8 months)
    infant_input = {
        "a1": 1, "a2": 1, "a3": 1, "a4": 1, "a5": 1, "a6": 1, "a7": 1, "a8": 1, "a9": 1, "a10": 1,
        "age_months": 8, "sex": "m"
    }
    infant_res = ps.predict_child(infant_input, model_name="catboost")
    assert infant_res["screening_status"] == "OBSERVATION_ONLY_UNDER_12M"
    assert infant_res["predicted_probability"] is None
    assert infant_res["is_calibrated"] is False
    assert infant_res["risk_tier"] == "OBSERVATION_ONLY_UNDER_12M"

    # Case B: Toddler (24 months) - High concern profile
    toddler_high = {
        "a1": 1, "a2": 1, "a3": 1, "a4": 1, "a5": 0, "a6": 1, "a7": 0, "a8": 1, "a9": 0, "a10": 1,
        "age_months": 24, "sex": "m", "ethnicity": "middle eastern", "jaundice": "yes",
        "family_mem_with_asd": "no", "who_completed_test": "family member"
    }
    toddler_res = ps.predict_child(toddler_high, model_name="catboost")
    assert toddler_res["screening_status"] == "COMPLETED"
    assert toddler_res["predicted_probability"] is not None
    assert toddler_res["predicted_probability"] >= 0.70
    assert toddler_res["risk_tier"] == "ELEVATED_TRIAGE_RECOMMENDED"
    assert toddler_res["is_calibrated"] is True
    assert toddler_res["explanation"]["method"].startswith("SHAP")
    assert len(toddler_res["explanation"]["positive_risk_drivers"]) > 0

    # Case C: Toddler - Typical profile
    toddler_low = {
        "a1": 0, "a2": 0, "a3": 0, "a4": 0, "a5": 0, "a6": 0, "a7": 0, "a8": 0, "a9": 0, "a10": 0,
        "age_months": 24, "sex": "f", "ethnicity": "White European", "jaundice": "no",
        "family_mem_with_asd": "no", "who_completed_test": "health care professional"
    }
    toddler_low_res = ps.predict_child(toddler_low, model_name="catboost")
    assert toddler_low_res["predicted_probability"] < 0.20
    assert toddler_low_res["risk_tier"] == "LOWER_PREDICTED_RISK"


# =============================================================================
# 9. FASTAPI ENDPOINTS INTEGRATION TESTS
# =============================================================================

def test_api_dataset_preview(client):
    res = client.get("/api/v1/ml/preview-dataset")
    assert res.status_code == 200
    data = res.json()
    assert data["row_count"] == 1054
    assert data["identified_target"] == "Class/ASD Traits"
    assert "Case_No" in data["target_leakage_audit"]["dropped_columns"]
    assert "Qchat-10-Score" in data["target_leakage_audit"]["dropped_columns"]


def test_api_training_status(client):
    res = client.get("/api/v1/ml/training-status")
    assert res.status_code == 200
    data = res.json()
    assert data["is_model_artifact_available"] is True
    model_keys = [m["key"] for m in data["models_available"]]
    assert "catboost" in model_keys
    assert "random_forest" in model_keys
    assert "lasso_logistic" in model_keys


def test_api_model_comparison(client):
    res = client.get("/api/v1/ml/models/comparison")
    assert res.status_code == 200
    data = res.json()
    assert "catboost" in data
    assert "random_forest" in data
    assert "lasso_logistic" in data
    assert data["catboost"]["youden_threshold"] > 0
    assert data["lasso_logistic"]["lasso_selected_features_count"] > 0


def test_api_explainability_endpoint(client):
    # CatBoost SHAP
    res_cb = client.get("/api/v1/ml/models/catboost/explainability")
    assert res_cb.status_code == 200
    data_cb = res_cb.json()
    assert data_cb["method"] == "SHAP (TreeExplainer)"
    assert len(data_cb["shap_summary"]["top_features"]) > 0

    # LASSO Coefficients
    res_lasso = client.get("/api/v1/ml/models/lasso_logistic/explainability")
    assert res_lasso.status_code == 200
    data_lasso = res_lasso.json()
    assert len(data_lasso["selected_features"]) > 0


def test_api_predict_endpoint(client):
    payload = {
        "a1": 1, "a2": 1, "a3": 1, "a4": 1, "a5": 0, "a6": 1, "a7": 0, "a8": 1, "a9": 0, "a10": 1,
        "age_months": 24, "sex": "m", "ethnicity": "middle eastern", "jaundice": "yes",
        "family_mem_with_asd": "no", "who_completed_test": "family member",
        "model_name": "catboost"
    }
    res = client.post("/api/v1/ml/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["screening_status"] == "COMPLETED"
    assert data["predicted_probability"] > 0.70
    assert data["risk_tier"] == "ELEVATED_TRIAGE_RECOMMENDED"
    assert "Youden" in data["threshold_label"]
    assert len(data["explanation"]["feature_importances"]) > 0

