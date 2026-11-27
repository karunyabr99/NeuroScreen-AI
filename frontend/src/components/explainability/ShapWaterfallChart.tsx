import React, { useState } from 'react';
import { FeatureContribution } from '../../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { HelpCircle, ArrowUpRight, ArrowDownRight, Layers, Eye, Mic, Activity, ShieldAlert } from 'lucide-react';

interface ShapWaterfallChartProps {
  importances: FeatureContribution[];
  baseValue: number;
  predictionValue: number;
  isCalibrated: boolean;
  calibrationNotice?: string;
}

export const ShapWaterfallChart: React.FC<ShapWaterfallChartProps> = ({
  importances,
  baseValue,
  predictionValue,
  isCalibrated,
  calibrationNotice
}) => {
  const [filterModality, setFilterModality] = useState<string>('all');
  const [selectedFeature, setSelectedFeature] = useState<FeatureContribution | null>(null);

  const filtered = importances.filter(f => 
    filterModality === 'all' ? true : f.modality === filterModality
  );

  const maxAbsValue = Math.max(...importances.map(f => Math.abs(f.importance_value)), 0.1);

  const getModalityIcon = (mod: string) => {
    switch (mod) {
      case 'behavioral': return <Activity className="w-3.5 h-3.5 text-blue-600" />;
      case 'visual_gaze': return <Eye className="w-3.5 h-3.5 text-teal-600" />;
      case 'acoustic_prosody': return <Mic className="w-3.5 h-3.5 text-purple-600" />;
      default: return null;
    }
  };

  const getModalityBadge = (mod: string) => {
    switch (mod) {
      case 'behavioral': return <Badge variant="info">Behavioral</Badge>;
      case 'visual_gaze': return <Badge variant="success">Visual Gaze</Badge>;
      case 'acoustic_prosody': return <Badge variant="default">Acoustic Prosody</Badge>;
      default: return null;
    }
  };

  return (
    <Card className="border-slate-200">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Layers className="w-4 h-4 text-neuro-600" />
                SHAP Multimodal Feature Attribution Waterfall
              </CardTitle>
              {!isCalibrated && (
                <Badge variant="warning" className="text-[10px]">Uncalibrated Baseline</Badge>
              )}
            </div>
            <CardDescription>
              Shapley values indicating individual feature shifts toward elevated risk (+) or typical baseline (-). Base expected value E[f(x)]: {baseValue.toFixed(2)}, instance attribution: {predictionValue.toFixed(2)}
            </CardDescription>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
            <button
              onClick={() => setFilterModality('all')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filterModality === 'all' ? 'bg-white text-slate-900 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All ({importances.length})
            </button>
            <button
              onClick={() => setFilterModality('behavioral')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filterModality === 'behavioral' ? 'bg-white text-blue-700 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Behavioral
            </button>
            <button
              onClick={() => setFilterModality('visual_gaze')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filterModality === 'visual_gaze' ? 'bg-white text-teal-700 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Visual
            </button>
            <button
              onClick={() => setFilterModality('acoustic_prosody')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filterModality === 'acoustic_prosody' ? 'bg-white text-purple-700 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Acoustic
            </button>
          </div>
        </div>

        {calibrationNotice && (
          <div className="mt-2 text-[11px] text-amber-700 bg-amber-50/80 px-3 py-1.5 rounded-md border border-amber-200/60">
            {calibrationNotice}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Waterfall Chart Bars */}
        <div className="space-y-2 max-h-[460px] overflow-y-auto pr-2">
          {filtered.length === 0 && (
            <div className="p-8 text-center space-y-3 bg-slate-50 border border-dashed border-slate-200 rounded-xl my-2">
              <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center mx-auto text-amber-700">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div className="text-xs font-semibold text-slate-800">
                Explainability Calculation Suspended (Model Uncalibrated)
              </div>
              <p className="text-[11px] text-slate-500 max-w-md mx-auto leading-relaxed">
                In strict adherence to clinical AI safety governance, feature importance attribution is not computed on uncalibrated models. Heuristic or simulated values are prohibited. Attribution will activate automatically when a verified checkpoint is mounted into <code className="text-slate-700">ml_engine/weights/</code>.
              </p>
            </div>
          )}
          {filtered.map((item) => {
            const isPositive = item.importance_value > 0;
            const pct = Math.min(100, Math.round((Math.abs(item.importance_value) / maxAbsValue) * 100));
            const isSelected = selectedFeature?.feature_name === item.feature_name;

            return (
              <div
                key={item.feature_name}
                onClick={() => setSelectedFeature(isSelected ? null : item)}
                className={`p-2.5 rounded-lg border transition-all cursor-pointer ${
                  isSelected 
                    ? 'border-neuro-500 bg-neuro-50/50 shadow-xs' 
                    : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50/60'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <div className="flex items-center gap-2">
                    {getModalityIcon(item.modality)}
                    <span className="font-semibold text-slate-800">{item.display_name}</span>
                    <span className="text-slate-400 font-mono text-[11px]">val: {item.feature_value}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`font-mono font-semibold flex items-center ${
                      isPositive ? 'text-rose-600' : 'text-emerald-600'
                    }`}>
                      {isPositive ? <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> : <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />}
                      {isPositive ? `+${item.importance_value.toFixed(4)}` : item.importance_value.toFixed(4)}
                    </span>
                    {getModalityBadge(item.modality)}
                  </div>
                </div>

                {/* Relative Bar */}
                <div className="relative w-full h-3 bg-slate-100 rounded-full overflow-hidden flex items-center">
                  <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-slate-300 z-10" />

                  {isPositive ? (
                    <div
                      className="h-full bg-gradient-to-r from-rose-400 to-rose-600 rounded-r-full transition-all duration-300"
                      style={{
                        marginLeft: '50%',
                        width: `${pct * 0.5}%`
                      }}
                    />
                  ) : (
                    <div
                      className="h-full bg-gradient-to-l from-emerald-400 to-emerald-600 rounded-l-full transition-all duration-300 ml-auto"
                      style={{
                        marginRight: '50%',
                        width: `${pct * 0.5}%`
                      }}
                    />
                  )}
                </div>

                {/* Expanded Clinical Description */}
                {isSelected && (
                  <div className="mt-2.5 pt-2 border-t border-slate-200/80 text-[11px] text-slate-600 bg-white p-2.5 rounded-md">
                    <div className="flex items-center gap-1.5 text-neuro-700 font-medium mb-1">
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Clinical Significance (Reference Specification):</span>
                    </div>
                    <p className="leading-relaxed">{item.clinical_note}</p>
                    <div className="mt-1 flex items-center gap-4 text-slate-400 text-[10px]">
                      <span>Feature Identifier: <code className="text-slate-600">{item.feature_name}</code></span>
                      <span>Direction: <strong>{item.direction.replace('_', ' ')}</strong></span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-500">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
              <span>Elevates Screening Risk</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span>Protective / Typical Baseline</span>
            </span>
          </div>
          <span className="text-[11px] text-slate-400">Click any feature to inspect clinical literature context</span>
        </div>
      </CardContent>
    </Card>
  );
};
