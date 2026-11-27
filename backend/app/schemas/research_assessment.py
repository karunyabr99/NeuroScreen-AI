from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class ConsentUpdateRequest(BaseModel):
    consent_status: str = Field(..., description="'granted', 'withdrawn', 'pending', or 'declined'")
    assent_status: Optional[str] = Field(default="not_applicable", description="'granted', 'declined', or 'not_applicable'")
    guardian_relationship: Optional[str] = Field(default="Parent", description="Relationship of consenting guardian")
    ethics_approval_ref: Optional[str] = Field(default="IRB-NS-2026-ETHICS-04", description="Ethics protocol reference")
    protocol_version: Optional[str] = Field(default="NS-DATA-COLL-v1.0", description="Protocol version")
    notes: Optional[str] = None

class ResearchAssessmentCreate(BaseModel):
    patient_id: str = Field(..., description="Target participant ID")
    form_type: str = Field(..., description="'caregiver', 'teacher', 'professional', or 'multimodal_comprehensive'")
    assessor_role: str = Field(..., description="Assessor category: Caregiver, Special Educator, or Qualified Professional")
    assessment_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Domains
    developmental_history: Optional[Dict[str, Any]] = Field(default_factory=dict)
    communication_milestones: Optional[Dict[str, Any]] = Field(default_factory=dict)
    social_interaction_observations: Optional[Dict[str, Any]] = Field(default_factory=dict)
    behavioral_characteristics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    repetitive_behaviors: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Caregiver concerns - Strictly unconfirmed observations
    caregiver_concerns: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Medical & Family history (Authorized)
    medical_family_history: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Multimodal measurements
    multimodal_measurements: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    notes: Optional[str] = None
    is_synthetic: bool = False

class ResearchAssessmentResponse(BaseModel):
    id: str
    patient_id: str
    form_type: str
    assessor_id: str
    assessor_role: str
    assessment_date: datetime
    protocol_version: str
    ethics_approval_ref: str
    is_synthetic: bool
    data_quality_status: str
    quality_score: float
    
    developmental_history: Dict[str, Any]
    communication_milestones: Dict[str, Any]
    social_interaction_observations: Dict[str, Any]
    behavioral_characteristics: Dict[str, Any]
    repetitive_behaviors: Dict[str, Any]
    caregiver_concerns: Dict[str, Any]
    medical_family_history: Dict[str, Any]
    multimodal_measurements: Dict[str, Any]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

