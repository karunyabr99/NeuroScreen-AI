from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.patient import Patient
from app.models.screening import ScreeningSession, ModalityFeature, ExplainabilityRecord
from app.models.audit import AuditLog
from app.schemas.screening import ScreeningCreate
from app.services.ml_bridge import MLBridge
from app.core.config import settings

class ScreeningService:
    @staticmethod
    def create_screening_session(
        db: Session,
        obj_in: ScreeningCreate
    ) -> Dict[str, Any]:
        # 1. Validate patient exists
        patient = db.query(Patient).filter(Patient.id == obj_in.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient reference not found.")

        # 1b. Governance Gating: Block intake if consent not granted for real participants
        if not patient.is_synthetic and patient.consent_status != "granted":
            raise HTTPException(
                status_code=422,
                detail=f"Real participant screening data intake is blocked by research governance protocol. "
                       f"Participant consent status is '{patient.consent_status}'. "
                       f"Verified guardian informed consent and ethics approval are mandatory prior to data collection."
            )

        # 2. Extract and align multimodal features
        beh_dict = obj_in.behavioral.model_dump() if obj_in.behavioral else None
        vis_dict = obj_in.visual_gaze.model_dump() if obj_in.visual_gaze else None
        aud_dict = obj_in.acoustic_prosody.model_dump() if obj_in.acoustic_prosody else None

        feature_vector, modality_features, modalities_present = MLBridge.process_multimodal_inputs(
            behavioral=beh_dict,
            visual_gaze=vis_dict,
            acoustic_prosody=aud_dict
        )

        # 3. Model routing and age gating
        # Prepare toddler dictionary for Toddler Q-CHAT model
        toddler_dict = None
        if beh_dict:
            toddler_dict = {
                'A1': beh_dict.get('a1') if beh_dict.get('a1') is not None else beh_dict.get('name_call_orientation', 0),
                'A2': beh_dict.get('a2') if beh_dict.get('a2') is not None else beh_dict.get('gaze_alternation_dyadic', 0),
                'A3': beh_dict.get('a3') if beh_dict.get('a3') is not None else beh_dict.get('pointing_proto_declarative', 0),
                'A4': beh_dict.get('a4') if beh_dict.get('a4') is not None else beh_dict.get('pointing_proto_declarative', 0),
                'A5': beh_dict.get('a5') if beh_dict.get('a5') is not None else beh_dict.get('pretend_play_engagement', 0),
                'A6': beh_dict.get('a6') if beh_dict.get('a6') is not None else beh_dict.get('gaze_alternation_dyadic', 0),
                'A7': beh_dict.get('a7') if beh_dict.get('a7') is not None else beh_dict.get('social_smile_reciprocity', 0),
                'A8': beh_dict.get('a8') if beh_dict.get('a8') is not None else beh_dict.get('sensory_hypersensitivity', 0),
                'A9': beh_dict.get('a9') if beh_dict.get('a9') is not None else beh_dict.get('gestural_communication', 0),
                'A10': beh_dict.get('a10') if beh_dict.get('a10') is not None else beh_dict.get('repetitive_motor_mannerisms', 0),
                'Age_Mons': patient.age_months,
                'Sex': 'm' if 'm' in (patient.biological_sex or 'm').lower() else 'f',
                'Ethnicity': beh_dict.get('ethnicity', 'Others'),
                'Jaundice': beh_dict.get('jaundice', 'no'),
                'Family_mem_with_ASD': beh_dict.get('family_mem_with_asd', 'no'),
                'Who completed the test': beh_dict.get('who_completed_test', 'family member')
            }

        import math
        if patient.age_months < 12:
            preferred_model = "toddler_qchat"
            protocol_version = "v1.0-observation-only-under-12m"
        elif obj_in.preferred_model in ["catboost", "random_forest", "lasso_logistic"]:
            preferred_model = obj_in.preferred_model
            protocol_version = f"v1.0-research-{preferred_model}"
        elif 12 <= patient.age_months <= 36:
            preferred_model = obj_in.preferred_model or "toddler_qchat"
            protocol_version = "v1.0-toddler-qchat-calibrated"
        else:
            preferred_model = obj_in.preferred_model or "stacking_ensemble"
            protocol_version = "v1.0-multimodal-research"

        ml_eval = MLBridge.evaluate_screening(
            feature_vector=feature_vector,
            model_name=preferred_model,
            toddler_dict=toddler_dict,
            patient_age_months=patient.age_months
        )
        pred = ml_eval["prediction"]
        shap_exp = ml_eval["shap_explanation"]
        lime_exp = ml_eval["lime_explanation"]
        model_status = ml_eval["model_status"]

        # 4. Create ScreeningSession DB Record
        is_score_valid = pred.is_calibrated and not math.isnan(pred.predicted_probability)
        session = ScreeningSession(
            patient_id=patient.id,
            status="completed",
            protocol_version=protocol_version,
            composite_risk_score=pred.predicted_probability if is_score_valid else None,
            risk_tier=pred.risk_tier,
            confidence_interval=pred.confidence_interval if is_score_valid else None,
            model_version=f"{preferred_model}-{'calibrated' if pred.is_calibrated else 'observation-only' if patient.age_months < 12 else 'uncalibrated'}",
            is_calibrated=pred.is_calibrated,
            modalities_included=modalities_present,
            completed_at=datetime.utcnow()
        )
        db.add(session)
        db.flush() # Populate session.id

        # 5. Persist Modality Feature Records
        feature_records = []
        for mod_name, extracted_dict in modality_features.items():
            if mod_name in modalities_present:
                raw_source = (
                    beh_dict if mod_name == "behavioral"
                    else vis_dict if mod_name == "visual_gaze"
                    else aud_dict
                )
                mod_feat = ModalityFeature(
                    session_id=session.id,
                    modality_type=mod_name,
                    raw_metrics=raw_source or {},
                    extracted_features=extracted_dict,
                    quality_score=0.95
                )
                db.add(mod_feat)
                feature_records.append(mod_feat)

        # 6. Persist Explainability Records (both SHAP and LIME)
        shap_rec = ExplainabilityRecord(
            session_id=session.id,
            method="SHAP",
            base_value=shap_exp["base_value"],
            prediction_value=shap_exp["prediction_value"],
            feature_importances=shap_exp["feature_importances"],
            summary_narrative=shap_exp["summary_narrative"]
        )
        db.add(shap_rec)

        lime_rec = ExplainabilityRecord(
            session_id=session.id,
            method="LIME",
            base_value=lime_exp["base_value"],
            prediction_value=lime_exp["prediction_value"],
            feature_importances=lime_exp["feature_importances"],
            summary_narrative=lime_exp["summary_narrative"]
        )
        db.add(lime_rec)

        # 7. Audit log
        audit = AuditLog(
            action="SCREENING_SESSION_EXECUTED",
            actor="clinician",
            details={
                "session_id": session.id,
                "patient_anon_id": patient.anonymized_id,
                "model": preferred_model,
                "modalities": modalities_present,
                "is_calibrated": pred.is_calibrated,
                "risk_tier": pred.risk_tier
            }
        )
        db.add(audit)

        db.commit()
        db.refresh(session)

        # Build response payload
        shap_exp["id"] = shap_rec.id
        shap_exp["session_id"] = session.id
        shap_exp["created_at"] = shap_rec.created_at
        shap_exp["is_calibrated"] = pred.is_calibrated

        lime_exp["id"] = lime_rec.id
        lime_exp["session_id"] = session.id
        lime_exp["created_at"] = lime_rec.created_at
        lime_exp["is_calibrated"] = pred.is_calibrated

        return {
            "session": session,
            "features": feature_records,
            "explanations": [shap_exp, lime_exp],
            "model_status": model_status,
            "clinical_disclaimer": settings.CLINICAL_DISCLAIMER
        }

    @staticmethod
    def get_screening_detail(db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
        if not session:
            return None

        features = db.query(ModalityFeature).filter(ModalityFeature.session_id == session.id).all()
        explanations = db.query(ExplainabilityRecord).filter(ExplainabilityRecord.session_id == session.id).all()

        # Format explanation records
        formatted_explanations = []
        for exp in explanations:
            # Reconstruct modality breakdown
            mod_totals = {"behavioral": 0.0, "visual_gaze": 0.0, "acoustic_prosody": 0.0}
            for item in exp.feature_importances:
                mod = item.get("modality", "behavioral")
                if mod in mod_totals:
                    mod_totals[mod] += abs(float(item.get("importance_value", 0.0)))
            total = sum(mod_totals.values()) or 1.0
            breakdown = {k: round((v / total) * 100.0, 1) for k, v in mod_totals.items()}

            if session.risk_tier == "OBSERVATION_ONLY_UNDER_12M":
                exp_status = "OBSERVATION_ONLY_UNDER_12M"
                status_notice = "Screening recorded in observation-only mode (infants < 12 months). Q-CHAT statistical risk prediction suspended."
            elif session.is_calibrated and len(exp.feature_importances) > 0:
                exp_status = "EXPLAINABILITY_ACTIVE_CALIBRATED"
                status_notice = "Verified Calibrated Inference"
            else:
                exp_status = "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED"
                status_notice = "Uncalibrated Modular Interface: Checkpoint unmounted."

            formatted_explanations.append({
                "id": exp.id,
                "session_id": exp.session_id,
                "method": exp.method,
                "status": exp_status,
                "base_value": exp.base_value or 0.5,
                "prediction_value": exp.prediction_value or 0.5,
                "is_calibrated": session.is_calibrated,
                "calibration_status_notice": status_notice,
                "feature_importances": exp.feature_importances,
                "summary_narrative": exp.summary_narrative,
                "modality_breakdown": breakdown,
                "created_at": exp.created_at
            })

        # Model status
        model_name = session.model_version.split("-")[0] if session.model_version else "random_forest"
        model_status = MLBridge.evaluate_screening(
            feature_vector=MLBridge._fusion_pipeline.process_screening_inputs()[0],
            model_name=model_name
        )["model_status"]

        return {
            "session": session,
            "features": features,
            "explanations": formatted_explanations,
            "model_status": model_status,
            "clinical_disclaimer": settings.CLINICAL_DISCLAIMER
        }

    @staticmethod
    def list_screenings(db: Session, skip: int = 0, limit: int = 100) -> List[ScreeningSession]:
        return db.query(ScreeningSession).order_by(ScreeningSession.created_at.desc()).offset(skip).limit(limit).all()

