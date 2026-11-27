from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DatasetPreviewResponse(BaseModel):
    row_count: int
    column_count: int
    identified_target: Optional[str] = None
    id_columns: List[str] = []
    leakage_columns: List[str] = []
    duplicate_rows_count: int = 0
    total_missing_cells: int = 0
    overall_missing_rate: float = 0.0
    columns: List[Dict[str, Any]] = []
    class_balance: Dict[str, Any] = {}
    preview: List[Dict[str, Any]] = []
    target_leakage_audit: Optional[Dict[str, Any]] = None


class TrainModelsRequest(BaseModel):
    dataset_name: Optional[str] = None
    iterations: Optional[int] = Field(default=350, ge=50, le=1000)
    depth: Optional[int] = Field(default=4, ge=2, le=8)
    learning_rate: Optional[float] = Field(default=0.05, ge=0.001, le=0.5)
    n_estimators: Optional[int] = Field(default=150, ge=10, le=500)
    lasso_c: Optional[float] = Field(default=0.5, ge=0.01, le=10.0)


class ChildPredictionRequest(BaseModel):
    a1: int = Field(default=0, ge=0, le=1)
    a2: int = Field(default=0, ge=0, le=1)
    a3: int = Field(default=0, ge=0, le=1)
    a4: int = Field(default=0, ge=0, le=1)
    a5: int = Field(default=0, ge=0, le=1)
    a6: int = Field(default=0, ge=0, le=1)
    a7: int = Field(default=0, ge=0, le=1)
    a8: int = Field(default=0, ge=0, le=1)
    a9: int = Field(default=0, ge=0, le=1)
    a10: int = Field(default=0, ge=0, le=1)
    age_months: float = Field(default=24.0, ge=0.0, le=120.0)
    sex: str = Field(default="m")
    ethnicity: Optional[str] = Field(default="middle eastern")
    jaundice: Optional[str] = Field(default="no")
    family_mem_with_asd: Optional[str] = Field(default="no")
    who_completed_test: Optional[str] = Field(default="family member")
    model_name: Optional[str] = Field(default="catboost")


class ChildPredictionResponse(BaseModel):
    screening_status: str
    predicted_probability: Optional[float] = None
    is_calibrated: bool
    risk_tier: str
    risk_category_label: str
    confidence_interval: Dict[str, float]
    threshold_applied: Optional[float] = None
    threshold_label: Optional[str] = None
    status_message: str
    model_used: str
    model_title: Optional[str] = None
    explanation: Dict[str, Any]
    raw_inputs: Optional[Dict[str, Any]] = None

