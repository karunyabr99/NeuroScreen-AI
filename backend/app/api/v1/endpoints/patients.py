from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services.patient_service import PatientService
from app.models.user import User

router = APIRouter()

@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Patient Intake (Administrator & Assessor Only)"
)
@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor"]))
):
    return PatientService.create_patient(db, payload)

@router.get(
    "/",
    response_model=List[PatientResponse],
    summary="List Registered Patients (Administrator, Assessor & Researcher)"
)
@router.get(
    "",
    response_model=List[PatientResponse],
    include_in_schema=False
)
def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    return PatientService.list_patients(db, skip=skip, limit=limit)

@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get Patient Intake Details (Administrator, Assessor & Researcher)"
)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    patient = PatientService.get_patient(db, patient_id)
    if not patient:
        # Generic error preventing internal details exposure
        raise HTTPException(status_code=404, detail="Patient record not found.")
    return patient

@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update Patient Demographics (Administrator & Assessor Only)"
)
def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor"]))
):
    patient = PatientService.update_patient(db, patient_id, payload)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient record not found.")
    return patient

@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive/Delete Patient Record (Administrator Only)"
)
def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator"]))
):
    success = PatientService.delete_patient(db, patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient record not found.")
    return None
