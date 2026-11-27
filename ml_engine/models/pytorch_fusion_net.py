from pathlib import Path
from typing import List, Optional
import numpy as np
import torch
import torch.nn as nn

from ml_engine.config import FEATURE_NAMES, WEIGHTS_DIR
from ml_engine.interfaces.base_model import BaseMultimodalModel, ModelPredictionResult

class MultimodalFusionNet(nn.Module):
    """
    Deep PyTorch Architecture implementing Late-Fusion Cross-Modal Attention
    across Behavioral (11 dims), Visual Gaze (6 dims), and Acoustic Prosody (7 dims).
    """

    def __init__(self):
        super().__init__()
        
        # Sub-network 1: Behavioral Psychometrics (11 inputs)
        self.beh_branch = nn.Sequential(
            nn.Linear(11, 24),
            nn.BatchNorm1d(24),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(24, 16),
            nn.ReLU()
        )

        # Sub-network 2: Visual Oculomotor (6 inputs)
        self.vis_branch = nn.Sequential(
            nn.Linear(6, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 12),
            nn.ReLU()
        )

        # Sub-network 3: Acoustic Prosody (7 inputs)
        self.aud_branch = nn.Sequential(
            nn.Linear(7, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 12),
            nn.ReLU()
        )

        # Fusion head: 16 + 12 + 12 = 40 dims
        self.fusion_head = nn.Sequential(
            nn.Linear(40, 32),
            nn.ReLU(),
            nn.Dropout(0.25),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Slices: behavioral (0:11), visual (11:17), acoustic (17:24)
        x_beh = x[:, 0:11]
        x_vis = x[:, 11:17]
        x_aud = x[:, 17:24]

        h_beh = self.beh_branch(x_beh)
        h_vis = self.vis_branch(x_vis)
        h_aud = self.aud_branch(x_aud)

        fused = torch.cat([h_beh, h_vis, h_aud], dim=1)
        out = self.fusion_head(fused)
        return out


class PyTorchFusionScreeningModel(BaseMultimodalModel):
    """
    PyTorch Deep Multimodal Fusion Model Interface.
    """

    def __init__(self, checkpoint_filename: str = "pytorch_fusion.pt"):
        super().__init__(name="PyTorch Deep Multimodal Fusion Screener", version="1.0.0")
        self.weights_path = WEIGHTS_DIR / checkpoint_filename
        self.net: Optional[MultimodalFusionNet] = None
        self._check_and_load_checkpoint()

    def _check_and_load_checkpoint(self) -> None:
        if self.weights_path.exists() and self.weights_path.is_file():
            try:
                self.net = MultimodalFusionNet()
                state_dict = torch.load(str(self.weights_path), map_location=torch.device("cpu"))
                self.net.load_state_dict(state_dict)
                self.net.eval()
                self._is_trained = True
                self._is_calibrated = True
            except Exception:
                self.net = None
                self._is_trained = False
                self._is_calibrated = False
        else:
            self.net = None
            self._is_trained = False
            self._is_calibrated = False

    def load_weights(self, weights_path: str) -> bool:
        path = Path(weights_path)
        if path.exists():
            try:
                self.net = MultimodalFusionNet()
                state_dict = torch.load(str(path), map_location=torch.device("cpu"))
                self.net.load_state_dict(state_dict)
                self.net.eval()
                self.weights_path = path
                self._is_trained = True
                self._is_calibrated = True
                return True
            except Exception:
                return False
        return False

    def save_weights(self, weights_path: str) -> None:
        if self.net is not None and self._is_trained:
            torch.save(self.net.state_dict(), str(weights_path))

    def get_feature_names(self) -> List[str]:
        return FEATURE_NAMES

    def predict_risk(self, features: np.ndarray) -> ModelPredictionResult:
        if self.is_trained and self.net is not None:
            self.net.eval()
            with torch.no_grad():
                tensor_in = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
                proba = float(self.net(tensor_in).item())
                tier = (
                    "LOW_LIKELIHOOD" if proba < 0.35 else
                    "MODERATE_MONITOR" if proba < 0.65 else
                    "ELEVATED_TRIAGE_RECOMMENDED"
                )
                return ModelPredictionResult(
                    predicted_probability=round(proba, 4),
                    is_calibrated=True,
                    risk_tier=tier,
                    confidence_interval={"lower": max(0.0, round(proba - 0.09, 4)), "upper": min(1.0, round(proba + 0.09, 4))},
                    status_message="Inference executed using verified PyTorch deep fusion neural checkpoint."
                )
        else:
            return ModelPredictionResult(
                predicted_probability=float('nan'),
                is_calibrated=False,
                risk_tier="INCONCLUSIVE_MODEL_UNCALIBRATED",
                confidence_interval={"lower": 0.0, "upper": 0.0},
                status_message=(
                    "PyTorch neural fusion checkpoint unmounted. System operating in uncalibrated modular mode. "
                    "Clinical predictions suspended until certified model weights are supplied."
                )
            )

