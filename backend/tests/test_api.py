import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path

# Add backend and root to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from app.main import app
from app.core.database import Base, get_db
from app.services.auth_service import AuthService

# In-memory test SQLite engine
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        AuthService.seed_default_users(db)
    finally:
        db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert data["ml_engine"]["registered_models_count"] >= 4

def test_feature_catalog():
    response = client.get("/api/v1/multimodal/features")
    assert response.status_code == 200
    features = response.json()
    assert len(features) == 24
    modalities = {f["modality"] for f in features}
    assert modalities == {"behavioral", "visual_gaze", "acoustic_prosody"}

def test_unauthenticated_requests_rejected():
    """Verify that protected patient and screening endpoints reject requests without token (401)."""
    resp1 = client.get("/api/v1/patients/")
    assert resp1.status_code == 401
    assert "Authentication required" in resp1.json()["detail"]

    resp2 = client.post("/api/v1/patients/", json={"age_months": 24, "biological_sex": "male"})
    assert resp2.status_code == 401

    resp3 = client.get("/api/v1/screenings/")
    assert resp3.status_code == 401

def test_patient_crud_and_screening_workflow_with_auth():
    """Verify complete authenticated clinical workflow and explainability suspension in uncalibrated mode."""
    # 1. Login as Assessor
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "assessor@neuroscreen.ai",
        "password": "Assessor@12345"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Patient
    patient_payload = {
        "age_months": 36,
        "biological_sex": "male",
        "referral_source": "Pediatric Neurodevelopmental Clinic",
        "clinical_notes": "Referred due to delayed expressive speech and reduced reciprocal gaze.",
        "consent_status": "granted"
    }
    resp = client.post("/api/v1/patients/", json=patient_payload, headers=headers)
    assert resp.status_code == 201
    patient_data = resp.json()
    patient_id = patient_data["id"]
    assert patient_data["anonymized_id"].startswith("NS-")

    # 3. Submit Multimodal Screening Session
    screening_payload = {
        "patient_id": patient_id,
        "preferred_model": "random_forest",
        "behavioral": {
            "social_smile_reciprocity": 1,
            "name_call_orientation": 1,
            "pointing_proto_declarative": 1,
            "pretend_play_engagement": 1,
            "repetitive_motor_mannerisms": 1,
            "monotropic_focus_intensity": 1,
            "gaze_alternation_dyadic": 1,
            "sensory_hypersensitivity": 1,
            "peer_social_interest": 1,
            "gestural_communication": 1,
            "response_latency_mean_sec": 3.8
        },
        "visual_gaze": {
            "fixation_count": 32,
            "mean_fixation_duration_ms": 320.0,
            "social_roi_dwell_percentage": 42.0,
            "joint_attention_latency_ms": 950.0,
            "saccade_mean_amplitude_deg": 6.2,
            "atypical_scanpath_entropy": 0.68
        },
        "acoustic_prosody": {
            "fundamental_freq_f0_mean_hz": 265.0,
            "f0_pitch_variability_stdev_hz": 18.5,
            "vocal_jitter_percent": 1.85,
            "vocal_shimmer_db": 0.62,
            "pause_to_speech_ratio": 0.48,
            "formant_dispersion_hz": 1050.0,
            "speech_rate_syllables_sec": 2.2
        }
    }
    screen_resp = client.post("/api/v1/screenings/", json=screening_payload, headers=headers)
    assert screen_resp.status_code == 201
    result = screen_resp.json()

    # Verify session fields
    session = result["session"]
    assert session["patient_id"] == patient_id
    assert session["status"] == "completed"
    assert "behavioral" in session["modalities_included"]
    assert "visual_gaze" in session["modalities_included"]
    assert "acoustic_prosody" in session["modalities_included"]

    # Verify explainability records
    explanations = result["explanations"]
    assert len(explanations) == 2
    shap_exp = next(e for e in explanations if e["method"] == "SHAP")
    lime_exp = next(e for e in explanations if e["method"] == "LIME")

    if session["is_calibrated"]:
        assert shap_exp["is_calibrated"] is True
        assert shap_exp["status"] in ("EXPLAINABILITY_ACTIVE_CALIBRATED", "SUCCESS")
        assert len(shap_exp["feature_importances"]) > 0
        assert lime_exp["is_calibrated"] is True
    else:
        assert shap_exp["status"] == "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED"
        assert shap_exp["feature_importances"] == [] # Empty array
        assert shap_exp["is_calibrated"] is False
        assert lime_exp["status"] == "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED"
        assert lime_exp["feature_importances"] == []

    # 4. Retrieve screening detail
    session_id = session["id"]
    detail_resp = client.get(f"/api/v1/screenings/{session_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["session"]["id"] == session_id
    assert len(detail_data["features"]) == 3
