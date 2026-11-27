from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class FeatureContribution(BaseModel):
    feature_name: str
    display_name: str
    modality: str
    feature_value: float
    importance_value: float
    direction: str
    clinical_note: str

class ExplainabilityResponse(BaseModel):
    id: str
    session_id: str
    method: str
    status: str = "EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED"
    base_value: float
    prediction_value: float
    is_calibrated: bool
    calibration_status_notice: str
    feature_importances: List[FeatureContribution]
    summary_narrative: str
    modality_breakdown: Dict[str, float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ModelStatusResponse(BaseModel):
    model_name: str
    model_family: str
    is_trained: bool
    is_calibrated: bool
    checkpoint_found: bool
    weights_path: Optional[str]
    input_feature_dim: int
    architecture_description: str
    supported_explainers: List[str]
    status_message: str

class ScreeningDetailResponse(BaseModel):
    session: Any
    features: List[Any]
    explanations: List[ExplainabilityResponse]
    model_status: ModelStatusResponse
    clinical_disclaimer: str
