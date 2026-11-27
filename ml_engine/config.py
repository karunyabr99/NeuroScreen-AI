from pathlib import Path
from typing import Dict, List, Any

# Root paths
ML_DIR = Path(__file__).resolve().parent
WEIGHTS_DIR = ML_DIR / "weights"
DATASETS_DIR = ML_DIR / "datasets"

# Standardized Feature Specifications for the Multimodal ASD Model
FEATURE_DEFINITIONS: List[Dict[str, Any]] = [
    # --- Modality 1: Behavioral & Psychometric (Research Paper 1 Reference) ---
    {
        "id": "social_smile_reciprocity",
        "name": "Social Smile Reciprocity",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.15,
        "std_norm": 0.35,
        "clinical_note": "Atypical or absent reciprocal social smiling in response to examiner/caregiver."
    },
    {
        "id": "name_call_orientation",
        "name": "Name Call Orientation",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.18,
        "std_norm": 0.38,
        "clinical_note": "Failure to orient head or eyes upon hearing own name called repeatedly."
    },
    {
        "id": "pointing_proto_declarative",
        "name": "Joint Attention Pointing",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.20,
        "std_norm": 0.40,
        "clinical_note": "Absence of pointing to share interest in an object or event (proto-declarative)."
    },
    {
        "id": "pretend_play_engagement",
        "name": "Pretend / Imaginative Play",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.22,
        "std_norm": 0.41,
        "clinical_note": "Reduced spontaneous pretend play with miniature objects or symbolic toys."
    },
    {
        "id": "repetitive_motor_mannerisms",
        "name": "Repetitive Motor Mannerisms",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.10,
        "std_norm": 0.30,
        "clinical_note": "Observed hand-flapping, finger flicking, or whole-body rocking."
    },
    {
        "id": "monotropic_focus_intensity",
        "name": "Monotropic Focus Intensity",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.15,
        "std_norm": 0.36,
        "clinical_note": "Intense perseveration on narrow parts of toys (e.g. spinning wheels)."
    },
    {
        "id": "gaze_alternation_dyadic",
        "name": "Dyadic Gaze Alternation",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.12,
        "std_norm": 0.32,
        "clinical_note": "Reduced gaze shifting between interesting object and adult partner."
    },
    {
        "id": "sensory_hypersensitivity",
        "name": "Sensory Hyper-Reactivity",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.25,
        "std_norm": 0.43,
        "clinical_note": "Adverse reaction to everyday environmental sounds, textures, or lighting."
    },
    {
        "id": "peer_social_interest",
        "name": "Peer Social Interest",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.18,
        "std_norm": 0.38,
        "clinical_note": "Preference for solitary play over reciprocal engagement with peers."
    },
    {
        "id": "gestural_communication",
        "name": "Gestural Communication",
        "modality": "behavioral",
        "typical_range": (0.0, 1.0),
        "mean_norm": 0.14,
        "std_norm": 0.35,
        "clinical_note": "Under-utilization of descriptive gestures (nodding, waving, reaching)."
    },
    {
        "id": "response_latency_mean_sec",
        "name": "Mean Response Latency (s)",
        "modality": "behavioral",
        "typical_range": (1.0, 5.0),
        "mean_norm": 2.2,
        "std_norm": 0.8,
        "clinical_note": "Elevated latency between examiner social cue and child behavioral response."
    },

    # --- Modality 2: Visual Gaze & Oculomotor (Patent Reference 1) ---
    {
        "id": "fixation_count",
        "name": "Ocular Fixation Count",
        "modality": "visual_gaze",
        "typical_range": (20.0, 80.0),
        "mean_norm": 45.0,
        "std_norm": 12.0,
        "clinical_note": "Total count of sustained ocular fixations during social dynamic video stimulus."
    },
    {
        "id": "mean_fixation_duration_ms",
        "name": "Mean Fixation Duration (ms)",
        "modality": "visual_gaze",
        "typical_range": (150.0, 450.0),
        "mean_norm": 260.0,
        "std_norm": 65.0,
        "clinical_note": "Prolonged or hyper-fragmented gaze dwell time per fixation."
    },
    {
        "id": "social_roi_dwell_percentage",
        "name": "Social ROI Dwell %",
        "modality": "visual_gaze",
        "typical_range": (40.0, 90.0),
        "mean_norm": 72.0,
        "std_norm": 14.0,
        "clinical_note": "Percentage of total gaze time directed towards facial and social regions of interest."
    },
    {
        "id": "joint_attention_latency_ms",
        "name": "Joint Attention Latency (ms)",
        "modality": "visual_gaze",
        "typical_range": (300.0, 1200.0),
        "mean_norm": 520.0,
        "std_norm": 160.0,
        "clinical_note": "Speed in milliseconds to saccade towards target indicated by actor's gaze cue."
    },
    {
        "id": "saccade_mean_amplitude_deg",
        "name": "Saccade Mean Amplitude (°)",
        "modality": "visual_gaze",
        "typical_range": (4.0, 14.0),
        "mean_norm": 7.5,
        "std_norm": 2.1,
        "clinical_note": "Angular degree distance of rapid ocular transitions between fixation points."
    },
    {
        "id": "atypical_scanpath_entropy",
        "name": "Scanpath Spatial Entropy",
        "modality": "visual_gaze",
        "typical_range": (0.1, 0.9),
        "mean_norm": 0.40,
        "std_norm": 0.15,
        "clinical_note": "Information entropy of visual search path; higher indicates disorganized scanpath."
    },

    # --- Modality 3: Acoustic Prosody & Biomarkers (Research Paper 2 Reference) ---
    {
        "id": "fundamental_freq_f0_mean_hz",
        "name": "Mean Fundamental Frequency F0 (Hz)",
        "modality": "acoustic_prosody",
        "typical_range": (180.0, 320.0),
        "mean_norm": 240.0,
        "std_norm": 35.0,
        "clinical_note": "Average vocal pitch frequency across conversational or naming vocalizations."
    },
    {
        "id": "f0_pitch_variability_stdev_hz",
        "name": "Pitch Variability StDev (Hz)",
        "modality": "acoustic_prosody",
        "typical_range": (20.0, 65.0),
        "mean_norm": 42.0,
        "std_norm": 11.0,
        "clinical_note": "Monotone vs atypical pitch excursions (prosodic expressivity)."
    },
    {
        "id": "vocal_jitter_percent",
        "name": "Vocal Jitter (%)",
        "modality": "acoustic_prosody",
        "typical_range": (0.2, 2.5),
        "mean_norm": 0.85,
        "std_norm": 0.35,
        "clinical_note": "Short-term cycle-to-cycle perturbation in vocal fundamental frequency."
    },
    {
        "id": "vocal_shimmer_db",
        "name": "Vocal Shimmer (dB)",
        "modality": "acoustic_prosody",
        "typical_range": (0.1, 1.2),
        "mean_norm": 0.32,
        "std_norm": 0.15,
        "clinical_note": "Short-term cycle-to-cycle amplitude perturbation in speech waveform."
    },
    {
        "id": "pause_to_speech_ratio",
        "name": "Pause-to-Speech Ratio",
        "modality": "acoustic_prosody",
        "typical_range": (0.15, 0.60),
        "mean_norm": 0.30,
        "std_norm": 0.08,
        "clinical_note": "Ratio of silent pause hesitation intervals to active phonation time."
    },
    {
        "id": "formant_dispersion_hz",
        "name": "Formant Dispersion (Hz)",
        "modality": "acoustic_prosody",
        "typical_range": (800.0, 1600.0),
        "mean_norm": 1150.0,
        "std_norm": 120.0,
        "clinical_note": "Average frequency difference between adjacent formant frequencies."
    },
    {
        "id": "speech_rate_syllables_sec",
        "name": "Speech Rate (syllables/s)",
        "modality": "acoustic_prosody",
        "typical_range": (2.0, 5.5),
        "mean_norm": 3.6,
        "std_norm": 0.7,
        "clinical_note": "Estimated articulatory syllable generation speed per elapsed second."
    }
]

FEATURE_NAMES = [f["id"] for f in FEATURE_DEFINITIONS]
FEATURE_MAP = {f["id"]: f for f in FEATURE_DEFINITIONS}
TOTAL_FEATURE_DIM = len(FEATURE_NAMES)

