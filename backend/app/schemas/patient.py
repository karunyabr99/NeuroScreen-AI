from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class PatientBase(BaseModel):
    age_months: int = Field(..., ge=0, le=360, description="Patient age in completed months (0-11m observation mode, 12-36m toddler screening)")
    biological_sex: str = Field(..., description="'male', 'female', 'other', or 'unspecified'")
    referral_source: str = Field(default="Clinic", description="Originating referral clinic, school or specialist")
    clinical_notes: Optional[str] = Field(default=None, description="Optional clinician context")
    
    # Phase 4 Research Governance
    is_synthetic: bool = Field(default=False, description="Explicit tag segregating synthetic dev records from real cohorts")
    consent_status: str = Field(default="pending", description="'granted', 'pending', 'withdrawn', or 'declined'")
    assent_status: str = Field(default="not_applicable", description="'granted', 'declined', or 'not_applicable'")
    guardian_relationship: Optional[str] = Field(default="Parent", description="Relationship of consenting guardian")
    ethics_approval_ref: str = Field(default="IRB-NS-2026-ETHICS-04", description="Institutional ethics approval protocol reference")
    protocol_version: str = Field(default="NS-DATA-COLL-v1.0", description="Data collection research protocol version")

class PatientCreate(PatientBase):
    anonymized_id: Optional[str] = Field(default=None, description="Optional custom ID (e.g. NS-2026-XXXX); auto-generated if omitted")
    consent_date: Optional[datetime] = None
    assessor_id: Optional[str] = None

class PatientUpdate(BaseModel):
    age_months: Optional[int] = None
    biological_sex: Optional[str] = None
    referral_source: Optional[str] = None
    clinical_notes: Optional[str] = None
    consent_status: Optional[str] = None
    assent_status: Optional[str] = None
    guardian_relationship: Optional[str] = None
    ethics_approval_ref: Optional[str] = None
    protocol_version: Optional[str] = None

class PatientResponse(PatientBase):
    id: str
    anonymized_id: str
    consent_date: Optional[datetime] = None
    consent_withdrawn_at: Optional[datetime] = None
    assessor_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
