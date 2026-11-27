from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class SimulationInput(BaseModel):
    participant_id: Optional[str] = Field(default=None, description="Optional custom or auto-generated participant ID")
    scenario_name: Optional[str] = Field(default="Custom Simulation", description="Preset or custom scenario name")
    age_months: int = Field(default=36, ge=12, le=120, description="Child age in months (12-120)")
    
    # 9 Core Assessment Observation Dimensions (0 to 3 scale)
    communication_development: float = Field(default=0.0, ge=0.0, le=3.0, description="0: Age-appropriate, 1: Mild, 2: Moderate, 3: Significant delay")
    social_interaction: float = Field(default=0.0, ge=0.0, le=3.0, description="0: Reciprocal, 1: Variable, 2: Infrequent, 3: Marked withdrawal")
    response_to_name: float = Field(default=0.0, ge=0.0, le=3.0, description="0: Immediate, 1: Delayed, 2: Inconsistent, 3: Rarely orients")
    eye_contact_observations: float = Field(default=0.0, ge=0.0, le=3.0, description="0: Natural, 1: Brief, 2: Fleeting, 3: Avoidant")
    gesture_usage: float = Field(default=0.0, ge=0.0, le=3.0, description="0: Rich gestures & pointing, 1: Basic, 2: Reduced, 3: Absent")
    repetitive_behaviours: float = Field(default=0.0, ge=0.0, le=3.0, description="0: None, 1: Occasional, 2: Frequent stereotypies, 3: Intense")
    play_patterns: float = Field(default=0.0, ge=0.0, le=3.0, description="0: Imaginative pretend play, 1: Structured, 2: Rigid lining, 3: Monotropic")
    developmental_milestones: float = Field(default=0.0, ge=0.0, le=3.0, description="0: On schedule, 1: Isolated delay, 2: Multi-domain delay, 3: Global lag")
    caregiver_observations: float = Field(default=0.0, ge=0.0, le=3.0, description="0: No concerns, 1: Mild routine/speech, 2: Moderate social, 3: High sensory")
    
    # Test flags
    is_incomplete: bool = Field(default=False, description="Simulate missing/unrecorded sensor modalities")
    notes: Optional[str] = Field(default=None, description="Clinical observation notes")

class ContributingFeature(BaseModel):
    feature_name: str
    display_name: str
    modality: str
    feature_value: float
    importance_value: float
    direction: str # "risk_increasing" | "risk_decreasing" | "neutral"
    clinical_note: str

class SimulationResultResponse(BaseModel):
    session_id: str
    patient_id: str
    participant_id: str
    scenario_name: str
    age_months: int
    
    # Model Prediction
    predicted_probability: float
    risk_tier: str
    confidence_interval: Dict[str, float]
    model_name: str
    model_architecture: str
    is_calibrated: bool
    
    # Explainability & Contributing Features
    contributing_features: List[ContributingFeature]
    positive_contributions: List[ContributingFeature]
    negative_contributions: List[ContributingFeature]
    summary_narrative: str
    
    # Governance & Synthetic Notice
    is_synthetic_demonstration: bool = True
    clinical_disclaimer: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScenarioDefinition(BaseModel):
    id: str
    name: str
    description: str
    clinical_focus: str
    inputs: SimulationInput

