from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User
from app.schemas.media import (
    MediaUploadResponse,
    MediaAnalysisResponse,
    MediaAnalysisTriggerRequest,
    MultimodalVideoScreeningResponse
)
from app.services.media_service import MediaService

router = APIRouter()

@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Child Video or Photograph (Administrator & Assessor Only)"
)
async def upload_child_media(
    patient_id: str = Form(..., description="De-identified participant UUID"),
    media_type: str = Form(..., description="'video' or 'image'"),
    task_context: str = Form(default="structured_joint_attention", description="Clinical activity context"),
    media_training_authorized: bool = Form(default=False, description="Separate explicit authorization for model development usage"),
    session_id: Optional[str] = Form(default=None, description="Screening session UUID"),
    file: UploadFile = File(..., description="Binary video or image file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor"]))
):
    """
    Secure intake endpoint for research participant video and image media.
    Requires verified guardian consent. Storage is private and non-public.
    """
    return MediaService.upload_media(
        db=db,
        patient_id=patient_id,
        file=file,
        media_type=media_type,
        task_context=task_context,
        media_training_authorized=media_training_authorized,
        session_id=session_id,
        current_user=current_user
    )


@router.get(
    "/patient/{patient_id}",
    response_model=List[MediaUploadResponse],
    summary="List Media for Participant (Authorized Roles)"
)
def list_patient_media(
    patient_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """Retrieves all media uploads associated with the specified participant."""
    return MediaService.get_patient_media(db=db, patient_id=patient_id)


@router.get(
    "/{media_id}",
    response_model=MediaUploadResponse,
    summary="Get Media Metadata & Analysis (Authorized Roles)"
)
def get_media_details(
    media_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """Retrieves metadata and current behavioral analysis results for a specific media upload."""
    return MediaService.get_media_by_id(db=db, media_id=media_id)


@router.get(
    "/{media_id}/stream",
    summary="Secure Authenticated Media Stream (Authorized Roles)"
)
def stream_media(
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """
    Streams media content directly through an authenticated gateway.
    Verifies caller credentials, RBAC permissions, and checks that participant
    guardian consent has not been withdrawn. Media is never exposed via static URLs.
    """
    return MediaService.stream_media(db=db, media_id=media_id, current_user=current_user)


@router.post(
    "/{media_id}/analyze",
    response_model=MediaAnalysisResponse,
    summary="Execute CV Behavioral Analysis (Authorized Roles)"
)
def analyze_media(
    media_id: str,
    payload: MediaAnalysisTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """
    Executes task-specific behavioral computer vision analysis on video or photo.
    Extracts movement dynamics, rhythmicity, coarse gaze orientation, joint-attention latency,
    and enforces strict negative ethical constraints against facial autism diagnosis.
    """
    return MediaService.analyze_media(
        db=db,
        media_id=media_id,
        trigger_req=payload,
        current_user=current_user
    )


@router.get(
    "/{media_id}/screening-synthesis",
    response_model=MultimodalVideoScreeningResponse,
    summary="Synthesize Multimodal Video Screening (Authorized Roles)"
)
def get_multimodal_screening_synthesis(
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """
    Synthesizes objective video-derived behavioral features with developmental milestones,
    structured caregiver observations, and qualified clinical ratings into a clinical triage summary.
    """
    return MediaService.synthesize_multimodal_screening(
        db=db,
        media_id=media_id,
        current_user=current_user
    )


@router.delete(
    "/{media_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Media Record & File (Administrator & Assessor Only)"
)
def delete_media(
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor"]))
):
    """
    Securely removes research media file from disk, deletes database records,
    and logs the deletion event to the immutable audit trail.
    """
    MediaService.delete_media(db=db, media_id=media_id, current_user=current_user)
    return {"status": "success", "message": "Media upload and associated analyses securely deleted."}

