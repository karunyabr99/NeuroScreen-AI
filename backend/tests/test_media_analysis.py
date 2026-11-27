import pytest
import io
import uuid
import tempfile
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

from app.main import app
from app.core.database import Base, get_db
from app.models.patient import Patient
from app.models.screening import ScreeningSession
from app.models.media import MediaUpload, MediaAnalysis
from app.models.audit import AuditLog
from app.services.auth_service import AuthService
from ml_engine.vision.video_analyzer import VideoBehavioralAnalyzer
from ml_engine.vision.image_analyzer import ImageQualityAndContextAnalyzer
from ml_engine.vision.model_evaluation import ParticipantLevelVisionDatasetSplitter

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
    email = f"{role.lower()}@neuroscreen.ai"
    pwd = f"{role.capitalize()}@12345"
    if role.lower() == "administrator":
        email = "admin@neuroscreen.ai"
        pwd = "Admin@12345"
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def create_sample_patient(consent_status: str = "granted") -> str:
    db = TestingSessionLocal()
    patient = Patient(
        id=str(uuid.uuid4()),
        anonymized_id=f"NS-MEDIA-{uuid.uuid4().hex[:6].upper()}",
        age_months=36,
        biological_sex="Male",
        referral_source="Clinic",
        clinical_notes="Social communication observations",
        guardian_relationship="Parent",
        consent_status=consent_status,
        protocol_version="v2.1",
        ethics_approval_ref="IRB-NS-2026-088",
        assessor_id="ASSESSOR-01",
        is_synthetic=False
    )
    db.add(patient)
    db.commit()
    patient_id = patient.id
    db.close()
    return patient_id

def create_test_image_bytes(width: int = 200, height: int = 200, color: tuple = (120, 140, 160)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def create_test_video_bytes() -> bytes:
    # A dummy binary blob representing minimal video bytes for file structure test
    return b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42" + (b"\x00" * 4096)


# --------------------------------------------------------------------------
# MODULE 1 & 2: Media Upload and Guardian Consent Gating
# --------------------------------------------------------------------------

def test_media_upload_requires_granted_consent():
    headers = get_auth_headers("Assessor")
    # Patient with pending consent
    patient_id = create_sample_patient(consent_status="pending")
    
    img_data = create_test_image_bytes()
    resp = client.post(
        "/api/v1/media/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "media_type": "image",
            "task_context": "structured_joint_attention",
            "media_training_authorized": "false"
        },
        files={"file": ("assessment_photo.jpg", img_data, "image/jpeg")}
    )
    assert resp.status_code == 403
    assert "consent is not verified" in resp.json()["detail"].lower()


def test_media_upload_succeeds_with_granted_consent():
    headers = get_auth_headers("Assessor")
    patient_id = create_sample_patient(consent_status="granted")
    img_data = create_test_image_bytes()

    resp = client.post(
        "/api/v1/media/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "media_type": "image",
            "task_context": "structured_tabletop_assessment",
            "media_training_authorized": "false"
        },
        files={"file": ("observation_session.jpg", img_data, "image/jpeg")}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["patient_id"] == patient_id
    assert data["media_type"] == "image"
    assert data["media_training_authorized"] is False
    assert data["task_context"] == "structured_tabletop_assessment"
    assert data["file_size_bytes"] > 0
    return data["id"], patient_id


def test_media_upload_rejects_invalid_file_format():
    headers = get_auth_headers("Assessor")
    patient_id = create_sample_patient(consent_status="granted")

    resp = client.post(
        "/api/v1/media/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "media_type": "video",
            "task_context": "free_play"
        },
        files={"file": ("malicious_payload.exe", b"MZexecutabledata", "application/octet-stream")}
    )
    assert resp.status_code == 400
    assert "invalid video file extension" in resp.json()["detail"].lower()


def test_media_upload_requires_authentication():
    patient_id = create_sample_patient(consent_status="granted")
    img_data = create_test_image_bytes()
    resp = client.post(
        "/api/v1/media/upload",
        data={"patient_id": patient_id, "media_type": "image"},
        files={"file": ("test.jpg", img_data, "image/jpeg")}
    )
    assert resp.status_code == 401


# --------------------------------------------------------------------------
# MODULE 2: Observable Video Behavioral Analyzer & Safeguards
# --------------------------------------------------------------------------

def test_video_behavioral_analyzer_negative_constraints():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(create_test_video_bytes())
        temp_path = Path(f.name)

    try:
        results = VideoBehavioralAnalyzer.analyze_video(
            file_path=temp_path,
            task_context="structured_joint_attention"
        )
        assert results["status"] == "completed"
        safeguards = results["ethical_safeguards"]

        # Verify absolute negative constraints
        assert safeguards["facial_autism_inference_attempted"] is False
        assert safeguards["facial_appearance_or_attractiveness_evaluated"] is False
        assert safeguards["facial_emotion_recognition_used"] is False
        assert safeguards["autism_severity_percentage_generated"] is False
        assert safeguards["webcam_infrared_equivalence_claimed"] is False

        # Verify behavioral feature domains are present
        assert "movement_and_pose" in results
        assert "gesture_and_actions" in results
        assert "gaze_measurements" in results
        assert "joint_attention_observations" in results
        assert "repetitive_movements" in results
        assert "social_interaction_opportunities" in results
        
        # Verify clinical recommendation mandates direct evaluation
        assert "ADOS-2" in results["clinical_recommendation"] or "evaluation" in results["clinical_recommendation"].lower()
    finally:
        if temp_path.exists():
            temp_path.unlink()


# --------------------------------------------------------------------------
# MODULE 3: Image Quality & Context Analyzer & Ethical Refusal
# --------------------------------------------------------------------------

def test_image_analyzer_quality_and_ethical_refusal():
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img_data = create_test_image_bytes(width=300, height=300)
        f.write(img_data)
        temp_path = Path(f.name)

    try:
        results = ImageQualityAndContextAnalyzer.analyze_image(
            file_path=temp_path,
            task_context="structured_tabletop_assessment"
        )
        assert results["status"] == "completed"
        quality_metrics = results["image_quality_and_context"]
        assert "laplacian_variance_sharpness" in quality_metrics
        assert "lighting_status" in quality_metrics
        assert "data_quality_score" in results

        # Verify ethical refusal
        safeguards = results["ethical_safeguards"]
        assert safeguards["facial_autism_inference_attempted"] is False
        assert safeguards["photographic_autism_classification_performed"] is False
        assert safeguards["diagnostic_severity_score_generated"] is False
        assert "STRICT CLINICAL SAFEGUARD" in safeguards["non_diagnostic_photograph_disclaimer"]
    finally:
        if temp_path.exists():
            temp_path.unlink()


# --------------------------------------------------------------------------
# MODULE 4: Authenticated Media Streaming & Consent Withdrawal Quarantining
# --------------------------------------------------------------------------

def test_authenticated_streaming_and_quarantine_on_withdrawal():
    headers = get_auth_headers("Assessor")
    patient_id = create_sample_patient(consent_status="granted")
    img_data = create_test_image_bytes()

    upload_resp = client.post(
        "/api/v1/media/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "media_type": "image",
            "task_context": "free_play"
        },
        files={"file": ("play_session.jpg", img_data, "image/jpeg")}
    )
    media_id = upload_resp.json()["id"]

    # 1. Successful stream with valid token
    stream_resp = client.get(f"/api/v1/media/{media_id}/stream", headers=headers)
    assert stream_resp.status_code == 200
    assert stream_resp.headers["x-content-type-options"] == "nosniff"

    # 2. Unauthenticated stream rejected
    unauth_resp = client.get(f"/api/v1/media/{media_id}/stream")
    assert unauth_resp.status_code == 401

    # 3. Guardian withdraws consent -> Stream immediately blocked/quarantined
    db = TestingSessionLocal()
    pat = db.query(Patient).filter(Patient.id == patient_id).first()
    pat.consent_status = "withdrawn"
    db.commit()
    db.close()

    quarantined_resp = client.get(f"/api/v1/media/{media_id}/stream", headers=headers)
    assert quarantined_resp.status_code == 403
    assert "withdrawn" in quarantined_resp.json()["detail"].lower()


# --------------------------------------------------------------------------
# MODULE 5: CV Analysis Endpoint & Multimodal Screening Synthesis
# --------------------------------------------------------------------------

def test_media_analysis_and_multimodal_synthesis():
    headers = get_auth_headers("Assessor")
    patient_id = create_sample_patient(consent_status="granted")
    img_data = create_test_image_bytes()

    upload_resp = client.post(
        "/api/v1/media/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "media_type": "image",
            "task_context": "structured_joint_attention"
        },
        files={"file": ("test_run.jpg", img_data, "image/jpeg")}
    )
    media_id = upload_resp.json()["id"]

    # 1. Trigger CV Analysis
    analysis_resp = client.post(
        f"/api/v1/media/{media_id}/analyze",
        headers=headers,
        json={"task_context": "structured_joint_attention", "extract_repetitive_patterns": True}
    )
    assert analysis_resp.status_code == 200
    analysis = analysis_resp.json()
    assert analysis["pipeline_version"] == "cv-behavioral-v1.0"
    assert analysis["analysis_status"] == "completed"
    assert analysis["ethical_safeguards"]["facial_autism_inference_attempted"] is False

    # 2. Trigger Multimodal Video Screening Synthesis
    synth_resp = client.get(
        f"/api/v1/media/{media_id}/screening-synthesis",
        headers=headers
    )
    assert synth_resp.status_code == 200
    synth = synth_resp.json()
    assert synth["patient_id"] == patient_id
    assert "video_observable_features" in synth
    assert "developmental_milestones" in synth
    assert "caregiver_observations" in synth
    assert synth["caregiver_observations"]["is_confirmed_clinical_diagnosis"] is False
    assert "screening_support_category" in synth
    assert "mandatory_safeguard_disclaimer" in synth
    assert "percentage" not in synth["mandatory_safeguard_disclaimer"].lower() or "not" in synth["mandatory_safeguard_disclaimer"].lower()


# --------------------------------------------------------------------------
# MODULE 6: Secure Media Deletion & Audit Logging
# --------------------------------------------------------------------------

def test_secure_media_deletion_and_audit():
    headers = get_auth_headers("Administrator")
    patient_id = create_sample_patient(consent_status="granted")
    img_data = create_test_image_bytes()

    upload_resp = client.post(
        "/api/v1/media/upload",
        headers=headers,
        data={
            "patient_id": patient_id,
            "media_type": "image",
            "task_context": "free_play"
        },
        files={"file": ("delete_me.jpg", img_data, "image/jpeg")}
    )
    media_id = upload_resp.json()["id"]

    # Delete media
    del_resp = client.delete(f"/api/v1/media/{media_id}", headers=headers)
    assert del_resp.status_code == 200

    # Verify 404 on subsequent get
    get_resp = client.get(f"/api/v1/media/{media_id}", headers=headers)
    assert get_resp.status_code == 404

    # Verify audit log record
    db = TestingSessionLocal()
    audit_entries = db.query(AuditLog).all()
    actions = [a.action for a in audit_entries]
    assert "MEDIA_UPLOADED" in actions
    assert "MEDIA_DELETED" in actions
    db.close()


# --------------------------------------------------------------------------
# MODULE 7: Participant-Level ML Splitting & Leakage Prevention
# --------------------------------------------------------------------------

def test_participant_level_vision_dataset_splitter():
    # 50 samples across 10 unique participants
    participants = np.array([f"P{i // 5:02d}" for i in range(50)])
    features = np.random.randn(50, 8)
    labels = np.array([0 if i % 2 == 0 else 1 for i in range(50)])

    splitter = ParticipantLevelVisionDatasetSplitter()
    splits = splitter.split_by_participant(features, labels, participants, n_splits=5)

    assert len(splits) == 5
    for fold, (train_idx, test_idx) in enumerate(splits):
        train_p = set(participants[train_idx])
        test_p = set(participants[test_idx])
        # Zero participant overlap
        assert len(train_p.intersection(test_p)) == 0, f"Participant leakage in fold {fold}"

    # Evaluation metrics
    y_true = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    y_pred = np.array([1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0])
    y_prob = np.array([0.9, 0.1, 0.8, 0.4, 0.2, 0.85, 0.15, 0.6, 0.9, 0.1, 0.8, 0.2, 0.35, 0.1, 0.75, 0.05, 0.95, 0.2, 0.88, 0.12])

    metrics = splitter.evaluate_clinical_metrics(y_true, y_pred, y_prob, bootstrap_ci=True)
    assert "sensitivity" in metrics
    assert "specificity" in metrics
    assert "precision" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics
    assert "pr_auc" in metrics
    assert "brier_score" in metrics
    assert "confidence_intervals_95" in metrics
    assert len(metrics["confidence_intervals_95"]["sensitivity"]) == 2
