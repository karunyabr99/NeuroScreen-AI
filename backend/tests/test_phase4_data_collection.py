import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path
import numpy as np

backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

from app.main import app
from app.core.database import Base, get_db
from app.models.patient import Patient
from app.models.screening import ScreeningSession
from app.models.research_assessment import ResearchAssessment
from app.services.auth_service import AuthService
from ml_engine.training.train_pipeline import (
    DatasetValidator,
    ParticipantLevelSplitter,
    FeaturePreprocessor,
    TrainingPipeline
)

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

def get_auth_headers(role: str = "Assessor"):
    if role.lower() == "administrator":
        email = "admin@neuroscreen.ai"
        pwd = "Admin@12345"
    elif role.lower() == "researcher":
        email = "researcher@neuroscreen.ai"
        pwd = "Researcher@12345"
    else:
        email = "assessor@neuroscreen.ai"
        pwd = "Assessor@12345"
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ----------------- 1. Registration & Consent Validation -----------------

def test_participant_registration_and_consent_status():
    """Verify that a participant is registered with default pending consent and consent can be updated."""
    headers = get_auth_headers("Assessor")

    # 1. Register new participant with pending consent
    create_resp = client.post("/api/v1/patients/", json={
        "age_months": 32,
        "biological_sex": "female",
        "referral_source": "Autism Assessment Center",
        "consent_status": "pending",
        "ethics_approval_ref": "IRB-NS-2026-ETHICS-04"
    }, headers=headers)
    assert create_resp.status_code == 201
    p_data = create_resp.json()
    patient_id = p_data["id"]
    assert p_data["consent_status"] == "pending"

    # 2. Update consent to granted
    consent_resp = client.post(f"/api/v1/research/consent/{patient_id}", json={
        "consent_status": "granted",
        "assent_status": "not_applicable",
        "guardian_relationship": "Mother",
        "ethics_approval_ref": "IRB-NS-2026-ETHICS-04",
        "protocol_version": "NS-DATA-COLL-v1.0",
        "notes": "Guardian signed informed consent form."
    }, headers=headers)
    assert consent_resp.status_code == 200
    updated = consent_resp.json()
    assert updated["consent_status"] == "granted"
    assert updated["consent_date"] is not None

# ----------------- 2. Consent Hard Gate Blocking -----------------

def test_consent_gating_blocks_unconsented_intake():
    """Verify that real participant data intake is strictly blocked (HTTP 422) if consent is pending."""
    headers = get_auth_headers("Assessor")

    # 1. Create participant with pending consent
    p_resp = client.post("/api/v1/patients/", json={
        "age_months": 28,
        "biological_sex": "male",
        "referral_source": "Special Education Nursery",
        "consent_status": "pending"
    }, headers=headers)
    p_id = p_resp.json()["id"]

    # 2. Attempt to create screening session -> MUST BE BLOCKED
    screen_resp = client.post("/api/v1/screenings/", json={
        "patient_id": p_id,
        "behavioral": {"social_smile_reciprocity": 0, "name_call_orientation": 0, "pointing_proto_declarative": 0, "pretend_play_engagement": 0, "repetitive_motor_mannerisms": 1, "monotropic_focus_intensity": 1, "gaze_alternation_dyadic": 0, "sensory_hypersensitivity": 1, "peer_social_interest": 0, "gestural_communication": 0, "response_latency_mean_sec": 3.0}
    }, headers=headers)
    assert screen_resp.status_code == 422
    assert "Real participant screening data intake is blocked" in screen_resp.json()["detail"]

    # 3. Attempt to submit research assessment -> MUST BE BLOCKED
    assess_resp = client.post("/api/v1/research/assessments", json={
        "patient_id": p_id,
        "form_type": "caregiver",
        "assessor_role": "Caregiver / Parent",
        "developmental_history": {"walking_age_months": 15}
    }, headers=headers)
    assert assess_resp.status_code == 422
    assert "Real-world data collection is strictly blocked" in assess_resp.json()["detail"]

# ----------------- 3. Consent Withdrawal Handling -----------------

def test_consent_withdrawal_blocks_future_intake():
    """Verify that withdrawing consent marks status as withdrawn and prevents subsequent intakes."""
    headers = get_auth_headers("Assessor")

    # 1. Register & grant consent
    p_resp = client.post("/api/v1/patients/", json={
        "age_months": 36,
        "biological_sex": "male",
        "referral_source": "Pediatric Clinic",
        "consent_status": "granted"
    }, headers=headers)
    p_id = p_resp.json()["id"]

    # 2. Withdraw consent
    w_resp = client.post(f"/api/v1/research/consent/{p_id}/withdraw?reason=Guardian+withdrew+study+participation", headers=headers)
    assert w_resp.status_code == 200
    withdrawn_data = w_resp.json()
    assert withdrawn_data["consent_status"] == "withdrawn"
    assert withdrawn_data["consent_withdrawn_at"] is not None

    # 3. Subsequent screening attempt must be blocked
    screen_resp = client.post("/api/v1/screenings/", json={
        "patient_id": p_id,
        "behavioral": {"social_smile_reciprocity": 1, "name_call_orientation": 1, "pointing_proto_declarative": 1, "pretend_play_engagement": 1, "repetitive_motor_mannerisms": 0, "monotropic_focus_intensity": 0, "gaze_alternation_dyadic": 1, "sensory_hypersensitivity": 0, "peer_social_interest": 1, "gestural_communication": 1, "response_latency_mean_sec": 1.0}
    }, headers=headers)
    assert screen_resp.status_code == 422

# ----------------- 4. Multi-Informant Assessment Forms -----------------

def test_multi_informant_assessment_submission_and_caveats():
    """Verify Caregiver, Teacher, and Professional forms with caregiver concern safeguards and webcam caveats."""
    headers = get_auth_headers("Assessor")

    # Create consented participant
    p_resp = client.post("/api/v1/patients/", json={
        "age_months": 30,
        "biological_sex": "female",
        "referral_source": "Early Intervention Unit",
        "consent_status": "granted"
    }, headers=headers)
    p_id = p_resp.json()["id"]

    # 1. Submit Caregiver Form
    c_resp = client.post("/api/v1/research/assessments", json={
        "patient_id": p_id,
        "form_type": "caregiver",
        "assessor_role": "Caregiver / Parent",
        "developmental_history": {"walking_age_months": 13, "language_regression": False},
        "communication_milestones": {"first_words_age_months": 15, "phrase_speech_age_months": 24},
        "caregiver_concerns": {"concerns": "Preference for repetitive spinning"},
        "medical_family_history": {"passed_hearing_screen": True}
    }, headers=headers)
    assert c_resp.status_code == 201
    c_data = c_resp.json()
    # Verify caregiver concerns are strictly flagged as unconfirmed
    assert c_data["caregiver_concerns"]["verified_clinical_diagnosis"] is False
    assert "DO NOT constitute a confirmed clinical diagnosis" in c_data["caregiver_concerns"]["clinical_disclaimer"]

    # 2. Submit Professional Form with webcam sensor metadata
    prof_resp = client.post("/api/v1/research/assessments", json={
        "patient_id": p_id,
        "form_type": "professional",
        "assessor_role": "Qualified Clinical Specialist",
        "social_interaction_observations": {"joint_attention": 1},
        "multimodal_measurements": {
            "eye_tracking": {"sensor_type": "webcam_exploratory", "sampling_rate_hz": 30}
        }
    }, headers=headers)
    assert prof_resp.status_code == 201
    prof_data = prof_resp.json()
    # Verify webcam equivalence caveat is embedded
    assert "scientific_caveat" in prof_data["multimodal_measurements"]["eye_tracking"]
    assert "NOT scientifically or clinically equivalent" in prof_data["multimodal_measurements"]["eye_tracking"]["scientific_caveat"]

    # 3. Retrieve past assessments for participant
    list_resp = client.get(f"/api/v1/research/assessments/patient/{p_id}", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2

# ----------------- 5. Dataset Overview & Duplicates -----------------

def test_dataset_overview_and_duplicate_detection():
    """Verify dataset metrics aggregation, modality coverage, and profile collision detection."""
    headers = get_auth_headers("Researcher")

    # Create two duplicate profiles (same age, sex, clinic)
    admin_headers = get_auth_headers("Administrator")
    client.post("/api/v1/patients/", json={"age_months": 42, "biological_sex": "male", "referral_source": "Same Clinic Duplicate Test", "consent_status": "granted"}, headers=admin_headers)
    client.post("/api/v1/patients/", json={"age_months": 42, "biological_sex": "male", "referral_source": "Same Clinic Duplicate Test", "consent_status": "granted"}, headers=admin_headers)

    resp = client.get("/api/v1/research/dataset/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_participants"] >= 2
    assert "age_distribution" in data
    assert "modality_distribution" in data
    assert "missing_value_percentages" in data
    assert data["duplicate_count"] >= 1
    assert any("Same Clinic Duplicate Test" in d["duplicate_type"] or len(d["matching_ids"]) >= 2 for d in data["duplicates"])

# ----------------- 6. Anonymized CSV Export -----------------

def test_anonymized_csv_export_segregation():
    """Verify that CSV exports segregate real and synthetic records and exclude direct PII."""
    headers = get_auth_headers("Researcher")

    # Export real cohort
    resp = client.get("/api/v1/research/dataset/export-csv?export_type=real", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    csv_text = resp.text

    # Header check
    assert "anonymized_id,age_months,biological_sex,referral_source,is_synthetic,consent_status" in csv_text
    # Direct PII must NEVER be present
    assert "phone" not in csv_text.lower()
    assert "address" not in csv_text.lower()
    assert "email" not in csv_text.lower()

# ----------------- 7. ML Training Pipeline & Leakage-Free Splitting -----------------

def test_ml_training_validator_and_pipeline():
    """Verify DatasetValidator halts on small cohorts and TrainingPipeline executes without data leakage on valid benchmark data."""
    # 1. Test Validator on small cohort
    X_small = np.random.randn(10, 24)
    y_small = np.array([0, 1, 0, 1, 0, 0, 1, 0, 1, 0])
    pids_small = [f"P{i}" for i in range(10)]

    val = DatasetValidator.validate(X_small, y_small, pids_small)
    assert val.is_eligible is False
    assert any("below clinical training threshold" in r for r in val.reasons)

    # 2. Test Participant-Level Splitter for ZERO leakage
    X_synth = np.random.randn(60, 24)
    y_synth = (X_synth[:, 0] + X_synth[:, 1] > 0).astype(int)
    pids_synth = [f"P{i % 45}" for i in range(60)] # 45 unique participants across 60 samples

    splitter = ParticipantLevelSplitter(n_splits=5)
    splits = splitter.split(X_synth, y_synth, pids_synth)
    groups = np.array(pids_synth)

    for fold, (tr_idx, val_idx) in enumerate(splits):
        tr_pids = set(groups[tr_idx])
        val_pids = set(groups[val_idx])
        assert tr_pids.isdisjoint(val_pids), f"Participant leakage in fold {fold}!"

    # 3. Test Full TrainingPipeline
    pipeline = TrainingPipeline(n_splits=5)
    result = pipeline.run(X_synth, y_synth, pids_synth, export_checkpoints=False)
    assert result["status"] == "TRAINING_COMPLETED_SUCCESSFULLY"
    assert result["eligible"] is True
    assert "Random_Forest" in result["model_comparison"]
    assert "CatBoost" in result["model_comparison"]
    assert "Logistic_Regression" in result["model_comparison"]

    rf_metrics = result["model_comparison"]["Random_Forest"]
    assert "sensitivity" in rf_metrics
    assert "specificity" in rf_metrics
    assert "roc_auc" in rf_metrics
    assert "pr_auc" in rf_metrics

# ----------------- 8. Research Report PDF Generation -----------------

def test_research_report_pdf_generation():
    """Verify that vector PDF report is generated with correct title, headers, and disclaimers."""
    admin_headers = get_auth_headers("Administrator")

    # 1. Create consented patient and session
    p_resp = client.post("/api/v1/patients/", json={
        "age_months": 28,
        "biological_sex": "male",
        "referral_source": "PDF Test Clinic",
        "consent_status": "granted"
    }, headers=admin_headers)
    p_id = p_resp.json()["id"]

    s_resp = client.post("/api/v1/screenings/", json={
        "patient_id": p_id,
        "preferred_model": "random_forest",
        "behavioral": {"social_smile_reciprocity": 1, "name_call_orientation": 1, "pointing_proto_declarative": 1, "pretend_play_engagement": 1, "repetitive_motor_mannerisms": 0, "monotropic_focus_intensity": 0, "gaze_alternation_dyadic": 1, "sensory_hypersensitivity": 0, "peer_social_interest": 1, "gestural_communication": 1, "response_latency_mean_sec": 1.2}
    }, headers=admin_headers)
    s_id = s_resp.json()["session"]["id"]

    # 2. Download PDF
    pdf_resp = client.get(f"/api/v1/research/reports/{s_id}/pdf", headers=admin_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
    assert len(pdf_resp.content) > 5000 # Valid multi-page or structured PDF

# ----------------- 9. RBAC & Security Preservation -----------------

def test_rbac_security_preservation():
    """Verify that Researcher cannot grant consent or submit assessments, while Assessor can."""
    researcher_headers = get_auth_headers("Researcher")
    assessor_headers = get_auth_headers("Assessor")

    # 1. Create patient as Assessor
    p_resp = client.post("/api/v1/patients/", json={
        "age_months": 24,
        "biological_sex": "female",
        "referral_source": "RBAC Test Clinic",
        "consent_status": "pending"
    }, headers=assessor_headers)
    p_id = p_resp.json()["id"]

    # 2. Researcher cannot update consent (HTTP 403)
    r_consent = client.post(f"/api/v1/research/consent/{p_id}", json={"consent_status": "granted"}, headers=researcher_headers)
    assert r_consent.status_code == 403

    # 3. Researcher cannot submit assessment (HTTP 403)
    r_assess = client.post("/api/v1/research/assessments", json={"patient_id": p_id, "form_type": "caregiver", "assessor_role": "Caregiver"}, headers=researcher_headers)
    assert r_assess.status_code == 403

    # 4. Unauthenticated request rejected (HTTP 401)
    unauth_resp = client.get("/api/v1/research/dataset/overview")
    assert unauth_resp.status_code == 401
