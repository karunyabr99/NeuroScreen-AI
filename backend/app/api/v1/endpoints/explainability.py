from typing import List, Dict, Any
from fastapi import APIRouter
from app.services.ml_bridge import MLBridge

router = APIRouter()

@router.get("/models", summary="Inspect Registered ML & Deep Learning Models")
def list_registered_models() -> List[Dict[str, Any]]:
    """
    Returns discovery metadata and calibration status for all registered model architectures:
    - Scikit-Learn Random Forest
    - XGBoost Classifier
    - CatBoost Classifier
    - PyTorch Deep Multimodal Fusion Network
    """
    return MLBridge.get_registered_models()

