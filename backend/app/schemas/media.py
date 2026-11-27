from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class MediaAnalysisResponse(BaseModel):
    id: str
    media_id: str
    pipeline_version: str
    analysis_status: str
    data_quality_score: float
    
    # Observable Behavioral Feature Domains
    movement_and_pose: Dict[str, Any]
    gesture_and_actions: Dict[str, Any]
    gaze_measurements: Dict[str, Any]
    joint_attention_observations: Dict[str, Any]
    repetitive_movements: Dict[str, Any]
    social_interaction_opportunities: Dict[str, Any]
    
    # Image Quality & Scene Context (For Photographs)
    image_quality_and_context: Dict[str, Any]
    
    # Scientific & Ethical Safeguards (Mandatory Constraints)
    ethical_safeguards: Dict[str, Any]
    limitations_summary: Optional[str] = None
    clinical_recommendation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaUploadResponse(BaseModel):
    id: str
    patient_id: str
    session_id: Optional[str] = None
    media_type: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    duration_seconds: Optional[float] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[float] = None
    task_context: str
    media_quality_status: str
    media_training_authorized: bool
    uploader_id: str
    uploader_role: str
    is_synthetic: bool
    created_at: datetime
    analysis: Optional[MediaAnalysisResponse] = None

    model_config = ConfigDict(from_attributes=True)


class MediaAnalysisTriggerRequest(BaseModel):
    task_context: Optional[str] = Field(default="structured_joint_attention", description="Structured protocol activity type")
    extract_repetitive_patterns: bool = Field(default=True, description="Analyze periodic motor stereotypies")
    measure_gaze_orientation: bool = Field(default=True, description="Analyze head orientation and coarse gaze toward task targets")
    observe_joint_attention: bool = Field(default=True, description="Quantify latency in shifting orientation toward examiner visual cue")


class MultimodalVideoScreeningResponse(BaseModel):
    patient_id: str
    anonymized_id: str
    age_months: int
    screening_session_id: Optional[str] = None
    media_id: str
    
    # Separately Identifiable Information Sources (Module 4)
    video_observable_features: Dict[str, Any]
    developmental_milestones: Dict[str, Any]
    caregiver_observations: Dict[str, Any] # Clearly marked as descriptive, not confirmed diagnosis
    teacher_observations: Dict[str, Any]
    professional_clinical_findings: Dict[str, Any]
    
    # Synthesis & Triage Guidance
    data_quality_status: str
    screening_support_category: str
    model_availability: str
    confidence_interval: Optional[Dict[str, float]] = None
    limitations: List[str]
    mandatory_safeguard_disclaimer: str
    clinical_recommendation: str

