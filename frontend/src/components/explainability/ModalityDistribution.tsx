import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { PieChart, Activity, Eye, Mic } from 'lucide-react';

interface ModalityDistributionProps {
  breakdown: {
    behavioral: number;
    visual_gaze: number;
    acoustic_prosody: number;
  };
}

export const ModalityDistribution: React.FC<ModalityDistributionProps> = ({ breakdown }) => {
  const beh = breakdown.behavioral || 0;
  const vis = breakdown.visual_gaze || 0;
  const aud = breakdown.acoustic_prosody || 0;
  const isSuspended = beh === 0 && vis === 0 && aud === 0;

  return (
    <Card className="border-slate-200">
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <PieChart className="w-4 h-4 text-neuro-600" />
          Multimodal Evidence Weight Distribution
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Multi-segmented progress bar */}
        <div className="w-full h-3 rounded-full overflow-hidden flex bg-slate-100 shadow-inner">
          <div
            className="bg-blue-600 transition-all duration-500"
            style={{ width: `${beh}%` }}
            title={`Behavioral: ${beh}%`}
          />
          <div
            className="bg-teal-500 transition-all duration-500"
            style={{ width: `${vis}%` }}
            title={`Visual Gaze: ${vis}%`}
          />
          <div
            className="bg-purple-600 transition-all duration-500"
            style={{ width: `${aud}%` }}
            title={`Acoustic Prosody: ${aud}%`}
          />
        </div>

        {isSuspended ? (
          <div className="text-[11px] text-slate-400 text-center py-2 italic bg-slate-50 rounded-lg border border-slate-100">
            Evidence distribution suspended until model calibration.
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2.5 rounded-lg bg-blue-50/70 border border-blue-100">
              <div className="flex items-center justify-center gap-1 text-blue-700 font-semibold mb-1">
                <Activity className="w-3.5 h-3.5" />
                <span>Behavioral</span>
              </div>
              <div className="text-lg font-bold text-blue-900 font-mono">{beh}%</div>
              <div className="text-[10px] text-blue-600/80">Psychometrics</div>
            </div>

            <div className="p-2.5 rounded-lg bg-teal-50/70 border border-teal-100">
              <div className="flex items-center justify-center gap-1 text-teal-700 font-semibold mb-1">
                <Eye className="w-3.5 h-3.5" />
                <span>Visual Gaze</span>
              </div>
              <div className="text-lg font-bold text-teal-900 font-mono">{vis}%</div>
              <div className="text-[10px] text-teal-600/80">Ocular Dynamics</div>
            </div>

            <div className="p-2.5 rounded-lg bg-purple-50/70 border border-purple-100">
              <div className="flex items-center justify-center gap-1 text-purple-700 font-semibold mb-1">
                <Mic className="w-3.5 h-3.5" />
                <span>Acoustic</span>
              </div>
              <div className="text-lg font-bold text-purple-900 font-mono">{aud}%</div>
              <div className="text-[10px] text-purple-600/80">Vocal Biomarkers</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
