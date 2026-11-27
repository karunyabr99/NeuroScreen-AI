import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.screening import ScreeningSession
from app.models.audit import AuditLog
from ml_engine.registry.model_registry import ModelRegistry
from app.services.simulation_service import SimulationService
from app.schemas.simulation import SimulationInput

client = TestClient(app)

def get_auth_headers():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "assessor@neuroscreen.ai",
        "password": "Assessor@12345"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_simulation_scenarios_endpoint():
    """Verify scenarios endpoint returns all 5 canonical research scenarios."""
    headers = get_auth_headers()
    resp = client.get("/api/v1/simulation/scenarios", headers=headers)
    assert resp.status_code == 200
    scenarios = resp.json()
    assert len(scenarios) >= 5
    scenario_ids = [s["id"] for s in scenarios]
    assert "scenario_a" in scenario_ids
    assert "scenario_b" in scenario_ids
    assert "scenario_c" in scenario_ids
    assert "scenario_d" in scenario_ids
    assert "scenario_e" in scenario_ids
    
    # Verify metadata richness
    sc_a = next(s for s in scenarios if s["id"] == "scenario_a")
    assert "Typical" in sc_a["name"]
    assert "Normative" in sc_a["clinical_focus"]
    assert "inputs" in sc_a

def test_simulation_run_scenario_a_typical():
    """Test running simulation with typical developmental parameters."""
    headers = get_auth_headers()
    scenarios_resp = client.get("/api/v1/simulation/scenarios", headers=headers)
    sc_a = next(s for s in scenarios_resp.json() if s["id"] == "scenario_a")

    payload = sc_a["inputs"]
    resp = client.post("/api/v1/simulation/run", json=payload, headers=headers)
    assert resp.status_code == 201
    result = resp.json()

    # Structural and clinical verification
    assert "Stacking Ensemble" in result["model_name"]
    assert result["is_calibrated"] is True
    assert result["risk_tier"] == "LOW_LIKELIHOOD"
    assert 0.0 <= result["predicted_probability"] <= 0.25
    assert len(result["contributing_features"]) > 0
    assert "confidence_interval" in result
    assert result["confidence_interval"]["lower"] <= result["predicted_probability"] <= result["confidence_interval"]["upper"]
    assert "DEMONSTRATION DATA" in result["clinical_disclaimer"]

    # Verify session and patient identifiers
    assert result["session_id"] is not None
    assert result["patient_id"] is not None

def test_simulation_run_scenario_e_elevated():
    """Test running simulation with atypical developmental observations."""
    headers = get_auth_headers()
    scenarios_resp = client.get("/api/v1/simulation/scenarios", headers=headers)
    sc_e = next(s for s in scenarios_resp.json() if s["id"] == "scenario_e")

    payload = sc_e["inputs"]
    resp = client.post("/api/v1/simulation/run", json=payload, headers=headers)
    assert resp.status_code == 201
    result = resp.json()

    assert result["risk_tier"] == "ELEVATED_TRIAGE_RECOMMENDED"
    assert result["predicted_probability"] >= 0.75
    assert len(result["contributing_features"]) >= 3
    # Top contributing features should be flagged as elevated risk factors
    top_feature = result["contributing_features"][0]
    assert top_feature["direction"] == "risk_increasing"

def test_simulation_parameter_sensitivity():
    """Verify that shifting social and communication responses significantly alters the model probability."""
    headers = get_auth_headers()
    baseline_payload = {
        "scenario_name": "Sensitivity Baseline",
        "age_months": 36,
        "communication_development": 0.2,
        "social_interaction": 0.2,
        "response_to_name": 0.1,
        "eye_contact_observations": 0.2,
        "gesture_usage": 0.1,
        "repetitive_behaviours": 0.1,
        "play_patterns": 0.2,
        "developmental_milestones": 0.2,
        "caregiver_observations": 0.1,
        "is_incomplete": False
    }
    resp_baseline = client.post("/api/v1/simulation/run", json=baseline_payload, headers=headers)
    assert resp_baseline.status_code == 201
    prob_baseline = resp_baseline.json()["predicted_probability"]

    # Increase atypicality across social and communication domains
    atypical_payload = dict(baseline_payload)
    atypical_payload["scenario_name"] = "Sensitivity Atypical"
    atypical_payload["communication_development"] = 2.8
    atypical_payload["social_interaction"] = 2.8
    atypical_payload["response_to_name"] = 2.8
    atypical_payload["eye_contact_observations"] = 2.7
    atypical_payload["gesture_usage"] = 2.6

    resp_atypical = client.post("/api/v1/simulation/run", json=atypical_payload, headers=headers)
    assert resp_atypical.status_code == 201
    prob_atypical = resp_atypical.json()["predicted_probability"]

    # Verify meaningful probability shift
    assert prob_atypical > prob_baseline
    assert prob_atypical - prob_baseline > 0.40

def test_simulation_incomplete_modality_handling():
    """Verify that incomplete inputs (missing visual or acoustic cues) are safely handled via imputation."""
    headers = get_auth_headers()
    incomplete_payload = {
        "scenario_name": "Incomplete Modality Test",
        "age_months": 28,
        "communication_development": 2.5,
        "social_interaction": 2.2,
        "response_to_name": 2.6,
        "eye_contact_observations": 2.0,
        "gesture_usage": 2.1,
        "repetitive_behaviours": 2.4,
        "play_patterns": 2.0,
        "developmental_milestones": 2.3,
        "caregiver_observations": 2.5,
        "is_incomplete": True
    }
    resp = client.post("/api/v1/simulation/run", json=incomplete_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["risk_tier"] in ("MODERATE_MONITOR", "ELEVATED_TRIAGE_RECOMMENDED")
    # Verify missing modality features did not yield None
    assert not any(f["importance_value"] is None for f in data["contributing_features"])

def test_simulation_database_persistence_and_synthetic_flag():
    """Verify simulations are persisted in SQLite with is_synthetic=True and visible in history."""
    headers = get_auth_headers()
    db = SessionLocal()
    initial_synthetic_count = db.query(Patient).filter(Patient.is_synthetic == True).count()
    db.close()

    # Run a simulation
    payload = {
        "age_months": 42,
        "communication_development": 1.5,
        "social_interaction": 1.5,
        "response_to_name": 1.4,
        "eye_contact_observations": 1.3,
        "gesture_usage": 1.3,
        "repetitive_behaviours": 1.4,
        "play_patterns": 1.3,
        "developmental_milestones": 1.4,
        "caregiver_observations": 1.3,
        "scenario_name": "Test Suite Synthetic Session"
    }
    resp = client.post("/api/v1/simulation/run", json=payload, headers=headers)
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]

    db = SessionLocal()
    try:
        # Verify screening session persisted
        session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
        assert session is not None
        assert session.status == "completed"

        # Verify patient record created and flagged as synthetic
        patient = db.query(Patient).filter(Patient.id == session.patient_id).first()
        assert patient is not None
        assert patient.is_synthetic is True
        assert "Simulation Engine" in patient.referral_source

        # Verify synthetic count incremented
        new_synthetic_count = db.query(Patient).filter(Patient.is_synthetic == True).count()
        assert new_synthetic_count == initial_synthetic_count + 1

        # Verify audit log recorded
        audit = db.query(AuditLog).filter(
            AuditLog.action == "SIMULATION_RUN_EXECUTED"
        ).order_by(AuditLog.timestamp.desc()).first()
        assert audit is not None
        assert "Simulation" in audit.actor or "assessor" in audit.actor
    finally:
        db.close()

    # Verify history endpoint retrieves the session
    hist_resp = client.get("/api/v1/simulation/history", headers=headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert any(h["session_id"] == session_id for h in history)
