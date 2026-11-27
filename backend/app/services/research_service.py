from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.patient import Patient
from app.models.research_assessment import ResearchAssessment
from app.models.audit import AuditLog
from app.schemas.research_assessment import ConsentUpdateRequest, ResearchAssessmentCreate

class ResearchService:
    @staticmethod
    def update_consent(
        db: Session,
        patient_id: str,
        obj_in: ConsentUpdateRequest,
        actor: str = "assessor"
    ) -> Patient:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Participant record not found.")

        old_status = patient.consent_status
        patient.consent_status = obj_in.consent_status
        patient.assent_status = obj_in.assent_status or patient.assent_status
        if obj_in.guardian_relationship:
            patient.guardian_relationship = obj_in.guardian_relationship
        if obj_in.ethics_approval_ref:
            patient.ethics_approval_ref = obj_in.ethics_approval_ref
        if obj_in.protocol_version:
            patient.protocol_version = obj_in.protocol_version

        if obj_in.consent_status == "granted" and not patient.consent_date:
            patient.consent_date = datetime.utcnow()
        elif obj_in.consent_status == "withdrawn":
            patient.consent_withdrawn_at = datetime.utcnow()

        # Audit trail
        audit = AuditLog(
            action="CONSENT_STATUS_UPDATE",
            actor=actor,
            details={
                "participant_id": patient.anonymized_id,
                "old_status": old_status,
                "new_status": patient.consent_status,
                "assent_status": patient.assent_status,
                "ethics_approval_ref": patient.ethics_approval_ref,
                "notes": obj_in.notes
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def withdraw_consent(
        db: Session,
        patient_id: str,
        reason: Optional[str] = None,
        actor: str = "assessor"
    ) -> Patient:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Participant record not found.")

        patient.consent_status = "withdrawn"
        patient.consent_withdrawn_at = datetime.utcnow()

        audit = AuditLog(
            action="CONSENT_REVOCATION_WITHDRAWAL",
            actor=actor,
            details={
                "participant_id": patient.anonymized_id,
                "reason": reason or "Caregiver / Participant requested consent withdrawal.",
                "withdrawn_at": patient.consent_withdrawn_at.isoformat()
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def create_assessment(
        db: Session,
        obj_in: ResearchAssessmentCreate,
        assessor_id: str,
        actor: str = "assessor"
    ) -> ResearchAssessment:
        patient = db.query(Patient).filter(Patient.id == obj_in.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Participant record not found.")

        # Hard Gate: Verify consent if real participant
        if not patient.is_synthetic and patient.consent_status != "granted":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Real-world data collection is strictly blocked by research governance protocol. "
                       f"Participant consent status is '{patient.consent_status}'. "
                       f"Institutional ethics approval and signed guardian informed consent are mandatory."
            )

        # Quality scoring
        quality_score = 1.0
        missing_domains = 0
        domains = [
            obj_in.developmental_history,
            obj_in.communication_milestones,
            obj_in.social_interaction_observations,
            obj_in.behavioral_characteristics,
            obj_in.repetitive_behaviors
        ]
        for d in domains:
            if not d:
                missing_domains += 1
        quality_score = max(0.2, 1.0 - (missing_domains * 0.15))
        quality_status = "complete" if missing_domains == 0 else "partial" if missing_domains <= 2 else "flagged"

        # Caregiver Concerns Governance Safeguard:
        # Caregiver concerns must never be treated as confirmed clinical diagnoses.
        caregiver_payload = obj_in.caregiver_concerns or {}
        if caregiver_payload:
            caregiver_payload["clinical_disclaimer"] = "Caregiver reported concerns are descriptive observational inputs and DO NOT constitute a confirmed clinical diagnosis."
            caregiver_payload["verified_clinical_diagnosis"] = False

        # Multimodal Sensor Metadata Caveat:
        # Explicitly distinguish webcam exploratory tracking from infrared eye tracking.
        multimodal_payload = obj_in.multimodal_measurements or {}
        if "eye_tracking" in multimodal_payload:
            sensor_type = multimodal_payload["eye_tracking"].get("sensor_type", "webcam_exploratory")
            if "webcam" in sensor_type.lower():
                multimodal_payload["eye_tracking"]["scientific_caveat"] = (
                    "Ordinary webcam visual tracking provides exploratory head-pose and coarse gaze estimates only. "
                    "It is NOT scientifically or clinically equivalent to dedicated high-speed infrared pupil-corneal reflection eye tracking."
                )

        assessment = ResearchAssessment(
            patient_id=patient.id,
            form_type=obj_in.form_type,
            assessor_id=assessor_id,
            assessor_role=obj_in.assessor_role,
            assessment_date=obj_in.assessment_date or datetime.utcnow(),
            protocol_version=patient.protocol_version,
            ethics_approval_ref=patient.ethics_approval_ref,
            is_synthetic=patient.is_synthetic or obj_in.is_synthetic,
            data_quality_status=quality_status,
            quality_score=quality_score,
            developmental_history=obj_in.developmental_history or {},
            communication_milestones=obj_in.communication_milestones or {},
            social_interaction_observations=obj_in.social_interaction_observations or {},
            behavioral_characteristics=obj_in.behavioral_characteristics or {},
            repetitive_behaviors=obj_in.repetitive_behaviors or {},
            caregiver_concerns=caregiver_payload,
            medical_family_history=obj_in.medical_family_history or {},
            multimodal_measurements=multimodal_payload,
            notes=obj_in.notes
        )

        db.add(assessment)

        # Audit log
        audit = AuditLog(
            action="RESEARCH_ASSESSMENT_SUBMITTED",
            actor=actor,
            details={
                "participant_id": patient.anonymized_id,
                "form_type": obj_in.form_type,
                "assessor_role": obj_in.assessor_role,
                "data_quality_status": quality_status,
                "quality_score": quality_score
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(assessment)
        return assessment

    @staticmethod
    def get_patient_assessments(db: Session, patient_id: str) -> List[ResearchAssessment]:
        return db.query(ResearchAssessment).filter(ResearchAssessment.patient_id == patient_id).order_by(ResearchAssessment.created_at.desc()).all()

