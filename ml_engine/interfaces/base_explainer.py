from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np

class BaseExplainer(ABC):
    """Abstract interface for local & global explainability engines (SHAP / LIME)."""

    @property
    @abstractmethod
    def explainer_type(self) -> str:
        """Explainer identifier ('SHAP' or 'LIME')."""
        pass

    @abstractmethod
    def explain_instance(
        self,
        model_wrapper: Any,
        feature_vector: np.ndarray,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Generate feature attributions for an individual screening instance.
        Must return structured attribution schema suitable for UI visualization.
        """
        pass

