from typing import Dict, Any
from ml_engine.interfaces.base_pipeline import BaseFeaturePipeline

class AudioProsodyPipeline(BaseFeaturePipeline):
    """
    Extracts and standardizes acoustic prosody biomarkers based on Research Paper 2.
    """

    @property
    def modality_name(self) -> str:
        return "acoustic_prosody"

    def extract_features(self, raw_input: Dict[str, Any]) -> Dict[str, float]:
        return {
            "fundamental_freq_f0_mean_hz": float(max(70.0, min(500.0, raw_input.get("fundamental_freq_f0_mean_hz", 240.0)))),
            "f0_pitch_variability_stdev_hz": float(max(2.0, min(150.0, raw_input.get("f0_pitch_variability_stdev_hz", 40.0)))),
            "vocal_jitter_percent": float(max(0.05, min(10.0, raw_input.get("vocal_jitter_percent", 0.9)))),
            "vocal_shimmer_db": float(max(0.01, min(5.0, raw_input.get("vocal_shimmer_db", 0.32)))),
            "pause_to_speech_ratio": float(max(0.05, min(0.95, raw_input.get("pause_to_speech_ratio", 0.32)))),
            "formant_dispersion_hz": float(max(400.0, min(2500.0, raw_input.get("formant_dispersion_hz", 1150.0)))),
            "speech_rate_syllables_sec": float(max(0.5, min(9.0, raw_input.get("speech_rate_syllables_sec", 3.5)))),
        }

