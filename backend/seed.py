import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from app.core.database import SessionLocal, init_db
from app.services.patient_service import PatientService
from app.schemas.patient import PatientCreate
from app.services.screening_service import ScreeningService
from app.schemas.screening import (
    ScreeningCreate,
    BehavioralInput,
    VisualGazeInput,
    AcousticProsodyInput
)

def seed_sample_data():
    init_db()
    db = SessionLocal()

    try:
        # Check if patients already exist
        existing = PatientService.list_patients(db, limit=5)
        if existing:
            print(f"Database already contains {len(existing)} patients.")
            return

        # 1. Patient 1 (Toddler, 32 months)
        p1 = PatientService.create_patient(
            db,
            PatientCreate(
                anonymized_id="NS-2026-A101",
                age_months=32,
                biological_sex="male",
                referral_source="Developmental Pediatrics Clinic",
                clinical_notes="Parental concern regarding reduced eye contact and speech delay."
            )
        )
        print(f"Created patient {p1.anonymized_id}")

        # 2. Patient 2 (Preschooler, 48 months)
        p2 = PatientService.create_patient(
            db,
            PatientCreate(
                anonymized_id="NS-2026-B204",
                age_months=48,
                biological_sex="female",
                referral_source="Child Psychological Assessment Center",
                clinical_notes="Sensory sensitivities observed at preschool; solitary play preference."
            )
        )
        print(f"Created patient {p2.anonymized_id}")

        # 3. Create baseline screening for Patient 1
        screening_in = ScreeningCreate(
            patient_id=p1.id,
            preferred_model="random_forest",
            behavioral=BehavioralInput(
                social_smile_reciprocity=1,
                name_call_orientation=1,
                pointing_proto_declarative=1,
                pretend_play_engagement=1,
                repetitive_motor_mannerisms=0,
                monotropic_focus_intensity=1,
                gaze_alternation_dyadic=1,
                sensory_hypersensitivity=0,
                peer_social_interest=1,
                gestural_communication=1,
                response_latency_mean_sec=3.2
            ),
            visual_gaze=VisualGazeInput(
                fixation_count=36,
                mean_fixation_duration_ms=310.0,
                social_roi_dwell_percentage=45.0,
                joint_attention_latency_ms=880.0,
                saccade_mean_amplitude_deg=6.5,
                atypical_scanpath_entropy=0.62
            ),
            acoustic_prosody=AcousticProsodyInput(
                fundamental_freq_f0_mean_hz=255.0,
                f0_pitch_variability_stdev_hz=22.0,
                vocal_jitter_percent=1.65,
                vocal_shimmer_db=0.55,
                pause_to_speech_ratio=0.42,
                formant_dispersion_hz=1080.0,
                speech_rate_syllables_sec=2.6
            )
        )
        res = ScreeningService.create_screening_session(db, screening_in)
        print(f"Created baseline screening session {res['session'].id}")

        print("✅ Sample research data seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_sample_data()
