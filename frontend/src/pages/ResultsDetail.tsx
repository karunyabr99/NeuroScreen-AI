import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ScreeningDetail } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ShapWaterfallChart } from '../components/explainability/ShapWaterfallChart';
import { LimeFeatureBar } from '../components/explainability/LimeFeatureBar';
import { ModalityDistribution } from '../components/explainability/ModalityDistribution';
import { ModelStatusCard } from '../components/explainability/ModelStatusCard';
import { formatDateTime, formatRiskTier } from '../lib/utils';
import {
  Activity,
  ArrowLeft,
  Printer,
  Sparkles,
  ShieldAlert,
  Layers,
  FileCheck2,
  Clock,
  Download
} from 'lucide-react';

interface ResultsDetailProps {
  sessionId: string;
  onBack: () => void;
}

export const ResultsDetail: React.FC<ResultsDetailProps> = ({ sessionId, onBack }) => {
  const [detail, setDetail] = useState<ScreeningDetail | null>(null);
  const [activeTab, setActiveTab] = useState<'shap' | 'lime' | 'features'>('shap');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDetail() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.getScreeningDetail(sessionId);
        setDetail(data);
      } catch (err: any) {
        console.error("Failed to load screening detail:", err);
        setError(err.message || "Failed to retrieve screening session.");
      } finally {
        setIsLoading(false);
      }
    }
    loadDetail();
  }, [sessionId]);

  const [isDownloadingPdf, setIsDownloadingPdf] = useState<boolean>(false);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = async () => {
    if (!sessionId) return;
    setIsDownloadingPdf(true);
    try {
      const blob = await api.downloadReportPdf(sessionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `research_screening_summary_${sessionId.substring(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert("PDF download failed: " + err.message);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-16 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-neuro-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm text-slate-500">Loading screening decision-support metrics and explainability charts...</p>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="p-8 max-w-lg mx-auto text-center space-y-4">
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm">
          {error || "Screening session not found."}
        </div>
        <Button variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
        </Button>
      </div>
    );
  }

  const { session, features, explanations, model_status } = detail;
  const tier = formatRiskTier(session.risk_tier);
  const shapExp = explanations.find(e => e.method === 'SHAP');
  const limeExp = explanations.find(e => e.method === 'LIME');

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Action Bar */}
      <div className="flex items-center justify-between no-print">
        <Button variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Dashboard
        </Button>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleDownloadPdf} disabled={isDownloadingPdf}>
            <Download className="w-4 h-4 mr-1.5 text-neuro-600" />
            {isDownloadingPdf ? 'Generating PDF...' : 'Download Research Summary (PDF)'}
          </Button>

          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="w-4 h-4 mr-1.5" /> Print Record
          </Button>
        </div>
      </div>

      {/* Summary Header Card */}
      <Card className="border-slate-200">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-slate-400">SESSION #{session.id.substring(0, 12)}</span>
                <Badge variant="outline" className="text-[10px] font-mono">
                  {session.protocol_version}
                </Badge>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <Activity className="w-5 h-5 text-neuro-600" />
                Multimodal Screening-Support Evaluation
              </h1>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
                <span className="flex items-center gap-1 font-mono">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  {formatDateTime(session.created_at)}
                </span>
                <span>•</span>
                <span>Model: <strong className="text-slate-800">{model_status.model_name}</strong></span>
                <span>•</span>
                <span>Modalities: <strong className="text-slate-800">{session.modalities_included.join(', ')}</strong></span>
              </div>
            </div>

            {/* Risk Tier Card */}
            <div className={`p-4 rounded-xl border flex flex-col justify-center min-w-[260px] ${tier.bg} ${tier.border}`}>
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                Screening Triage Indication:
              </div>
              <div className={`text-lg font-bold mt-0.5 ${tier.color}`}>
                {tier.label}
              </div>
              <div className="text-[11px] text-slate-600 mt-1">
                {session.is_calibrated && typeof session.composite_risk_score === 'number' ? (
                  <span>Model Estimated Probability: <strong>{(session.composite_risk_score * 100).toFixed(1)}%</strong></span>
                ) : (
                  <span>Calibrated Risk: <span className="italic">Suspended (Weights Unmounted)</span></span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Narrative Alert */}
      {shapExp?.summary_narrative && (
        <div className="bg-neuro-50/80 border border-neuro-200/80 rounded-xl p-4 flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-neuro-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-semibold text-neuro-950">Deterministic Clinical Summary Narrative</h4>
            <p className="text-xs text-neuro-900 leading-relaxed">
              {shapExp.summary_narrative}
            </p>
          </div>
        </div>
      )}

      {/* Grid: Explainability Views & Sidebar Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main 2 Cols: SHAP & LIME charts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Sub Navigation */}
          <div className="flex border-b border-slate-200 gap-2 no-print">
            <button
              onClick={() => setActiveTab('shap')}
              className={`pb-2.5 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'shap'
                  ? 'border-neuro-600 text-neuro-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Layers className="w-4 h-4 text-neuro-600" />
              <span>SHAP Waterfall Attribution ({shapExp?.feature_importances.length || 0})</span>
            </button>

            <button
              onClick={() => setActiveTab('lime')}
              className={`pb-2.5 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'lime'
                  ? 'border-purple-600 text-purple-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <FileCheck2 className="w-4 h-4 text-purple-600" />
              <span>LIME Local Surrogate</span>
            </button>

            <button
              onClick={() => setActiveTab('features')}
              className={`pb-2.5 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'features'
                  ? 'border-slate-800 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Activity className="w-4 h-4 text-slate-700" />
              <span>Raw Modalities Data</span>
            </button>
          </div>

          {activeTab === 'shap' && shapExp && (
            <ShapWaterfallChart
              importances={shapExp.feature_importances}
              baseValue={shapExp.base_value}
              predictionValue={shapExp.prediction_value}
              isCalibrated={session.is_calibrated}
              calibrationNotice={shapExp.calibration_status_notice}
            />
          )}

          {activeTab === 'lime' && limeExp && (
            <LimeFeatureBar
              importances={limeExp.feature_importances}
              summaryNarrative={limeExp.summary_narrative}
            />
          )}

          {activeTab === 'features' && (
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Extracted Modality Payloads</CardTitle>
                <CardDescription>Structured metrics persisted in the SQLite screening record</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {features.map((feat) => (
                  <div key={feat.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-800 mb-2">
                      <span className="capitalize">{feat.modality_type.replace('_', ' ')}</span>
                      <span className="text-slate-400 font-mono text-[10px]">Signal Quality: {(feat.quality_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="bg-white p-2.5 rounded border border-slate-200 font-mono text-[11px] max-h-40 overflow-y-auto">
                      <pre>{JSON.stringify(feat.extracted_features, null, 2)}</pre>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar 1 Col: Modality Distribution & Model Verification */}
        <div className="space-y-6">
          {shapExp && (
            <ModalityDistribution breakdown={shapExp.modality_breakdown} />
          )}

          <ModelStatusCard modelStatus={model_status} />

          {/* Clinical Safeguard Alert */}
          <Card className="border-slate-200 bg-slate-50/50">
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                <ShieldAlert className="w-4 h-4 text-amber-600" />
                <span>Screening-Support Protocol</span>
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                This report displays standardized feature deviations across all 24 modalities.
                Results must be correlated with parent clinical history, child interaction observation,
                and formal psychological evaluation.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
