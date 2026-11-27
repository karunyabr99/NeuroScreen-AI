import React from 'react';
import { BehavioralInput, VisualGazeInput, AcousticProsodyInput } from '../../types';
import { Button } from '../ui/Button';
import { Sparkles, CheckCircle, AlertTriangle, HelpCircle } from 'lucide-react';

interface ClinicalPresetSelectorProps {
  onApplyPreset: (
    behavioral: BehavioralInput,
    visual: VisualGazeInput,
    acoustic: AcousticProsodyInput,
    presetName: string
  ) => void;
}

export const ClinicalPresetSelector: React.FC<ClinicalPresetSelectorProps> = ({ onApplyPreset }) => {
  const applyPreset1 = () => {
    // High Risk Indicators Scenario (Research Paper 1 + 2 & Patent 1 convergence)
    onApplyPreset(
      {
        social_smile_reciprocity: 1,
        name_call_orientation: 1,
        pointing_proto_declarative: 1,
        pretend_play_engagement: 1,
        repetitive_motor_mannerisms: 1,
        monotropic_focus_intensity: 1,
        gaze_alternation_dyadic: 1,
        sensory_hypersensitivity: 1,
        peer_social_interest: 1,
        gestural_communication: 1,
        response_latency_mean_sec: 4.2
      },
      {
        fixation_count: 32,
        mean_fixation_duration_ms: 380.0,
        social_roi_dwell_percentage: 38.0,
        joint_attention_latency_ms: 1100.0,
        saccade_mean_amplitude_deg: 5.4,
        atypical_scanpath_entropy: 0.76
      },
      {
        fundamental_freq_f0_mean_hz: 275.0,
        f0_pitch_variability_stdev_hz: 16.0,
        vocal_jitter_percent: 2.1,
        vocal_shimmer_db: 0.75,
        pause_to_speech_ratio: 0.52,
        formant_dispersion_hz: 980.0,
        speech_rate_syllables_sec: 2.1
      },
      "Research Case A: High Multimodal Atypia"
    );
  };

  const applyPreset2 = () => {
    // Mixed / Moderate Profile
    onApplyPreset(
      {
        social_smile_reciprocity: 0,
        name_call_orientation: 1,
        pointing_proto_declarative: 0,
        pretend_play_engagement: 1,
        repetitive_motor_mannerisms: 0,
        monotropic_focus_intensity: 1,
        gaze_alternation_dyadic: 0,
        sensory_hypersensitivity: 1,
        peer_social_interest: 1,
        gestural_communication: 0,
        response_latency_mean_sec: 2.6
      },
      {
        fixation_count: 48,
        mean_fixation_duration_ms: 270.0,
        social_roi_dwell_percentage: 54.0,
        joint_attention_latency_ms: 680.0,
        saccade_mean_amplitude_deg: 7.2,
        atypical_scanpath_entropy: 0.48
      },
      {
        fundamental_freq_f0_mean_hz: 245.0,
        f0_pitch_variability_stdev_hz: 34.0,
        vocal_jitter_percent: 1.15,
        vocal_shimmer_db: 0.38,
        pause_to_speech_ratio: 0.36,
        formant_dispersion_hz: 1140.0,
        speech_rate_syllables_sec: 3.2
      },
      "Research Case B: Moderate / Mixed Profile"
    );
  };

  const applyPreset3 = () => {
    // Typical Normative Control
    onApplyPreset(
      {
        social_smile_reciprocity: 0,
        name_call_orientation: 0,
        pointing_proto_declarative: 0,
        pretend_play_engagement: 0,
        repetitive_motor_mannerisms: 0,
        monotropic_focus_intensity: 0,
        gaze_alternation_dyadic: 0,
        sensory_hypersensitivity: 0,
        peer_social_interest: 0,
        gestural_communication: 0,
        response_latency_mean_sec: 1.8
      },
      {
        fixation_count: 52,
        mean_fixation_duration_ms: 240.0,
        social_roi_dwell_percentage: 78.0,
        joint_attention_latency_ms: 420.0,
        saccade_mean_amplitude_deg: 8.5,
        atypical_scanpath_entropy: 0.32
      },
      {
        fundamental_freq_f0_mean_hz: 235.0,
        f0_pitch_variability_stdev_hz: 48.0,
        vocal_jitter_percent: 0.72,
        vocal_shimmer_db: 0.26,
        pause_to_speech_ratio: 0.25,
        formant_dispersion_hz: 1220.0,
        speech_rate_syllables_sec: 4.1
      },
      "Research Case C: Typical Baseline Control"
    );
  };

  return (
    <div className="bg-gradient-to-r from-neuro-50 to-sky-50 border border-neuro-100 rounded-xl p-4 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-neuro-600" />
          <span className="text-xs font-semibold text-neuro-900">Load Research Benchmark Profiles:</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={applyPreset1}
            className="text-xs border-rose-200 text-rose-700 hover:bg-rose-50"
          >
            <AlertTriangle className="w-3.5 h-3.5 mr-1 text-rose-600" />
            Case A: High Atypia
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={applyPreset2}
            className="text-xs border-amber-200 text-amber-700 hover:bg-amber-50"
          >
            <HelpCircle className="w-3.5 h-3.5 mr-1 text-amber-600" />
            Case B: Mixed
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={applyPreset3}
            className="text-xs border-emerald-200 text-emerald-700 hover:bg-emerald-50"
          >
            <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-600" />
            Case C: Typical Baseline
          </Button>
        </div>
      </div>
    </div>
  );
};

