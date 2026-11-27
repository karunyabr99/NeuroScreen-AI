from typing import Dict, Any
from ml_engine.interfaces.base_pipeline import BaseFeaturePipeline

class VisualGazePipeline(BaseFeaturePipeline):
    """
    Extracts and standardizes ocular gaze and scanpath features based on Patent Reference 1.
    """

    @property
    def modality_name(self) -> str:
        return "visual_gaze"

    def extract_features(self, raw_input: Dict[str, Any]) -> Dict[str, float]:
        return {
            "fixation_count": float(max(5, min(300, raw_input.get("fixation_count", 45)))),
            "mean_fixation_duration_ms": float(max(50.0, min(1200.0, raw_input.get("mean_fixation_duration_ms", 260.0)))),
            "social_roi_dwell_percentage": float(max(0.0, min(100.0, raw_input.get("social_roi_dwell_percentage", 70.0)))),
            "joint_attention_latency_ms": float(max(100.0, min(4000.0, raw_input.get("joint_attention_latency_ms", 520.0)))),
            "saccade_mean_amplitude_deg": float(max(0.5, min(35.0, raw_input.get("saccade_mean_amplitude_deg", 7.5)))),
            "atypical_scanpath_entropy": float(max(0.0, min(1.0, raw_input.get("atypical_scanpath_entropy", 0.40)))),
        }

