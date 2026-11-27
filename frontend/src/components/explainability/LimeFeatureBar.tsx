import React from 'react';
import { FeatureContribution } from '../../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { SlidersHorizontal, ArrowUpRight, ArrowDownRight, ShieldAlert } from 'lucide-react';

interface LimeFeatureBarProps {
  importances: FeatureContribution[];
  summaryNarrative: string;
}

export const LimeFeatureBar: React.FC<LimeFeatureBarProps> = ({ importances, summaryNarrative }) => {
  // Take top 8 highest impact features for LIME
  const topFeatures = importances.slice(0, 8);
  const maxAbs = Math.max(...topFeatures.map(f => Math.abs(f.importance_value)), 0.05);

  return (
    <Card className="border-slate-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-purple-600" />
            LIME Local Decision Surrogate Weights
          </CardTitle>
          <Badge variant="outline" className="text-[10px]">Local Linear Approximation</Badge>
        </div>
        <CardDescription>
          Interpretable local surrogate modeling of feature boundaries in the neighborhood of this patient's profile
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {summaryNarrative && (
          <div className="bg-purple-50/70 border border-purple-200/60 rounded-lg p-3 text-xs text-purple-900 leading-relaxed">
            {summaryNarrative}
          </div>
        )}

        {topFeatures.length === 0 ? (
          <div className="p-8 text-center space-y-3 bg-slate-50 border border-dashed border-slate-200 rounded-xl my-2">
            <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center mx-auto text-amber-700">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div className="text-xs font-semibold text-slate-800">
              LIME Local Surrogate Suspended (Model Uncalibrated)
            </div>
            <p className="text-[11px] text-slate-500 max-w-md mx-auto leading-relaxed">
              Local linear surrogate approximations require an active trained decision function. Calculations are suspended until a certified checkpoint is mounted into <code className="text-slate-700">ml_engine/weights/</code>.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {topFeatures.map((feat) => {
            const isPos = feat.importance_value > 0;
            const pct = Math.min(100, Math.round((Math.abs(feat.importance_value) / maxAbs) * 100));

            return (
              <div key={feat.feature_name} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-800">{feat.display_name}</span>
                  <span className={`font-mono font-semibold flex items-center ${
                    isPos ? 'text-rose-600' : 'text-emerald-600'
                  }`}>
                    {isPos ? <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> : <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />}
                    {isPos ? `+${feat.importance_value.toFixed(4)}` : feat.importance_value.toFixed(4)}
                  </span>
                </div>

                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden flex items-center">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      isPos ? 'bg-purple-600' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
        )}
      </CardContent>
    </Card>
  );
};

