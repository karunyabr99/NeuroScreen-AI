from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.audit import AuditLog
from app.schemas.patient import PatientCreate, PatientUpdate
from app.core.security import generate_anonymized_id

class PatientService:
    @staticmethod
    def create_patient(db: Session, obj_in: PatientCreate) -> Patient:
        anon_id = obj_in.anonymized_id or generate_anonymized_id()
        consent_st = obj_in.consent_status or "pending"
        db_obj = Patient(
            anonymized_id=anon_id,
            age_months=obj_in.age_months,
            biological_sex=obj_in.biological_sex,
            referral_source=obj_in.referral_source,
            clinical_notes=obj_in.clinical_notes,
            is_synthetic=obj_in.is_synthetic,
            consent_status=consent_st,
            assent_status=obj_in.assent_status,
            guardian_relationship=obj_in.guardian_relationship,
            ethics_approval_ref=obj_in.ethics_approval_ref,
            protocol_version=obj_in.protocol_version,
            consent_date=obj_in.consent_date,
            assessor_id=obj_in.assessor_id
        )
        db.add(db_obj)
        
        # Audit entry
        audit = AuditLog(
            action="PATIENT_REGISTERED",
            actor="clinician",
            details={"patient_anon_id": anon_id, "age_months": obj_in.age_months}
        )
        db.add(audit)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_patient(db: Session, patient_id: str) -> Optional[Patient]:
        return db.query(Patient).filter(Patient.id == patient_id).first()

    @staticmethod
    def get_patient_by_anon_id(db: Session, anon_id: str) -> Optional[Patient]:
        return db.query(Patient).filter(Patient.anonymized_id == anon_id).first()

    @staticmethod
    def list_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
        return db.query(Patient).order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_patient(db: Session, patient_id: str, obj_in: PatientUpdate) -> Optional[Patient]:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(patient, key, value)
            
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def delete_patient(db: Session, patient_id: str) -> bool:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return False
        db.delete(patient)
        db.commit()
        return True

