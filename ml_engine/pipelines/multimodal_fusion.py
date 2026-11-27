from typing import Dict, Any, Tuple, List
import numpy as np
from ml_engine.config import FEATURE_DEFINITIONS, FEATURE_NAMES, FEATURE_MAP
from ml_engine.pipelines.behavioral_pipeline import BehavioralPipeline
from ml_engine.pipelines.visual_pipeline import VisualGazePipeline
from ml_engine.pipelines.audio_pipeline import AudioProsodyPipeline

class MultimodalFusionPipeline:
    """
    Coordinates multimodal ingestion across Behavioral, Visual Ocular, and Acoustic Prosody
    pipelines, constructing the canonical aligned feature representation.
    """

    def __init__(self):
        self.behavioral_pipe = BehavioralPipeline()
        self.visual_pipe = VisualGazePipeline()
        self.audio_pipe = AudioProsodyPipeline()

    def process_screening_inputs(
        self,
        behavioral_raw: Dict[str, Any] = None,
        visual_raw: Dict[str, Any] = None,
        audio_raw: Dict[str, Any] = None
    ) -> Tuple[np.ndarray, Dict[str, Dict[str, float]], List[str]]:
        """
        Processes and aligns all available modalities.
        Returns:
            - feature_vector: 1D np.ndarray of shape (24,) matching FEATURE_NAMES
            - modality_features: dict mapping modality -> extracted feature map
            - modalities_present: list of present modalities
        """
        modality_features: Dict[str, Dict[str, float]] = {}
        modalities_present: List[str] = []

        if behavioral_raw is not None:
            modality_features["behavioral"] = self.behavioral_pipe.extract_features(behavioral_raw)
            modalities_present.append("behavioral")
        else:
            modality_features["behavioral"] = {}

        if visual_raw is not None:
            modality_features["visual_gaze"] = self.visual_pipe.extract_features(visual_raw)
            modalities_present.append("visual_gaze")
        else:
            modality_features["visual_gaze"] = {}

        if audio_raw is not None:
            modality_features["acoustic_prosody"] = self.audio_pipe.extract_features(audio_raw)
            modalities_present.append("acoustic_prosody")
        else:
            modality_features["acoustic_prosody"] = {}

        # Merge into single feature dictionary
        unified_features: Dict[str, float] = {}
        for mod_dict in modality_features.values():
            unified_features.update(mod_dict)

        # Assemble canonical 1D numpy array aligned with FEATURE_NAMES
        vector = np.zeros(len(FEATURE_NAMES), dtype=np.float32)
        for i, feat_id in enumerate(FEATURE_NAMES):
            defn = FEATURE_MAP[feat_id]
            if feat_id in unified_features:
                vector[i] = unified_features[feat_id]
            else:
                # Use clinical normative population mean if modality was omitted
                vector[i] = defn["mean_norm"]

        return vector, modality_features, modalities_present

    def normalize_vector(self, raw_vector: np.ndarray) -> np.ndarray:
        """Standardize raw feature vector using population normative parameters."""
        normalized = np.zeros_like(raw_vector)
        for i, feat_id in enumerate(FEATURE_NAMES):
            defn = FEATURE_MAP[feat_id]
            mean_val = defn["mean_norm"]
            std_val = defn["std_norm"]
            normalized[i] = (raw_vector[i] - mean_val) / (std_val if std_val > 0 else 1.0)
        return normalized

