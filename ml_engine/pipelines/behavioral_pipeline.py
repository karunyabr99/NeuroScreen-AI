from typing import Dict, Any
from ml_engine.interfaces.base_pipeline import BaseFeaturePipeline

class BehavioralPipeline(BaseFeaturePipeline):
    """
    Extracts and standardizes psychometric features based on Research Paper 1
    (Digitized AQ-10 & M-CHAT social communication and repetitive behavior vectors).
    """

    @property
    def modality_name(self) -> str:
        return "behavioral"

    def extract_features(self, raw_input: Dict[str, Any]) -> Dict[str, float]:
        features: Dict[str, float] = {}
        
        # Binary indicator items (0 or 1)
        binary_fields = [
            "social_smile_reciprocity",
            "name_call_orientation",
            "pointing_proto_declarative",
            "pretend_play_engagement",
            "repetitive_motor_mannerisms",
            "monotropic_focus_intensity",
            "gaze_alternation_dyadic",
            "sensory_hypersensitivity",
            "peer_social_interest",
            "gestural_communication"
        ]
        
        for field in binary_fields:
            val = float(raw_input.get(field, 0.0))
            features[field] = max(0.0, min(1.0, val))

        # Continuous response latency
        latency = float(raw_input.get("response_latency_mean_sec", 2.2))
        features["response_latency_mean_sec"] = max(0.5, min(30.0, latency))
        
        return features

