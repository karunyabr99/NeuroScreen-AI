import io
import csv
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.screening import ScreeningSession, ModalityFeature
from app.models.research_assessment import ResearchAssessment
from app.models.audit import AuditLog
from app.schemas.dataset import DatasetOverviewResponse, DuplicateRecord

DATASET_VERSION = "v1.4.0-research-2026-11"

class DatasetService:
    @staticmethod
    def get_dataset_overview(db: Session) -> DatasetOverviewResponse:
        all_patients = db.query(Patient).all()
        real_patients = [p for p in all_patients if not p.is_synthetic]
        synth_patients = [p for p in all_patients if p.is_synthetic]
        consented_real = [p for p in real_patients if p.consent_status == "granted"]
        withdrawn = [p for p in real_patients if p.consent_status == "withdrawn"]

        all_sessions = db.query(ScreeningSession).all()
        real_sessions = [s for s in all_sessions if s.patient and not s.patient.is_synthetic]
        synth_sessions = [s for s in all_sessions if s.patient and s.patient.is_synthetic]
        all_assessments = db.query(ResearchAssessment).count()

        # Age distribution
        age_bins = {"12-24m": 0, "25-36m": 0, "37-48m": 0, "49-60m": 0, "61m+": 0}
        for p in all_patients:
            if p.age_months <= 24:
                age_bins["12-24m"] += 1
            elif p.age_months <= 36:
                age_bins["25-36m"] += 1
            elif p.age_months <= 48:
                age_bins["37-48m"] += 1
            elif p.age_months <= 60:
                age_bins["49-60m"] += 1
            else:
                age_bins["61m+"] += 1

        # Modality coverage distribution
        modality_counts = defaultdict(int)
        features = db.query(ModalityFeature).all()
        total_sessions_count = len(all_sessions) or 1
        for f in features:
            if f.is_available:
                modality_counts[f.modality_type] += 1
        
        modality_distribution = {
            "behavioral": round((modality_counts["behavioral"] / total_sessions_count) * 100, 1),
            "visual_gaze": round((modality_counts["visual_gaze"] / total_sessions_count) * 100, 1),
            "acoustic_prosody": round((modality_counts["acoustic_prosody"] / total_sessions_count) * 100, 1),
            "developmental_milestones": round((all_assessments / total_sessions_count) * 100, 1)
        }

        # Missing value percentages
        missing_percentages = {
            "behavioral": round(max(0.0, 100.0 - modality_distribution["behavioral"]), 1),
            "visual_gaze": round(max(0.0, 100.0 - modality_distribution["visual_gaze"]), 1),
            "acoustic_prosody": round(max(0.0, 100.0 - modality_distribution["acoustic_prosody"]), 1),
            "developmental_milestones": round(max(0.0, 100.0 - modality_distribution["developmental_milestones"]), 1)
        }

        # Duplicate detection: profiles with exact (age_months, biological_sex, referral_source)
        seen_profiles = defaultdict(list)
        for p in all_patients:
            key = f"{p.age_months}_{p.biological_sex}_{p.referral_source.strip().lower()}"
            seen_profiles[key].append(p.anonymized_id)

        duplicates = []
        for key, ids in seen_profiles.items():
            if len(ids) > 1:
                parts = key.split("_")
                duplicates.append(DuplicateRecord(
                    anonymized_id=ids[0],
                    age_months=int(parts[0]),
                    biological_sex=parts[1],
                    duplicate_type="Exact Age-Sex-Referral Cohort Profile Collision",
                    matching_ids=ids
                ))

        # Label distribution
        label_dist = {"ELEVATED_LIKELIHOOD": 0, "MODERATE_LIKELIHOOD": 0, "LOW_TYPICAL": 0, "INCONCLUSIVE_UNCALIBRATED": 0}
        for s in all_sessions:
            if s.risk_tier == "ELEVATED_LIKELIHOOD":
                label_dist["ELEVATED_LIKELIHOOD"] += 1
            elif s.risk_tier == "MODERATE_LIKELIHOOD":
                label_dist["MODERATE_LIKELIHOOD"] += 1
            elif s.risk_tier == "LOW_TYPICAL":
                label_dist["LOW_TYPICAL"] += 1
            else:
                label_dist["INCONCLUSIVE_UNCALIBRATED"] += 1

        # Data quality warnings
        warnings = []
        if len(real_patients) < 50:
            warnings.append(
                f"Active real-world participant cohort (N={len(real_patients)}) is below minimum research training threshold (N=50). Supervised ML training remains suspended."
            )
        if missing_percentages["visual_gaze"] > 25.0:
            warnings.append("Visual gaze modality missing rate exceeds 25.0%. Infrared calibration or sensor availability should be verified.")
        if len(duplicates) > 0:
            warnings.append(f"Detected {len(duplicates)} potential participant profile collisions requiring deduplication review.")
        if len(withdrawn) > 0:
            warnings.append(f"{len(withdrawn)} participants have withdrawn consent; their records are excluded from training pipelines.")

        return DatasetOverviewResponse(
            total_participants=len(all_patients),
            real_participants=len(real_patients),
            synthetic_participants=len(synth_patients),
            consented_real_participants=len(consented_real),
            withdrawn_participants=len(withdrawn),
            total_sessions=len(all_sessions),
            real_sessions=len(real_sessions),
            synthetic_sessions=len(synth_sessions),
            total_research_assessments=all_assessments,
            age_distribution=age_bins,
            modality_distribution=modality_distribution,
            missing_value_percentages=missing_percentages,
            duplicate_count=len(duplicates),
            duplicates=duplicates,
            label_distribution=label_dist,
            data_quality_warnings=warnings,
            dataset_version=DATASET_VERSION
        )

    @staticmethod
    def export_anonymized_csv(db: Session, export_type: str = "real", actor: str = "researcher") -> str:
        """
        Exports de-identified CSV dataset.
        Options:
          - "real": Only genuine, consented participant records (never includes synthetic test data).
          - "synthetic": Only clearly marked synthetic test records.
          - "all": Includes all records with explicit 'is_synthetic' flag column.
        Strictly strips all direct PII (no names, telephone numbers, addresses, assessor names).
        """
        query = db.query(Patient)
        if export_type == "real":
            # Exclude synthetic and exclude withdrawn consent
            query = query.filter(Patient.is_synthetic == False, Patient.consent_status == "granted")
        elif export_type == "synthetic":
            query = query.filter(Patient.is_synthetic == True)
        
        patients = query.order_by(Patient.created_at.asc()).all()

        output = io.StringIO()
        fieldnames = [
            "anonymized_id",
            "age_months",
            "biological_sex",
            "referral_source",
            "is_synthetic",
            "consent_status",
            "protocol_version",
            "ethics_approval_ref",
            "session_id",
            "session_date",
            "composite_risk_score",
            "risk_tier",
            "is_calibrated",
            "modalities_included",
            "behavioral_feature_count",
            "visual_gaze_feature_count",
            "acoustic_prosody_feature_count",
            "data_quality_score"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for p in patients:
            sessions = p.screenings or []
            if not sessions:
                writer.writerow({
                    "anonymized_id": p.anonymized_id,
                    "age_months": p.age_months,
                    "biological_sex": p.biological_sex,
                    "referral_source": p.referral_source,
                    "is_synthetic": p.is_synthetic,
                    "consent_status": p.consent_status,
                    "protocol_version": p.protocol_version,
                    "ethics_approval_ref": p.ethics_approval_ref,
                    "session_id": "NONE",
                    "session_date": p.created_at.isoformat(),
                    "composite_risk_score": "",
                    "risk_tier": "NO_SESSION_RECORDED",
                    "is_calibrated": False,
                    "modalities_included": "[]",
                    "behavioral_feature_count": 0,
                    "visual_gaze_feature_count": 0,
                    "acoustic_prosody_feature_count": 0,
                    "data_quality_score": 1.0
                })
            else:
                for s in sessions:
                    beh_count = sum(1 for f in s.features if f.modality_type == "behavioral")
                    gaze_count = sum(1 for f in s.features if f.modality_type == "visual_gaze")
                    acoust_count = sum(1 for f in s.features if f.modality_type == "acoustic_prosody")
                    writer.writerow({
                        "anonymized_id": p.anonymized_id,
                        "age_months": p.age_months,
                        "biological_sex": p.biological_sex,
                        "referral_source": p.referral_source,
                        "is_synthetic": p.is_synthetic,
                        "consent_status": p.consent_status,
                        "protocol_version": p.protocol_version,
                        "ethics_approval_ref": p.ethics_approval_ref,
                        "session_id": s.id,
                        "session_date": s.created_at.isoformat(),
                        "composite_risk_score": s.composite_risk_score if s.composite_risk_score is not None else "",
                        "risk_tier": s.risk_tier,
                        "is_calibrated": s.is_calibrated,
                        "modalities_included": ",".join(s.modalities_included or []),
                        "behavioral_feature_count": beh_count,
                        "visual_gaze_feature_count": gaze_count,
                        "acoustic_prosody_feature_count": acoust_count,
                        "data_quality_score": round(sum(f.quality_score for f in s.features) / max(1, len(s.features)), 2)
                    })

        # Audit log export
        audit = AuditLog(
            action="DATASET_CSV_EXPORT",
            actor=actor,
            details={
                "export_type": export_type,
                "exported_records_count": len(patients),
                "dataset_version": DATASET_VERSION,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        db.add(audit)
        db.commit()

        return output.getvalue()

    @staticmethod
    def generate_benchmark_development_cohort(
        db: Session,
        sample_size: int = 60,
        target_asd_prevalence: float = 0.5,
        actor: str = "administrator"
    ) -> Dict[str, Any]:
        """
        Generates a synthetic development cohort strictly for offline software testing.
        Every record is permanently flagged with is_synthetic = True and SYN-NS prefix.
        Never mixed with real participant cohorts.
        """
        from app.services.patient_service import PatientService
        from app.schemas.patient import PatientCreate
        from app.services.screening_service import ScreeningService
        from app.schemas.screening import ScreeningCreate, BehavioralInput, VisualGazeInput, AcousticProsodyInput

        created_participants = []
        random.seed(42)

        for i in range(sample_size):
            is_positive = (random.random() < target_asd_prevalence)
            age = random.randint(18, 60)
            sex = random.choice(["male", "male", "female", "other"])
            syn_id = f"SYN-NS-2026-{1000 + i}"

            patient = Patient(
                anonymized_id=syn_id,
                age_months=age,
                biological_sex=sex,
                referral_source="Synthetic Development Testing Cohort",
                clinical_notes=f"Synthetic software verification profile ({'ASD-Aligned' if is_positive else 'Normative-Control'}).",
                is_synthetic=True,
                consent_status="granted",
                ethics_approval_ref="IRB-NS-DEV-BENCHMARK-ONLY",
                protocol_version="NS-SYNTHETIC-DEV-v1.0"
            )
            db.add(patient)
            db.flush()

            # Generate aligned multimodal session
            beh = BehavioralInput(
                social_smile_reciprocity=0 if is_positive else 1,
                name_call_orientation=0 if is_positive and random.random() < 0.8 else 1,
                pointing_proto_declarative=0 if is_positive else 1,
                pretend_play_engagement=0 if is_positive else 1,
                repetitive_motor_mannerisms=1 if is_positive else 0,
                monotropic_focus_intensity=1 if is_positive else 0,
                gaze_alternation_dyadic=0 if is_positive else 1,
                sensory_hypersensitivity=1 if is_positive else 0,
                peer_social_interest=0 if is_positive else 1,
                gestural_communication=0 if is_positive else 1,
                response_latency_mean_sec=round(3.5 if is_positive else 1.2, 2)
            )

            vis = VisualGazeInput(
                fixation_count=random.randint(15, 30) if is_positive else random.randint(35, 60),
                mean_fixation_duration_ms=round(random.uniform(200, 350) if is_positive else random.uniform(350, 500), 1),
                social_roi_dwell_percentage=round(random.uniform(25, 45) if is_positive else random.uniform(55, 80), 1),
                joint_attention_latency_ms=round(random.uniform(850, 1400) if is_positive else random.uniform(400, 750), 1),
                saccade_mean_amplitude_deg=round(random.uniform(5.5, 8.5), 1),
                atypical_scanpath_entropy=round(random.uniform(0.65, 0.90) if is_positive else random.uniform(0.35, 0.60), 2)
            )

            aud = AcousticProsodyInput(
                fundamental_freq_f0_mean_hz=round(random.uniform(240, 290) if is_positive else random.uniform(210, 250), 1),
                f0_pitch_variability_stdev_hz=round(random.uniform(12, 22), 1),
                vocal_jitter_percent=round(random.uniform(1.8, 3.2) if is_positive else random.uniform(0.6, 1.4), 2),
                vocal_shimmer_db=round(random.uniform(0.5, 1.1) if is_positive else random.uniform(0.2, 0.45), 2),
                pause_to_speech_ratio=round(random.uniform(0.35, 0.60) if is_positive else random.uniform(0.15, 0.30), 2),
                formant_dispersion_hz=round(random.uniform(1150, 1350), 1),
                speech_rate_syllables_sec=round(random.uniform(1.8, 2.9) if is_positive else random.uniform(3.2, 4.5), 2)
            )

            screening_data = ScreeningService.create_screening_session(
                db,
                ScreeningCreate(
                    patient_id=patient.id,
                    preferred_model="random_forest",
                    behavioral=beh,
                    visual_gaze=vis,
                    acoustic_prosody=aud
                )
            )
            created_participants.append(patient.anonymized_id)

        db.commit()

        # Audit
        audit = AuditLog(
            action="BENCHMARK_SYNTHETIC_COHORT_GENERATED",
            actor=actor,
            details={
                "sample_size": sample_size,
                "target_asd_prevalence": target_asd_prevalence,
                "created_synthetic_ids_count": len(created_participants)
            }
        )
        db.add(audit)
        db.commit()

        return {
            "status": "success",
            "message": f"Successfully generated {len(created_participants)} synthetic development records (tagged is_synthetic=True).",
            "synthetic_count": len(created_participants),
            "synthetic_sample_ids": created_participants[:5]
        }

