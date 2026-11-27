from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.screening import ScreeningCreate, ScreeningResponse
from app.services.screening_service import ScreeningService
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
