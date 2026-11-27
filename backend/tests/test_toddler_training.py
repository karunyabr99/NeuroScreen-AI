"""
NeuroScreen AI - Test Suite for Toddler ASD Questionnaire Training & Live Video Modules
Tests:
1. Dataset audit and integrity checks (Thabtah 1,054 records, Polish Mendeley 252 records)
2. Trained model artifacts verification (model, preprocessor, metrics, metadata)
3. Model Registry registration and startup verification
4. Age-validation boundaries (under 12m observation-only, 12-36m toddler calibrated screener, >36m)
5. SHAP explainability integrity
6. End-to-end FastAPI screening session integration and PDF report generation
"""

import json
from pathlib import Path
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, get_db
from app.models.patient import Patient
from app.models.screening import ScreeningSession
from app.services.pdf_report_service import PdfReportService
from ml_engine.registry.model_registry import ModelRegistry
from ml_engine.models.toddler_questionnaire_model import ToddlerQuestionnaireModel
from ml_engine.config import WEIGHTS_DIR, DATASETS_DIR


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_toddler_datasets_exist_and_audited():
    """Verify primary and external validation datasets are present and audited."""
    primary_file = DATASETS_DIR / "toddler_autism_dataset_july_2018.csv"
    polish_file = DATASETS_DIR / "polish_toddler_qchat.sav"
    report_file = DATASETS_DIR / "toddler_dataset_inspection_report.json"
    
    assert primary_file.exists(), f"Primary toddler dataset missing at {primary_file}"
    assert polish_file.exists(), f"Polish toddler dataset missing at {polish_file}"
    assert report_file.exists(), f"Dataset inspection report missing at {report_file}"
    
    with open(report_file) as f:
        report = json.load(f)
        
    assert "primary_thabtah" in report
    assert report["primary_thabtah"]["total_records"] == 1054
    assert report["primary_thabtah"]["data_leakage_audit"]["strictly_thresholded_target"] is True
    
    assert "validation_polish" in report
    assert report["validation_polish"]["total_records"] == 252


def test_toddler_model_artifacts_and_metrics():
    """Verify all 4 required trained weight and metric artifacts exist in weights dir."""
    model_path = WEIGHTS_DIR / "toddler_questionnaire_model.joblib"
    preprocessor_path = WEIGHTS_DIR / "toddler_preprocessor.joblib"
    metrics_path = WEIGHTS_DIR / "toddler_training_metrics.json"
    metadata_path = WEIGHTS_DIR / "toddler_model_metadata.json"
    
    assert model_path.exists(), "toddler_questionnaire_model.joblib missing"
    assert preprocessor_path.exists(), "toddler_preprocessor.joblib missing"
    assert metrics_path.exists(), "toddler_training_metrics.json missing"
    assert metadata_path.exists(), "toddler_model_metadata.json missing"
    
    with open(metrics_path) as f:
        metrics = json.load(f)
        
    stack_metrics = metrics["test_evaluation"]["StackingEnsemble_Calibrated"]
    assert stack_metrics["roc_auc"] >= 0.95
    assert stack_metrics["sensitivity_recall"] >= 0.90
    assert stack_metrics["specificity"] >= 0.90
    
    # External Polish validation cohort verification
    assert "external_polish_validation" in metrics
    polish_metrics = metrics["external_polish_validation"]
    assert polish_metrics["total_participants"] == 252
    assert polish_metrics["roc_auc"] >= 0.90
    assert polish_metrics["accuracy"] >= 0.80
    assert polish_metrics["specificity"] >= 0.85


def test_model_registry_toddler_model():
    """Verify ModelRegistry instantiates and verifies toddler_qchat."""
    ModelRegistry.initialize()
    model = ModelRegistry.get_model("toddler_qchat")
    assert isinstance(model, ToddlerQuestionnaireModel)
    assert model.is_calibrated is True
    assert model.is_trained is True
    
    status = ModelRegistry.get_model_status("toddler_qchat")
    assert status["is_calibrated"] is True
    assert status["checkpoint_found"] is True
    assert "12-36 Months" in status["model_family"]


def test_age_gate_under_12_months_observation_only():
    """Verify infants under 12 months enter observation-only mode with probability withheld."""
    model = ModelRegistry.get_model("toddler_qchat")
    
    infant_profile = {
        "Age_Mons": 8,
        "Sex": "m",
        "A1": 1, "A2": 1, "A3": 1, "A4": 1, "A5": 1,
        "A6": 1, "A7": 1, "A8": 1, "A9": 1, "A10": 1
    }
    
    pred = model.predict_toddler(infant_profile)
    assert pred.risk_tier == "OBSERVATION_ONLY_UNDER_12M"
    assert pred.predicted_probability is None
    assert pred.is_calibrated is False
    assert "OBSERVATION_ONLY_UNDER_12M" in pred.status_message
    
    exp = model.explain_instance(infant_profile)
    assert exp["status"] == "OBSERVATION_ONLY_UNDER_12M"
    assert len(exp["feature_importances"]) == 0


def test_toddler_calibrated_predictions_12_to_36_months():
    """Verify toddlers 12-36 months produce calibrated probabilities and meaningful tiers."""
    model = ModelRegistry.get_model("toddler_qchat")
    
    # Low-risk toddler profile (typical milestones)
    low_risk = {
        "Age_Mons": 24, "Sex": "m", "Ethnicity": "White European",
        "A1": 0, "A2": 0, "A3": 0, "A4": 0, "A5": 0,
        "A6": 0, "A7": 0, "A8": 0, "A9": 0, "A10": 0
    }
    pred_low = model.predict_toddler(low_risk)
    assert pred_low.is_calibrated is True
    assert pred_low.risk_tier == "LOW"
    assert pred_low.predicted_probability < 0.20
    
    # High-risk toddler profile (multiple atypical flags)
    high_risk = {
        "Age_Mons": 24, "Sex": "m", "Ethnicity": "middle eastern",
        "A1": 1, "A2": 1, "A3": 1, "A4": 1, "A5": 1,
        "A6": 1, "A7": 1, "A8": 1, "A9": 1, "A10": 1
    }
    pred_high = model.predict_toddler(high_risk)
    assert pred_high.is_calibrated is True
    assert pred_high.risk_tier == "HIGH"
    assert pred_high.predicted_probability > 0.85
    
    # Explainability check
    exp = model.explain_instance(high_risk)
    assert exp["status"] == "EXPLAINABILITY_ACTIVE_CALIBRATED"
    assert len(exp["feature_importances"]) == 10
    assert any(x["importance_value"] > 0 for x in exp["feature_importances"])


def test_screening_api_end_to_end_infant_and_toddler(client, db):
    """Test full API screening flow for infant (<12m) and toddler (12-36m)."""
    # Login as Assessor
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "assessor@neuroscreen.ai",
        "password": "Assessor@12345"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Register infant (8 months)
    infant_resp = client.post("/api/v1/patients/", headers=headers, json={
        "age_months": 8,
        "biological_sex": "male",
        "referral_source": "Pediatric Clinic",
        "clinical_notes": "Well-child routine checkup.",
        "consent_status": "granted"
    })
    assert infant_resp.status_code == 201
    infant_id = infant_resp.json()["id"]
    
    # Execute infant screening
    infant_screen = client.post("/api/v1/screenings/", headers=headers, json={
        "patient_id": infant_id,
        "behavioral": {
            "a1": 0, "a2": 0, "a3": 0, "a4": 0, "a5": 0,
            "a6": 0, "a7": 0, "a8": 0, "a9": 0, "a10": 0
        }
    })
    assert infant_screen.status_code in [200, 201]
    infant_session = infant_screen.json()["session"]
    assert infant_session["risk_tier"] == "OBSERVATION_ONLY_UNDER_12M"
    assert infant_session["composite_risk_score"] is None
    assert infant_session["protocol_version"] == "v1.0-observation-only-under-12m"
    
    # 2. Register toddler (24 months)
    toddler_resp = client.post("/api/v1/patients/", headers=headers, json={
        "age_months": 24,
        "biological_sex": "female",
        "referral_source": "Parent Self-Referral",
        "clinical_notes": "Speech pacing evaluation.",
        "consent_status": "granted"
    })
    assert toddler_resp.status_code == 201
    toddler_id = toddler_resp.json()["id"]
    
    # Execute toddler screening
    toddler_screen = client.post("/api/v1/screenings/", headers=headers, json={
        "patient_id": toddler_id,
        "preferred_model": "toddler_qchat",
        "behavioral": {
            "a1": 1, "a2": 1, "a3": 0, "a4": 1, "a5": 1,
            "a6": 1, "a7": 0, "a8": 1, "a9": 0, "a10": 1,
            "ethnicity": "middle eastern",
            "jaundice": "yes",
            "family_mem_with_asd": "no"
        }
    })
    assert toddler_screen.status_code in [200, 201]
    toddler_session = toddler_screen.json()["session"]
    assert toddler_session["is_calibrated"] is True
    assert toddler_session["composite_risk_score"] is not None
    assert toddler_session["composite_risk_score"] > 0.0
    assert toddler_session["protocol_version"] == "v1.0-toddler-qchat-calibrated"
    
    # 3. Test PDF generation for both sessions
    pdf_infant = client.get(f"/api/v1/research/reports/{infant_session['id']}/pdf", headers=headers)
    assert pdf_infant.status_code == 200
    assert pdf_infant.headers["content-type"] == "application/pdf"
    assert len(pdf_infant.content) > 1000
    
    pdf_toddler = client.get(f"/api/v1/research/reports/{toddler_session['id']}/pdf", headers=headers)
    assert pdf_toddler.status_code == 200
    assert pdf_toddler.headers["content-type"] == "application/pdf"
    assert len(pdf_toddler.content) > 1000
