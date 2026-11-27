from typing import Dict, Any, List
from fastapi import APIRouter
from app.services.ml_bridge import MLBridge

router = APIRouter()

@router.get("/features", summary="Multimodal Feature Catalog & Research Specifications")
def get_feature_catalog() -> List[Dict[str, Any]]:
    """
    Returns the comprehensive catalog of 24 multimodal features
    across Behavioral, Visual Gaze, and Acoustic Prosody modalities,
    including reference research origins and population normative parameters.
    """
    return MLBridge.get_feature_catalog()

@router.post("/preview", summary="Preview Feature Alignment & Normalization Vector")
def preview_multimodal_vector(payload: Dict[str, Any]):
    """
    Dry-run endpoint allowing clinical researchers to inspect the constructed
    24-dimensional aligned vector and modality mappings without saving to database.
    """
    beh = payload.get("behavioral")
    vis = payload.get("visual_gaze")
    aud = payload.get("acoustic_prosody")

    vector, modality_features, present = MLBridge.process_multimodal_inputs(beh, vis, aud)
    normalized = MLBridge._fusion_pipeline.normalize_vector(vector)

    return {
        "modalities_present": present,
        "feature_count": len(vector),
        "raw_vector": vector.tolist(),
        "normalized_z_vector": [round(float(x), 3) for x in normalized],
        "modality_breakdown": modality_features
    }

