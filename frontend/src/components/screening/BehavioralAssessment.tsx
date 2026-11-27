import React from 'react';
import { BehavioralInput } from '../../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Activity } from 'lucide-react';

interface BehavioralAssessmentProps {
  value: BehavioralInput;
  onChange: (value: BehavioralInput) => void;
}

const ITEMS: { key: keyof BehavioralInput; label: string; description: string }[] = [
  {
    key: "social_smile_reciprocity",
    label: "Reciprocal Social Smiling",
    description: "Response smile when examiner or caregiver smiles directly (Flag if atypical/absent)"
  },
  {
    key: "name_call_orientation",
    label: "Name Call Orientation",
    description: "Orienting head or gaze upon examiner calling patient's name clearly"
  },
  {
    key: "pointing_proto_declarative",
    label: "Proto-Declarative Pointing",
    description: "Pointing with index finger to direct adult's attention to an object of shared interest"
  },
  {
    key: "pretend_play_engagement",
    label: "Pretend / Imaginative Symbolic Play",
    description: "Spontaneous pretend play (e.g. feeding a doll, toy car sounds, imaginary tea)"
  },
  {
    key: "repetitive_motor_mannerisms",
    label: "Repetitive Motor Stereotypies",
    description: "Observation of hand-flapping, finger flicking, or rhythmic whole-body swaying"
  },
  {
    key: "monotropic_focus_intensity",
    label: "Monotropic / Fixated Focus",
    description: "Intense fixation on specific mechanical parts or non-functional object features"
  },
  {
    key: "gaze_alternation_dyadic",
    label: "Dyadic Gaze Alternation",
    description: "Fluid gaze shifting between an interesting toy and the examiner to share affect"
  },
  {
    key: "sensory_hypersensitivity",
    label: "Sensory Reactivity Peculiarities",
    description: "Pronounced aversion or unusual fascination with sounds, textures, or lights"
  },
  {
    key: "peer_social_interest",
    label: "Peer Interaction Orientation",
    description: "Showing spontaneous curiosity or interest in other children nearby"
  },
  {
    key: "gestural_communication",
    label: "Descriptive Gestures",
    description: "Use of expressive gestures (nodding, waving goodbye, shrugging, reaching)"
  }
];

export const BehavioralAssessment: React.FC<BehavioralAssessmentProps> = ({ value, onChange }) => {
  const toggleItem = (key: keyof BehavioralInput) => {
    const current = value[key] as number;
    onChange({
      ...value,
      [key]: current === 1 ? 0 : 1
    });
  };

  const activeCount = Object.keys(value)
    .filter(k => k !== 'response_latency_mean_sec')
    .reduce((acc, k) => acc + (value[k as keyof BehavioralInput] === 1 ? 1 : 0), 0);

  return (
    <Card className="border-slate-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              Modality 1: Psychometric & Behavioral Features (Research Paper 1)
            </CardTitle>
            <CardDescription>
              Digitized AQ-10 & M-CHAT social communication and repetitive behavior observation items
            </CardDescription>
          </div>
          <div className="bg-blue-50 text-blue-700 font-mono text-xs px-2.5 py-1 rounded-md font-semibold">
            {activeCount} / 10 Indicators Flagged
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {ITEMS.map((item) => {
            const isFlagged = value[item.key] === 1;

            return (
              <div
                key={item.key}
                onClick={() => toggleItem(item.key)}
                className={`p-3 rounded-lg border cursor-pointer transition-all flex items-start gap-3 ${
                  isFlagged
                    ? 'border-rose-300 bg-rose-50/70 shadow-xs'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className={`mt-0.5 w-5 h-5 rounded flex items-center justify-center flex-shrink-0 border transition-colors ${
                  isFlagged
                    ? 'bg-rose-600 border-rose-600 text-white'
                    : 'border-slate-300 bg-slate-50'
                }`}>
                  {isFlagged && (
                    <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 20 20">
                      <path d="M0 11l2-2 5 5L18 3l2 2L7 18z"/>
                    </svg>
                  )}
                </div>

                <div className="flex-1">
                  <div className="text-xs font-semibold text-slate-800">{item.label}</div>
                  <div className="text-[11px] text-slate-500 leading-snug mt-0.5">{item.description}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Continuous Response Latency */}
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-slate-800">Mean Behavioral Social Response Latency:</span>
            <span className="text-xs font-mono font-bold text-neuro-700">{value.response_latency_mean_sec.toFixed(1)} seconds</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="10.0"
            step="0.1"
            value={value.response_latency_mean_sec}
            onChange={(e) => onChange({ ...value, response_latency_mean_sec: parseFloat(e.target.value) })}
            className="w-full accent-neuro-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>0.5s (Rapid typical orientation)</span>
            <span>Normative: ~2.2s</span>
            <span>10.0s (Severe orientation latency)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

