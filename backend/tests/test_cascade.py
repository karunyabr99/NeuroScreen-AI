import sys
import uuid
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

from app.core.database import Base, SessionLocal, init_db
from app.models.patient import Patient
from app.models.screening import ScreeningSession, ModalityFeature, ExplainabilityRecord
from app.services.patient_service import PatientService
from app.schemas.patient import PatientCreate
from app.services.screening_service import ScreeningService
from app.schemas.screening import ScreeningCreate, BehavioralInput

def test_sqlite_foreign_keys_and_cascade_deletion():
    """Verify that PRAGMA foreign_keys is ON and deleting a patient cascade deletes screenings, features, and explanations."""
    db = SessionLocal()
    try:
        # Check pragma
        fk_status = db.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk_status == 1, "PRAGMA foreign_keys must be enabled"

        # Clean up any leftover cascade test records
        for leftover in db.query(Patient).filter(Patient.anonymized_id.like("NS-CASCADE%")).all():
            db.delete(leftover)
        db.commit()

        # 1. Create a dedicated test patient
        patient = PatientService.create_patient(
            db,
            PatientCreate(
                anonymized_id=f"NS-CASCADE-{uuid.uuid4().hex[:6]}",
                age_months=24,
                biological_sex="other",
                referral_source="Cascade Verification Clinic",
                clinical_notes="Temporary record for cascade deletion verification",
                consent_status="granted"
            )
        )
        patient_id = patient.id

        # 2. Create a screening session with features and explanations
        screen_data = ScreeningService.create_screening_session(
            db,
            ScreeningCreate(
                patient_id=patient_id,
                preferred_model="random_forest",
                behavioral=BehavioralInput(
                    social_smile_reciprocity=1,
                    name_call_orientation=0,
                    pointing_proto_declarative=1
                )
            )
        )
        session_id = screen_data["session"].id

        # Verify child records exist in DB
        assert db.query(ScreeningSession).filter(ScreeningSession.id == session_id).count() == 1
        assert db.query(ModalityFeature).filter(ModalityFeature.session_id == session_id).count() >= 1
        assert db.query(ExplainabilityRecord).filter(ExplainabilityRecord.session_id == session_id).count() >= 1

        # 3. Delete the patient
        deleted = PatientService.delete_patient(db, patient_id)
        assert deleted is True

        # 4. Verify that child records are deleted
        assert db.query(Patient).filter(Patient.id == patient_id).first() is None
        assert db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first() is None
        assert db.query(ModalityFeature).filter(ModalityFeature.session_id == session_id).first() is None
        assert db.query(ExplainabilityRecord).filter(ExplainabilityRecord.session_id == session_id).first() is None

    finally:
        db.close()

