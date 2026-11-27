from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles, get_current_user_optional
from app.schemas.screening import ScreeningCreate, ScreeningResponse
from app.services.screening_service import ScreeningService
from app.services.pdf_report_service import PdfReportService
from app.models.screening import ScreeningSession
from app.models.user import User

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Execute Multimodal Screening & Explainability Assessment (Administrator & Assessor Only)"
)
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
def create_screening(
    payload: ScreeningCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor"]))
):
    """
    Submits multimodal behavioral, visual ocular, and acoustic prosody data.
    Runs feature extraction, model inference (via chosen architecture),
    and SHAP / LIME explainability analysis.
    """
    return ScreeningService.create_screening_session(db, payload)

@router.get(
    "/",
    response_model=List[ScreeningResponse],
    summary="List Screening Sessions (Administrator, Assessor & Researcher)"
)
@router.get(
    "",
    response_model=List[ScreeningResponse],
    include_in_schema=False
)
def list_screenings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    return ScreeningService.list_screenings(db, skip=skip, limit=limit)

@router.get(
    "/{session_id}",
    summary="Get Full Screening Session with SHAP & LIME Visualizations (Administrator, Assessor & Researcher)"
)
def get_screening_detail(
    session_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    result = ScreeningService.get_screening_detail(db, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Screening session record not found.")
    return result


@router.get(
    "/{session_id}/pdf",
    summary="Download De-identified Screening Summary Report PDF"
)
def download_screening_pdf(
    session_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """
    Direct endpoint for downloading publication-grade screening summary report PDF.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Screening session record not found.")

    patient = session.patient
    if not patient:
        raise HTTPException(status_code=404, detail="Participant record not found.")
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
    anon_tag = patient.anonymized_id
    filename = f"screening_summary_{anon_tag}_{session.id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
