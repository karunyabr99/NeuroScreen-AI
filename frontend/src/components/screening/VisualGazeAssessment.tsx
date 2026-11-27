import React from 'react';
import { VisualGazeInput } from '../../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Eye } from 'lucide-react';

interface VisualGazeAssessmentProps {
  value: VisualGazeInput;
  onChange: (value: VisualGazeInput) => void;
}

export const VisualGazeAssessment: React.FC<VisualGazeAssessmentProps> = ({ value, onChange }) => {
  return (
    <Card className="border-slate-200">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Eye className="w-4 h-4 text-teal-600" />
          Modality 2: Visual Ocular & Scanpath Metrics (Patent Reference 1)
        </CardTitle>
        <CardDescription>
          Automated eye-tracking fixation dynamics, social region-of-interest (ROI) dwell percentage, and saccade amplitude
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Social ROI Dwell */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-slate-800">Social / Facial ROI Dwell:</span>
              <span className="text-xs font-mono font-bold text-teal-700">{value.social_roi_dwell_percentage}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              value={value.social_roi_dwell_percentage}
              onChange={(e) => onChange({ ...value, social_roi_dwell_percentage: parseFloat(e.target.value) })}
              className="w-full accent-teal-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
              <span>0% (Atypical: Abstract preference)</span>
              <span>Typical: &gt;65%</span>
              <span>100% (High social focus)</span>
            </div>
          </div>

          {/* Joint Attention Latency */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-slate-800">Joint Attention Saccade Latency:</span>
              <span className="text-xs font-mono font-bold text-teal-700">{value.joint_attention_latency_ms} ms</span>
            </div>
            <input
              type="range"
              min="100"
              max="2000"
              step="10"
              value={value.joint_attention_latency_ms}
              onChange={(e) => onChange({ ...value, joint_attention_latency_ms: parseFloat(e.target.value) })}
              className="w-full accent-teal-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
              <span>100 ms (Rapid)</span>
              <span>Normative: ~520 ms</span>
              <span>2000 ms (Delayed)</span>
            </div>
          </div>

          {/* Fixation Count */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-slate-800">Fixation Count (Stimulus Duration):</span>
              <span className="text-xs font-mono font-bold text-teal-700">{value.fixation_count} fixations</span>
            </div>
            <input
              type="range"
              min="10"
              max="150"
              step="1"
              value={value.fixation_count}
              onChange={(e) => onChange({ ...value, fixation_count: parseInt(e.target.value) })}
              className="w-full accent-teal-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
              <span>10 (Sparse fixations)</span>
              <span>Normative: ~45</span>
              <span>150 (Hyper-fragmented)</span>
            </div>
          </div>

          {/* Scanpath Entropy */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-slate-800">Scanpath Spatial Entropy:</span>
              <span className="text-xs font-mono font-bold text-teal-700">{value.atypical_scanpath_entropy.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.95"
              step="0.01"
              value={value.atypical_scanpath_entropy}
              onChange={(e) => onChange({ ...value, atypical_scanpath_entropy: parseFloat(e.target.value) })}
              className="w-full accent-teal-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
              <span>0.10 (Predictable structured gaze)</span>
              <span>Normative: ~0.40</span>
              <span>0.90 (Disorganized scanpath)</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

