import uuid
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.patient import Patient
from app.models.screening import ScreeningSession, ModalityFeature, ExplainabilityRecord
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.simulation import SimulationInput, SimulationResultResponse, ContributingFeature
from app.services.ml_bridge import MLBridge
from app.core.config import settings

class SimulationService:
    @classmethod
    def get_preconfigured_scenarios(cls) -> List[Dict[str, Any]]:
        """
        Dynamic preconfigured clinical research test scenarios.
        Populates assessment observation inputs when selected.
        """
        return [
            {
                "id": "scenario_a",
                "name": "Scenario A: Typical Developmental Observations",
                "clinical_focus": "Normative Control / Age-Expected Social Communication",
                "description": "Child demonstrates spontaneous reciprocal smiling, direct flexible eye contact, proto-declarative pointing, and fluent prosody.",
                "inputs": {
                    "participant_id": "SIM-TYPICAL-01",
                    "scenario_name": "Scenario A: Typical Developmental Observations",
                    "age_months": 36,
                    "communication_development": 0.0,
                    "social_interaction": 0.0,
                    "response_to_name": 0.0,
                    "eye_contact_observations": 0.0,
                    "gesture_usage": 0.0,
                    "repetitive_behaviours": 0.0,
                    "play_patterns": 0.0,
                    "developmental_milestones": 0.0,
                    "caregiver_observations": 0.0,
                    "is_incomplete": False,
                    "notes": "Spontaneous pretend play and rich nonverbal gestures observed."
                }
            },
            {
                "id": "scenario_b",
                "name": "Scenario B: Communication-Related Observations",
                "clinical_focus": "Isolated Expressive Language & Prosodic Variation",
                "description": "Child exhibits notable speech and communication delays with monotone prosody, but maintains direct eye contact and shared enjoyment.",
                "inputs": {
                    "participant_id": "SIM-COMM-02",
                    "scenario_name": "Scenario B: Communication-Related Observations",
                    "age_months": 30,
                    "communication_development": 3.0,
                    "social_interaction": 0.5,
                    "response_to_name": 1.0,
                    "eye_contact_observations": 0.0,
                    "gesture_usage": 1.5,
                    "repetitive_behaviours": 0.0,
                    "play_patterns": 0.5,
                    "developmental_milestones": 1.5,
                    "caregiver_observations": 2.0,
                    "is_incomplete": False,
                    "notes": "Parent reports isolated expressive speech delay; joint attention and eye contact intact."
                }
            },
            {
                "id": "scenario_c",
                "name": "Scenario C: Social Interaction-Related Observations",
                "clinical_focus": "Dyadic Reciprocity & Joint Attention Variation",
                "description": "Child prefers solitary play, avoids sustained eye gaze, shows delayed orienting to name calls, but displays age-typical language grammar.",
                "inputs": {
                    "participant_id": "SIM-SOCIAL-03",
                    "scenario_name": "Scenario C: Social Interaction-Related Observations",
                    "age_months": 42,
                    "communication_development": 1.0,
                    "social_interaction": 3.0,
                    "response_to_name": 2.5,
                    "eye_contact_observations": 2.5,
                    "gesture_usage": 2.0,
                    "repetitive_behaviours": 0.5,
                    "play_patterns": 2.0,
                    "developmental_milestones": 0.5,
                    "caregiver_observations": 2.5,
                    "is_incomplete": False,
                    "notes": "Marked reduction in reciprocal smiling and dyadic gaze alternation."
                }
            },
            {
                "id": "scenario_d",
                "name": "Scenario D: Repetitive Behaviour-Related Observations",
                "clinical_focus": "Motor Stereotypies & Intense Monotropic Play",
                "description": "Child shows hand-flapping, whole-body rocking, sensory hyper-reactivity, and rigid alignment of miniature toys during unstructured stations.",
                "inputs": {
                    "participant_id": "SIM-STEREOTYPY-04",
                    "scenario_name": "Scenario D: Repetitive Behaviour-Related Observations",
                    "age_months": 38,
                    "communication_development": 1.0,
                    "social_interaction": 1.0,
                    "response_to_name": 1.0,
                    "eye_contact_observations": 1.0,
                    "gesture_usage": 1.0,
                    "repetitive_behaviours": 3.0,
                    "play_patterns": 3.0,
                    "developmental_milestones": 0.0,
                    "caregiver_observations": 3.0,
                    "is_incomplete": False,
                    "notes": "Intense perseveration on spinning wheels and adverse reaction to loud environmental sounds."
                }
            },
            {
                "id": "scenario_e",
                "name": "Scenario E: Mixed Developmental Observations",
                "clinical_focus": "Cross-Modal Multimodal Indicator Convergence",
                "description": "Child exhibits co-occurring atypicalities across social communication, reduced eye-contact dwell, repetitive motor mannerisms, and vocal pitch variations.",
                "inputs": {
                    "participant_id": "SIM-MIXED-05",
                    "scenario_name": "Scenario E: Mixed Developmental Observations",
                    "age_months": 34,
                    "communication_development": 2.5,
                    "social_interaction": 2.5,
                    "response_to_name": 2.5,
                    "eye_contact_observations": 2.5,
                    "gesture_usage": 2.5,
                    "repetitive_behaviours": 2.5,
                    "play_patterns": 2.5,
                    "developmental_milestones": 2.0,
                    "caregiver_observations": 3.0,
                    "is_incomplete": False,
                    "notes": "Multi-informant concerns across communication, social interaction, and sensory routines."
                }
            }
        ]

    @classmethod
    def map_assessment_to_features(
        cls,
        inputs: SimulationInput
    ) -> Tuple[np.ndarray, Dict[str, Dict[str, float]], List[str]]:
        """
        Maps the 9 child observation assessment dimensions to the standardized 24 multimodal feature schema.
        Handles incomplete/missing data cases gracefully.
        """
        feat = np.zeros(24)

        # 1. Behavioral Domain (Features 0 to 10)
        # social_smile_reciprocity
        feat[0] = 1.0 if inputs.social_interaction >= 2.0 else (0.5 if inputs.social_interaction >= 1.0 else 0.0)
        # name_call_orientation
        feat[1] = 1.0 if inputs.response_to_name >= 2.0 else (0.5 if inputs.response_to_name >= 1.0 else 0.0)
        # pointing_proto_declarative
        feat[2] = 1.0 if inputs.gesture_usage >= 2.0 else (0.5 if inputs.gesture_usage >= 1.0 else 0.0)
        # pretend_play_engagement
        feat[3] = 1.0 if inputs.play_patterns >= 2.0 else (0.5 if inputs.play_patterns >= 1.0 else 0.0)
        # repetitive_motor_mannerisms
        feat[4] = 1.0 if inputs.repetitive_behaviours >= 2.0 else (0.5 if inputs.repetitive_behaviours >= 1.0 else 0.0)
        # monotropic_focus_intensity
        feat[5] = 1.0 if (inputs.repetitive_behaviours >= 2.0 or inputs.play_patterns >= 2.0) else (0.5 if inputs.repetitive_behaviours >= 1.0 else 0.0)
        # gaze_alternation_dyadic
        feat[6] = 1.0 if inputs.eye_contact_observations >= 2.0 else (0.5 if inputs.eye_contact_observations >= 1.0 else 0.0)
        # sensory_hypersensitivity
        feat[7] = 1.0 if inputs.caregiver_observations >= 2.0 else (0.5 if inputs.repetitive_behaviours >= 1.0 else 0.0)
        # peer_social_interest
        feat[8] = 1.0 if inputs.social_interaction >= 2.0 else (0.5 if inputs.social_interaction >= 1.0 else 0.0)
        # gestural_communication
        feat[9] = 1.0 if inputs.gesture_usage >= 2.0 else (0.5 if inputs.communication_development >= 2.0 else 0.0)
        # response_latency_mean_sec
        feat[10] = round(1.4 + 0.9 * inputs.response_to_name, 2)

        # 2. Visual Gaze Domain (Features 11 to 16)
        if inputs.is_incomplete:
            # Simulate missing oculomotor recording
            feat[11:17] = np.nan
        else:
            feat[11] = round(52.0 - 9.5 * inputs.eye_contact_observations, 1)
            feat[12] = round(410.0 - 60.0 * inputs.eye_contact_observations, 1)
            feat[13] = round(78.0 - 15.0 * inputs.eye_contact_observations - 3.0 * inputs.social_interaction, 1)
            feat[14] = round(450.0 + 240.0 * inputs.response_to_name + 60.0 * inputs.social_interaction, 1)
            feat[15] = round(8.2 - 0.8 * inputs.eye_contact_observations, 1)
            feat[16] = round(0.38 + 0.14 * inputs.play_patterns + 0.05 * inputs.repetitive_behaviours, 2)

        # 3. Acoustic Prosody Domain (Features 17 to 23)
        feat[17] = round(230.0 + 16.0 * inputs.communication_development, 1)
        feat[18] = round(45.0 - 9.0 * inputs.communication_development, 1)
        feat[19] = round(0.80 + 0.55 * inputs.communication_development, 2)
        feat[20] = round(0.30 + 0.18 * inputs.communication_development, 2)
        feat[21] = round(0.24 + 0.10 * inputs.communication_development, 2)
        feat[22] = round(1150.0 + 60.0 * inputs.communication_development, 1)
        feat[23] = round(3.8 - 0.55 * inputs.communication_development, 2)

        modalities = ["behavioral", "acoustic_prosody"]
        if not inputs.is_incomplete:
            modalities.append("visual_gaze")

        modality_dicts = {
            "behavioral": {
                "social_smile_reciprocity": feat[0],
                "name_call_orientation": feat[1],
                "pointing_proto_declarative": feat[2],
                "pretend_play_engagement": feat[3],
                "repetitive_motor_mannerisms": feat[4],
                "monotropic_focus_intensity": feat[5],
                "gaze_alternation_dyadic": feat[6],
                "sensory_hypersensitivity": feat[7],
                "peer_social_interest": feat[8],
                "gestural_communication": feat[9],
                "response_latency_mean_sec": feat[10]
            },
            "visual_gaze": {
                "fixation_count": feat[11],
                "mean_fixation_duration_ms": feat[12],
                "social_roi_dwell_percentage": feat[13],
                "joint_attention_latency_ms": feat[14],
                "saccade_mean_amplitude_deg": feat[15],
                "atypical_scanpath_entropy": feat[16]
            } if not inputs.is_incomplete else {},
            "acoustic_prosody": {
                "fundamental_freq_f0_mean_hz": feat[17],
                "f0_pitch_variability_stdev_hz": feat[18],
                "vocal_jitter_percent": feat[19],
                "vocal_shimmer_db": feat[20],
                "pause_to_speech_ratio": feat[21],
                "formant_dispersion_hz": feat[22],
                "speech_rate_syllables_sec": feat[23]
            }
        }

        return feat, modality_dicts, modalities

    @classmethod
    def run_simulation(
        cls,
        db: Session,
        inputs: SimulationInput,
        current_user: User
    ) -> SimulationResultResponse:
        """
        Executes the full simulation pipeline:
        Inputs -> Preprocessing -> Stacking Ensemble Inference -> SHAP Explainability -> DB Persistence.
        """
        # 1. Generate or fetch synthetic participant record
        anon_id = inputs.participant_id or f"SIM-NS-{uuid.uuid4().hex[:6].upper()}"
        patient = db.query(Patient).filter(Patient.anonymized_id == anon_id).first()
        if not patient:
            patient = Patient(
                id=str(uuid.uuid4()),
                anonymized_id=anon_id,
                age_months=inputs.age_months,
                biological_sex="Unspecified",
                referral_source=f"Simulation Engine ({inputs.scenario_name or 'Custom'})",
                clinical_notes=inputs.notes or f"Synthetic simulation profile for {inputs.scenario_name}.",
                is_synthetic=True, # MANDATORY: Segregated from real ML training
                consent_status="granted",
                ethics_approval_ref="IRB-NS-SIMULATION-DEMO",
                protocol_version="NS-SIM-v1.0",
                assessor_id=str(current_user.id)
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        # 2. Map assessment inputs to feature vector
        feature_vector, modality_features, modalities_present = cls.map_assessment_to_features(inputs)

        # 3. Execute Stacking Ensemble Inference & SHAP Explainability via MLBridge
        ml_eval = MLBridge.evaluate_screening(feature_vector, model_name="stacking_ensemble")
        pred = ml_eval["prediction"]
        shap_exp = ml_eval["shap_explanation"]
        model_status = ml_eval["model_status"]

        # 4. Persist Simulation Screening Session
        session = ScreeningSession(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            status="completed",
            protocol_version="NS-SIM-STACKING-v1.0",
            composite_risk_score=pred.predicted_probability,
            risk_tier=pred.risk_tier,
            confidence_interval=pred.confidence_interval,
            model_version="stacking_ensemble-calibrated-v1.0",
            is_calibrated=True,
            modalities_included=modalities_present,
            completed_at=datetime.utcnow()
        )
        db.add(session)
        db.flush()

        # 5. Persist Modality Features
        for mod_name, f_dict in modality_features.items():
            if mod_name in modalities_present and f_dict:
                mod_feat = ModalityFeature(
                    id=str(uuid.uuid4()),
                    session_id=session.id,
                    modality_type=mod_name,
                    raw_metrics=f_dict,
                    extracted_features=f_dict,
                    quality_score=0.98 if not inputs.is_incomplete else 0.70,
                    quality_status="valid" if not inputs.is_incomplete else "incomplete_simulated",
                    is_available=True
                )
                db.add(mod_feat)

        # 6. Persist Explainability Record
        shap_rec = ExplainabilityRecord(
            id=str(uuid.uuid4()),
            session_id=session.id,
            method="SHAP",
            base_value=shap_exp.get("base_value", 0.32),
            prediction_value=pred.predicted_probability,
            feature_importances=shap_exp.get("feature_importances", []),
            summary_narrative=shap_exp.get("summary_narrative", "")
        )
        db.add(shap_rec)

        # 7. Audit Log
        audit = AuditLog(
            action="SIMULATION_RUN_EXECUTED",
            actor=f"{current_user.email} ({current_user.role})",
            details={
                "participant_id": anon_id,
                "scenario_name": inputs.scenario_name,
                "predicted_probability": pred.predicted_probability,
                "risk_tier": pred.risk_tier,
                "model": "Stacking Ensemble (RF + SVM + GB -> LR)"
            }
        )
        db.add(audit)
        db.commit()

        # Build contributing features for frontend
        raw_contribs = shap_exp.get("feature_importances", [])
        contributing_feats = [
            ContributingFeature(
                feature_name=f["feature_name"],
                display_name=f["display_name"],
                modality=f["modality"],
                feature_value=float(f.get("feature_value", 0.0)),
                importance_value=float(f.get("importance_value", 0.0)),
                direction=f.get("direction", "neutral"),
                clinical_note=f.get("clinical_note", "")
            )
            for f in raw_contribs[:10]
        ]
        pos_contribs = [c for c in contributing_feats if c.direction == "risk_increasing"][:5]
        neg_contribs = [c for c in contributing_feats if c.direction == "risk_decreasing"][:5]

        disclaimer = (
            "DEMONSTRATION DATA – NOT REAL CLINICAL DATA. "
            "NeuroScreen AI is an experimental clinical decision-support research instrument. "
            "Simulated screening estimates do NOT constitute a medical or psychological diagnosis. "
            "Comprehensive in-person multidisciplinary evaluation (e.g. ADOS-2, ADI-R) by licensed specialists is required."
        )

        return SimulationResultResponse(
            session_id=session.id,
            patient_id=patient.id,
            participant_id=patient.anonymized_id,
            scenario_name=inputs.scenario_name or "Custom Simulation",
            age_months=inputs.age_months,
            predicted_probability=pred.predicted_probability,
            risk_tier=pred.risk_tier,
            confidence_interval=pred.confidence_interval or {"lower": 0.0, "upper": 0.0},
            model_name="Stacking Ensemble Screener",
            model_architecture="Random Forest (Bagging) + SVM (RBF) + Gradient Boosting -> Logistic Regression Meta-Classifier",
            is_calibrated=True,
            contributing_features=contributing_feats,
            positive_contributions=pos_contribs,
            negative_contributions=neg_contribs,
            summary_narrative=shap_exp.get("summary_narrative", pred.status_message),
            is_synthetic_demonstration=True,
            clinical_disclaimer=disclaimer,
            created_at=session.created_at
        )

    @classmethod
    def get_simulation_history(cls, db: Session, limit: int = 25) -> List[Dict[str, Any]]:
        sessions = (
            db.query(ScreeningSession)
            .join(Patient)
            .filter(Patient.is_synthetic == True)
            .order_by(ScreeningSession.created_at.desc())
            .limit(limit)
            .all()
        )
        results = []
        for s in sessions:
            results.append({
                "session_id": s.id,
                "participant_id": s.patient.anonymized_id if s.patient else "UNKNOWN",
                "age_months": s.patient.age_months if s.patient else 0,
                "composite_risk_score": s.composite_risk_score,
                "risk_tier": s.risk_tier,
                "model_version": s.model_version,
                "created_at": s.created_at.isoformat()
            })
        return results

