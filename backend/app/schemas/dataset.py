from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class DuplicateRecord(BaseModel):
    anonymized_id: str
    age_months: int
    biological_sex: str
    duplicate_type: str # e.g. "exact_profile_match", "timestamp_collision"
    matching_ids: List[str]

class DatasetOverviewResponse(BaseModel):
    total_participants: int
    real_participants: int
    synthetic_participants: int
    consented_real_participants: int
    withdrawn_participants: int
    
    total_sessions: int
    real_sessions: int
    synthetic_sessions: int
    total_research_assessments: int
    
    age_distribution: Dict[str, int] # e.g. {"12-24m": 5, "25-36m": 12, ...}
    modality_distribution: Dict[str, float] # percentage coverage e.g. {"behavioral": 95.0, ...}
    missing_value_percentages: Dict[str, float]
    
    duplicate_count: int
    duplicates: List[DuplicateRecord]
    
    label_distribution: Dict[str, int]
    data_quality_warnings: List[str]
    dataset_version: str

class BenchmarkGenerationRequest(BaseModel):
    sample_size: int = Field(default=60, ge=20, le=500, description="Number of synthetic development records to generate")
    target_asd_prevalence: float = Field(default=0.5, ge=0.1, le=0.9, description="Target proportion of positive research cohorts")

