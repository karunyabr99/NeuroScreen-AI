import React from 'react';
import { ModelStatus } from '../../types';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Cpu, CheckCircle2, AlertTriangle, FolderGit2 } from 'lucide-react';

interface ModelStatusCardProps {
  modelStatus: ModelStatus;
}

export const ModelStatusCard: React.FC<ModelStatusCardProps> = ({ modelStatus }) => {
  return (
    <Card className="border-slate-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Cpu className="w-4 h-4 text-neuro-600" />
            Model Architecture & Verification Contract
          </CardTitle>
          {modelStatus.is_calibrated ? (
            <Badge variant="success" className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>Calibrated Live Checkpoint</span>
            </Badge>
          ) : (
            <Badge variant="warning" className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              <span>Modular Uncalibrated Mode</span>
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 text-xs">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <span className="text-slate-400">Selected Engine:</span>
            <div className="font-semibold text-slate-800">{modelStatus.model_name}</div>
          </div>
          <div>
            <span className="text-slate-400">Architecture Family:</span>
            <div className="font-semibold text-slate-800">{modelStatus.model_family}</div>
          </div>
          <div>
            <span className="text-slate-400">Feature Dimensions:</span>
            <div className="font-semibold text-slate-800 font-mono">{modelStatus.input_feature_dim} Aligned Dimensions</div>
          </div>
          <div>
            <span className="text-slate-400">Explainers:</span>
            <div className="font-semibold text-slate-800">{modelStatus.supported_explainers.join(' & ')}</div>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70 text-slate-600 leading-relaxed text-[11px]">
          <p className="mb-1">{modelStatus.architecture_description}</p>
          <div className="flex items-center gap-1 text-slate-400 font-mono text-[10px]">
            <FolderGit2 className="w-3 h-3" />
            <span>Weights directory: <code>ml_engine/weights/</code></span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

