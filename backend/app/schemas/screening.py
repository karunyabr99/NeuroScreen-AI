from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class BehavioralInput(BaseModel):
    # Toddler Q-CHAT-10 explicit items (optional, 0 or 1)
    a1: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-1: Response to name call")
    a2: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-2: Eye contact quality")
    a3: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-3: Proto-imperative pointing for wants")
    a4: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-4: Proto-declarative pointing to share interest")
    a5: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-5: Pretend play / symbolic play")
    a6: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-6: Gaze following")
    a7: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-7: Empathic comforting in distress")
    a8: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-8: First words / speech atypicality")
    a9: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-9: Communicative gestures (waving, nodding)")
    a10: Optional[int] = Field(None, ge=0, le=1, description="Q-CHAT-10: Aimless staring / visual fixation")

    # Demographic / history features for toddler models
    ethnicity: Optional[str] = Field("Others", description="Ethnicity (e.g. middle eastern, White European, Asian, etc.)")
    jaundice: Optional[str] = Field("no", description="Neonatal jaundice ('yes' or 'no')")
    family_mem_with_asd: Optional[str] = Field("no", description="Family member with ASD history ('yes' or 'no')")
    who_completed_test: Optional[str] = Field("family member", description="Test respondent relationship")

    # Multimodal behavioral items
    social_smile_reciprocity: int = Field(0, ge=0, le=1, description="Responsive social smiling")
    name_call_orientation: int = Field(0, ge=0, le=1, description="Orienting to auditory name call")
    pointing_proto_declarative: int = Field(0, ge=0, le=1, description="Proto-declarative joint attention pointing")
    pretend_play_engagement: int = Field(0, ge=0, le=1, description="Imaginative / pretend symbolic play")
    repetitive_motor_mannerisms: int = Field(0, ge=0, le=1, description="Hand-flapping or repetitive body rocking")
    monotropic_focus_intensity: int = Field(0, ge=0, le=1, description="Intense fixated interests / hyperfocus")
    gaze_alternation_dyadic: int = Field(0, ge=0, le=1, description="Gaze alternation between object and caregiver")
    sensory_hypersensitivity: int = Field(0, ge=0, le=1, description="Atypical auditory / tactile sensory reactivity")
    peer_social_interest: int = Field(0, ge=0, le=1, description="Spontaneous interest in peer interaction")
    gestural_communication: int = Field(0, ge=0, le=1, description="Use of descriptive / communicative gestures")
    response_latency_mean_sec: float = Field(2.4, ge=0.5, le=30.0, description="Mean response latency in seconds")

class VisualGazeInput(BaseModel):
    fixation_count: int = Field(42, ge=5, le=300, description="Total ocular fixations recorded")
    mean_fixation_duration_ms: float = Field(280.0, ge=50.0, le=1200.0, description="Mean duration per fixation in ms")
    social_roi_dwell_percentage: float = Field(58.5, ge=0.0, le=100.0, description="Dwell time % on social/face ROI vs abstract")
    joint_attention_latency_ms: float = Field(650.0, ge=100.0, le=4000.0, description="Latency to align gaze with cue")
    saccade_mean_amplitude_deg: float = Field(7.8, ge=0.5, le=35.0, description="Average saccadic amplitude in degrees")
    atypical_scanpath_entropy: float = Field(0.42, ge=0.0, le=1.0, description="Shannon entropy of ocular scanpath")

class AcousticProsodyInput(BaseModel):
    fundamental_freq_f0_mean_hz: float = Field(235.0, ge=70.0, le=500.0, description="Mean fundamental pitch F0 in Hz")
    f0_pitch_variability_stdev_hz: float = Field(32.4, ge=2.0, le=150.0, description="Pitch standard deviation / modulation")
    vocal_jitter_percent: float = Field(1.12, ge=0.05, le=10.0, description="Cycle-to-cycle frequency variation %")
    vocal_shimmer_db: float = Field(0.35, ge=0.01, le=5.0, description="Cycle-to-cycle amplitude perturbation in dB")
    pause_to_speech_ratio: float = Field(0.38, ge=0.05, le=0.95, description="Ratio of silent pause intervals to speech")
    formant_dispersion_hz: float = Field(1120.0, ge=400.0, le=2500.0, description="Vocal tract formant dispersion")
    speech_rate_syllables_sec: float = Field(3.4, ge=0.5, le=9.0, description="Estimated articulation rate")

class ScreeningCreate(BaseModel):
    patient_id: str
    behavioral: Optional[BehavioralInput] = None
    visual_gaze: Optional[VisualGazeInput] = None
    acoustic_prosody: Optional[AcousticProsodyInput] = None
    preferred_model: Optional[str] = Field("random_forest", description="'random_forest', 'xgboost', 'catboost', 'pytorch_fusion'")

class ScreeningResponse(BaseModel):
    id: str
    patient_id: str
    status: str
    protocol_version: str
    composite_risk_score: Optional[float]
    risk_tier: str
    confidence_interval: Optional[Dict[str, float]]
    model_version: str
    is_calibrated: bool
    modalities_included: List[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ModalityFeatureResponse(BaseModel):
    id: str
    modality_type: str
    raw_metrics: Dict[str, Any]
    extracted_features: Dict[str, Any]
    quality_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
