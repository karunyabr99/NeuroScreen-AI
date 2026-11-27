import React from 'react';
import { AcousticProsodyInput } from '../../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Mic } from 'lucide-react';

interface AcousticProsodyAssessmentProps {
  value: AcousticProsodyInput;
  onChange: (value: AcousticProsodyInput) => void;
}

export const AcousticProsodyAssessment: React.FC<AcousticProsodyAssessmentProps> = ({ value, onChange }) => {
  return (
    <Card className="border-slate-200">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Mic className="w-4 h-4 text-purple-600" />
          Modality 3: Acoustic Prosody & Vocal Biomarkers (Research Paper 2)
        </CardTitle>
        <CardDescription>
          Fundamental frequency ($F_0$) modulation, vocal jitter perturbation, and conversational turn-taking pause dynamics
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Pitch Variability */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-slate-800">F0 Pitch Variability StDev:</span>
              <span className="text-xs font-mono font-bold text-purple-700">{value.f0_pitch_variability_stdev_hz.toFixed(1)} Hz</span>
            </div>
            <input
              type="range"
              min="5"
              max="90"
              step="1"
              value={value.f0_pitch_variability_stdev_hz}
              onChange={(e) => onChange({ ...value, f0_pitch_variability_stdev_hz: parseFloat(e.target.value) })}
              className="w-full accent-purple-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
              <span>&lt; 20 Hz (Monotone intonation)</span>
              <span>Normative: ~42 Hz</span>
              <span>&gt; 70 Hz (Atypical sing-song)</span>
            </div>
          </div>

          {/* Pause to speech ratio */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-slate-800">Pause-to-Speech Ratio:</span>
              <span className="text-xs font-mono font-bold text-purple-700">{(value.pause_to_speech_ratio * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.80"
              step="0.01"
              value={value.pause_to_speech_ratio}
              onChange={(e) => onChange({ ...value, pause_to_speech_ratio: parseFloat(e.target.value) })}
              className="w-full accent-purple-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
              <span>10% (Continuous phonation)</span>
              <span>Normative: ~30%</span>
              <span>80% (Hesitation / Atypical pauses)</span>
            </div>
          </div>

          {/* Vocal Jitter */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-slate-800">Vocal Jitter Perturbation:</span>
              <span className="text-xs font-mono font-bold text-purple-700">{value.vocal_jitter_percent.toFixed(2)}%</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="4.00"
              step="0.05"
              value={value.vocal_jitter_percent}
              onChange={(e) => onChange({ ...value, vocal_jitter_percent: parseFloat(e.target.value) })}
              className="w-full accent-purple-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
              <span>0.2% (Steady vocal cords)</span>
              <span>Normative: ~0.85%</span>
              <span>4.0% (Micro-tremor perturbation)</span>
            </div>
          </div>

          {/* Articulation rate */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-slate-800">Speech Articulation Rate:</span>
              <span className="text-xs font-mono font-bold text-purple-700">{value.speech_rate_syllables_sec.toFixed(1)} syl/sec</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="6.0"
              step="0.1"
              value={value.speech_rate_syllables_sec}
              onChange={(e) => onChange({ ...value, speech_rate_syllables_sec: parseFloat(e.target.value) })}
              className="w-full accent-purple-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
              <span>1.0 (Labored / Delayed)</span>
              <span>Normative: ~3.6</span>
              <span>6.0 (Pressured speech)</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

