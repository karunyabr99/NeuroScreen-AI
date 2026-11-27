from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseFeaturePipeline(ABC):
    """Abstract interface for modality-specific feature extractors."""

    @property
    @abstractmethod
    def modality_name(self) -> str:
        """Name of the modality (behavioral, visual_gaze, acoustic_prosody)."""
        pass

    @abstractmethod
    def extract_features(self, raw_input: Dict[str, Any]) -> Dict[str, float]:
        """Convert raw user/device input payload into normalized quantitative features."""
        pass

