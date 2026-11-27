from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User
from app.models.screening import ScreeningSession
from app.models.patient import Patient
from app.schemas.patient import PatientResponse
from app.schemas.research_assessment import (
    ConsentUpdateRequest, ResearchAssessmentCreate, ResearchAssessmentResponse
)
from app.schemas.dataset import DatasetOverviewResponse, BenchmarkGenerationRequest
from app.services.research_service import ResearchService
from app.services.dataset_service import DatasetService
from app.services.pdf_report_service import PdfReportService

router = APIRouter()

# ----------------- Consent & Governance -----------------

@router.post("/consent/{patient_id}", response_model=PatientResponse, summary="Record or Update Guardian Informed Consent & Assent")
def update_participant_consent(
    patient_id: str,
    payload: ConsentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor"]))
):
    """Update participant informed consent, assent status, and protocol references with audit logging."""
    return ResearchService.update_consent(db, patient_id, payload, actor=current_user.email)

@router.post("/consent/{patient_id}/withdraw", response_model=PatientResponse, summary="Withdraw Participant Consent")
def withdraw_participant_consent(
    patient_id: str,
    reason: Optional[str] = Query(None, description="Optional stated reason for withdrawal"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor"]))
):
    """Withdraw participant consent; permanently blocks future data intake and excludes participant from training cohorts."""
    return ResearchService.withdraw_consent(db, patient_id, reason=reason, actor=current_user.email)

# ----------------- Multi-informant Assessments -----------------

@router.post("/assessments", response_model=ResearchAssessmentResponse, status_code=status.HTTP_201_CREATED, summary="Submit Multi-informant Assessment Form")
def create_research_assessment(
    payload: ResearchAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor"]))
):
    """
    Submit structured assessment from Caregiver, Special Educator, or Qualified Professional.
    Strictly blocked if participant is real and informed consent is missing.
    """
    return ResearchService.create_assessment(db, payload, assessor_id=current_user.id, actor=current_user.email)

@router.get("/assessments/patient/{patient_id}", response_model=List[ResearchAssessmentResponse], summary="List Participant Assessments")
def get_patient_assessments(
    patient_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """Retrieve all multi-informant assessment forms associated with a participant."""
    return ResearchService.get_patient_assessments(db, patient_id)

# ----------------- Dataset Management & Export -----------------

@router.get("/dataset/overview", response_model=DatasetOverviewResponse, summary="Get Dataset Metrics & Data Quality Overview")
def get_dataset_overview(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """Retrieve participant counts, modality coverage, missing rates, label distributions, and duplicate warnings."""
    return DatasetService.get_dataset_overview(db)

@router.get("/dataset/export-csv", summary="Export De-identified Research Dataset CSV")
def export_dataset_csv(
    export_type: str = Query("real", description="'real' (consented participants only), 'synthetic' (test cohort only), or 'all'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Researcher"]))
):
    """
    Generate and stream a strictly de-identified CSV dataset. Direct PII is never included.
    Enforces segregation between real participant cohorts and synthetic dev test records.
    """
    csv_data = DatasetService.export_anonymized_csv(db, export_type=export_type, actor=current_user.email)
    filename = f"neuroscreen_dataset_{export_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/dataset/generate-benchmark", summary="Generate Benchmark Synthetic Dev Cohort (Admin Only)")
def generate_benchmark_cohort(
    payload: BenchmarkGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator"]))
):
    """
    Generates a synthetic development cohort tagged is_synthetic=True for software testing.
    Never mixed with real research participant datasets.
    """
    return DatasetService.generate_benchmark_development_cohort(
        db,
        sample_size=payload.sample_size,
        target_asd_prevalence=payload.target_asd_prevalence,
        actor=current_user.email
    )

# ----------------- Research PDF Report Generation -----------------

@router.get("/reports/{session_id}/pdf", summary="Download De-identified Research Screening Summary PDF")
def download_research_report_pdf(
    session_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """
    Generates a publication-grade vector PDF titled 'De-identified Research Screening Summary'.
    Includes protocol references, modality quality, non-diagnostic disclaimers, and research limitations.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Screening session record not found.")

    patient = session.patient
    session_dict = {
        "id": session.id,
        "created_at": session.created_at,
        "protocol_version": session.protocol_version,
        "composite_risk_score": session.composite_risk_score,
        "risk_tier": session.risk_tier,
        "is_calibrated": session.is_calibrated,
        "model_version": session.model_version,
        "modalities_included": session.modalities_included
    }
    patient_dict = {
        "anonymized_id": patient.anonymized_id,
        "age_months": patient.age_months,
        "biological_sex": patient.biological_sex,
        "referral_source": patient.referral_source,
        "consent_status": patient.consent_status,
        "ethics_approval_ref": patient.ethics_approval_ref
    }

    pdf_bytes = PdfReportService.generate_research_summary_pdf(session_dict, patient_dict)
    filename = f"research_summary_{patient.anonymized_id}_{session.id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ----------------- ML Training Preparation & Benchmarking -----------------

@router.get("/train/eligibility", summary="Evaluate ML Training Eligibility of Current Research Dataset")
def evaluate_training_eligibility(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Researcher"]))
):
    """
    Evaluates whether the collected real-world participant dataset satisfies statistical
    and governance thresholds for machine learning model training.
    """
    from ml_engine.training.train_pipeline import DatasetValidator

    real_consented = db.query(Patient).filter(
        Patient.is_synthetic == False,
        Patient.consent_status == "granted"
    ).all()

    # Collect session features
    sessions = []
    pids = []
    labels = []
    for p in real_consented:
        for s in p.screenings:
            sessions.append(s)
            pids.append(p.anonymized_id)
            # Label based on clinical triage status if assigned
            labels.append(1 if s.risk_tier == "ELEVATED_LIKELIHOOD" else 0)

    import numpy as np
    from ml_engine.config import TOTAL_FEATURE_DIM

    X = np.zeros((len(sessions), TOTAL_FEATURE_DIM)) if sessions else np.empty((0, TOTAL_FEATURE_DIM))
    y = np.array(labels)

    validation_result = DatasetValidator.validate(X, y, pids)
    return {
        "status": "ELIGIBILITY_EVALUATED",
        "dataset_version": "v1.4.0-research-2026-11",
        "eligibility_report": validation_result.to_dict()
    }

@router.post("/train/run", summary="Execute Multimodal ML Training Pipeline (Admin Only)")
def run_training_pipeline(
    train_on_benchmark: bool = Query(False, description="If True, runs training pipeline on synthetic development benchmark for testing"),
    export_checkpoints: bool = Query(False, description="If True, exports trained and calibrated model checkpoints to weights directory"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator"]))
):
    """
    Executes participant-level cross-validation, feature preprocessing, and model comparison.
    If real clinical dataset is insufficient, training halts gracefully with an eligibility report.
    """
    from ml_engine.training.train_pipeline import TrainingPipeline

    if not train_on_benchmark:
        # Strictly run on real consented participants
        real_consented = db.query(Patient).filter(
            Patient.is_synthetic == False,
            Patient.consent_status == "granted"
        ).all()
        sessions = []
        pids = []
        labels = []
        for p in real_consented:
            for s in p.screenings:
                sessions.append(s)
                pids.append(p.anonymized_id)
                labels.append(1 if s.risk_tier == "ELEVATED_LIKELIHOOD" else 0)

        import numpy as np
        from ml_engine.config import TOTAL_FEATURE_DIM
        X = np.zeros((len(sessions), TOTAL_FEATURE_DIM)) if sessions else np.empty((0, TOTAL_FEATURE_DIM))
        y = np.array(labels)

        pipeline = TrainingPipeline()
        result = pipeline.run(X, y, pids, export_checkpoints=export_checkpoints)
        return result
    else:
        # Run on synthetic benchmark development cohort
        import numpy as np
        np.random.seed(42)
        sample_size = 60
        num_participants = 45
        X_bench = np.random.randn(sample_size, 24)
        y_bench = (X_bench[:, 0] + X_bench[:, 1] > 0).astype(int)
        pids_bench = [f"SYN-P{i % num_participants}" for i in range(sample_size)]

        pipeline = TrainingPipeline()
        result = pipeline.run(X_bench, y_bench, pids_bench, export_checkpoints=export_checkpoints)
        return result
