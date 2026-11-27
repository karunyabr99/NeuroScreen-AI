import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { DatasetOverview } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
  Database,
  Download,
  AlertTriangle,
  PlayCircle,
  Sparkles,
  BarChart3,
  CheckCircle2,
  Users,
  Layers,
  FileSpreadsheet,
  Cpu
} from 'lucide-react';

export const DatasetManagement: React.FC = () => {
  const [overview, setOverview] = useState<DatasetOverview | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [exportType, setExportType] = useState<'real' | 'synthetic' | 'all'>('real');
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [isGeneratingDev, setIsGeneratingDev] = useState<boolean>(false);

  // ML Training Pipeline State
  const [eligibilityReport, setEligibilityReport] = useState<any>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [trainingResult, setTrainingResult] = useState<any>(null);
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadOverview = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDatasetOverview();
      setOverview(data);
    } catch (err: any) {
      console.error("Failed to load dataset overview:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  const handleExportCsv = async () => {
    setIsExporting(true);
    try {
      const blob = await api.exportDatasetCsv(exportType);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `neuroscreen_${exportType}_dataset_${new Date().toISOString().substring(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert("Export failed: " + err.message);
    } finally {
      setIsExporting(false);
    }
  };

  const handleGenerateBenchmark = async () => {
    if (!confirm("Generate 60 synthetic development participant records (tagged is_synthetic=True) for software testing?")) return;
    setIsGeneratingDev(true);
    try {
      const res = await api.generateBenchmarkCohort(60, 0.5);
      setStatusMessage(res.message);
      await loadOverview();
    } catch (err: any) {
      alert("Error generating benchmark cohort: " + err.message);
    } finally {
      setIsGeneratingDev(false);
    }
  };

  const handleEvaluateEligibility = async () => {
    setIsEvaluating(true);
    try {
      const res = await api.evaluateTrainingEligibility();
      setEligibilityReport(res.eligibility_report);
    } catch (err: any) {
      alert("Eligibility evaluation failed: " + err.message);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleRunTraining = async (trainOnBenchmark: boolean) => {
    setIsTraining(true);
    setTrainingResult(null);
    try {
      const res = await api.runTrainingPipeline(trainOnBenchmark, false);
      setTrainingResult(res);
    } catch (err: any) {
      alert("Training run failed: " + err.message);
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Database className="w-5 h-5 text-neuro-600" />
            Research Dataset Management & ML Training Prep
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Cohort management, data quality assurance, de-identified CSV exports, and leakage-free cross-validation
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleGenerateBenchmark} disabled={isGeneratingDev}>
            <Sparkles className="w-3.5 h-3.5 mr-1 text-purple-600" />
            {isGeneratingDev ? 'Generating...' : 'Seed Dev Benchmark Cohort'}
          </Button>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 rounded-xl bg-purple-50 border border-purple-200 text-xs text-purple-800 flex items-center justify-between">
          <span>{statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-purple-600 font-bold">&times;</button>
        </div>
      )}

      {isLoading && !overview && (
        <div className="p-12 text-center text-xs text-slate-500 space-y-2">
          <div className="w-6 h-6 border-2 border-neuro-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p>Loading research cohort and dataset metrics...</p>
        </div>
      )}

      {/* Top Level Metric Cards */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="border-slate-200">
            <CardContent className="p-4 space-y-1">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 flex items-center gap-1">
                <Users className="w-3 h-3 text-neuro-600" /> Participants
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900">{overview.total_participants}</span>
                <span className="text-[11px] text-emerald-600 font-semibold">{overview.real_participants} Real</span>
              </div>
              <p className="text-[10px] text-purple-600 font-mono">{overview.synthetic_participants} Synthetic Dev</p>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardContent className="p-4 space-y-1">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 flex items-center gap-1">
                <Layers className="w-3 h-3 text-neuro-600" /> Screening Sessions
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900">{overview.total_sessions}</span>
                <span className="text-[11px] text-slate-500">{overview.real_sessions} Real Sessions</span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono">{overview.total_research_assessments} Multi-Forms</p>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardContent className="p-4 space-y-1">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Consented Cohort
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-emerald-700">{overview.consented_real_participants}</span>
                <span className="text-[11px] text-slate-500">of {overview.real_participants} Verified</span>
              </div>
              <p className="text-[10px] text-rose-500 font-mono">{overview.withdrawn_participants} Withdrawn</p>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardContent className="p-4 space-y-1">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 flex items-center gap-1">
                <Cpu className="w-3 h-3 text-sky-600" /> Dataset Version
              </span>
              <div className="text-sm font-bold text-slate-800 font-mono truncate">{overview.dataset_version}</div>
              <p className="text-[10px] text-slate-400">IRB-NS-2026 Protocol</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Warnings & Duplicate Alerts */}
      {overview && overview.data_quality_warnings.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
          <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>Dataset Integrity & Quality Alerts ({overview.data_quality_warnings.length})</span>
          </div>
          <ul className="list-disc pl-5 text-[11px] text-amber-800 space-y-1">
            {overview.data_quality_warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Cohort Distributions & Modality Completeness Grid */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Age Distribution */}
          <Card className="border-slate-200">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-neuro-600" />
                Participant Age Distribution (Completed Months)
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {Object.entries(overview.age_distribution).map(([bin, count]) => {
                const pct = overview.total_participants > 0 ? (count / overview.total_participants) * 100 : 0;
                return (
                  <div key={bin} className="space-y-1 text-xs">
                    <div className="flex justify-between text-slate-700 font-medium">
                      <span>{bin}</span>
                      <span>{count} participants ({pct.toFixed(0)}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div className="bg-neuro-600 h-2 rounded-full" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Modality Coverage & Missing Rate */}
          <Card className="border-slate-200">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-neuro-600" />
                Multimodal Feature Coverage & Missingness
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {Object.entries(overview.modality_distribution).map(([mod, cov]) => {
                const missing = overview.missing_value_percentages[mod] || 0;
                return (
                  <div key={mod} className="space-y-1 text-xs">
                    <div className="flex justify-between text-slate-700 font-medium capitalize">
                      <span>{mod.replace('_', ' ')}</span>
                      <span>
                        <strong className="text-emerald-700">{cov}% complete</strong>
                        <span className="text-slate-400 text-[11px] ml-2 font-mono">({missing}% missing)</span>
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${cov}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Anonymized CSV Export Panel */}
      <Card className="border-slate-200">
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-neuro-600" />
            Anonymized Research Dataset CSV Export
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Generates strictly de-identified tabular files. No names, telephone numbers, or direct personal identifiers are ever exported.
          </CardDescription>
        </CardHeader>

        <CardContent className="pt-4 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-xs">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="exportType"
                  value="real"
                  checked={exportType === 'real'}
                  onChange={() => setExportType('real')}
                  className="text-neuro-600 focus:ring-neuro-500"
                />
                <span className="font-semibold text-slate-800">Consented Real Cohort Only</span>
              </label>

              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="exportType"
                  value="synthetic"
                  checked={exportType === 'synthetic'}
                  onChange={() => setExportType('synthetic')}
                  className="text-neuro-600 focus:ring-neuro-500"
                />
                <span className="text-purple-700 font-medium">Synthetic Dev Set Only</span>
              </label>

              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="exportType"
                  value="all"
                  checked={exportType === 'all'}
                  onChange={() => setExportType('all')}
                  className="text-neuro-600 focus:ring-neuro-500"
                />
                <span className="text-slate-600">All Records (Tagged)</span>
              </label>
            </div>

            <Button variant="primary" size="sm" onClick={handleExportCsv} disabled={isExporting}>
              <Download className="w-3.5 h-3.5 mr-1.5" />
              {isExporting ? 'Generating CSV...' : `Download ${exportType.toUpperCase()} Dataset (.CSV)`}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ML Training Preparation & Benchmarking Panel */}
      <Card className="border-slate-200">
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-neuro-600" />
            Machine Learning Training Preparation & Leakage-Free Cross-Validation
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Participant-level stratified grouping (GroupKFold), feature imputation, CatBoost, Random Forest, and Platt calibration
          </CardDescription>
        </CardHeader>

        <CardContent className="pt-4 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="outline" size="sm" onClick={handleEvaluateEligibility} disabled={isEvaluating}>
              <PlayCircle className="w-3.5 h-3.5 mr-1" />
              {isEvaluating ? 'Evaluating...' : 'Check Real Cohort Training Eligibility'}
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleRunTraining(false)}
              disabled={isTraining}
            >
              Train on Real Cohort (Gated)
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleRunTraining(true)}
              disabled={isTraining}
              className="text-purple-700 border-purple-200 hover:bg-purple-50"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1" />
              {isTraining ? 'Executing 5-Fold Splits...' : 'Run Benchmark CV Pipeline (Dev Cohort)'}
            </Button>
          </div>

          {/* Eligibility Report Display */}
          {eligibilityReport && (
            <div className={`p-4 rounded-xl border text-xs space-y-2 ${
              eligibilityReport.is_eligible
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : 'bg-amber-50 border-amber-200 text-amber-900'
            }`}>
              <div className="flex items-center gap-2 font-bold">
                {eligibilityReport.is_eligible ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                )}
                <span>
                  Eligibility Status:{' '}
                  {eligibilityReport.is_eligible
                    ? 'Eligible for Supervised Machine Learning'
                    : 'Training Suspended — Insufficient Clinical Cohort Size'}
                </span>
              </div>

              {!eligibilityReport.is_eligible && (
                <ul className="list-disc pl-5 text-[11px] space-y-0.5">
                  {eligibilityReport.reasons.map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              )}

              <p className="text-[11px] text-slate-500 pt-1">
                Total Samples: {eligibilityReport.total_samples} • Participants: {eligibilityReport.num_participants} • Missing Rate: {(eligibilityReport.missing_rate_overall * 100).toFixed(1)}%
              </p>
            </div>
          )}

          {/* Training Results Display */}
          {trainingResult && (
            <div className="space-y-4 pt-2">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                <div>
                  <span className="font-bold text-slate-900">Training Pipeline Execution Status: </span>
                  <span className="font-mono text-neuro-700 font-semibold">{trainingResult.status}</span>
                </div>
                {trainingResult.best_model && (
                  <span className="text-[11px] bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full font-bold">
                    Top Architecture: {trainingResult.best_model} (ROC-AUC: {trainingResult.best_model_metrics?.roc_auc})
                  </span>
                )}
              </div>

              {trainingResult.model_comparison && Object.keys(trainingResult.model_comparison).length > 0 && (
                <div className="overflow-x-auto border border-slate-200 rounded-xl">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[10px]">
                      <tr>
                        <th className="px-4 py-2.5">Architecture</th>
                        <th className="px-4 py-2.5">Sensitivity (Recall)</th>
                        <th className="px-4 py-2.5">Specificity</th>
                        <th className="px-4 py-2.5">Precision</th>
                        <th className="px-4 py-2.5">F1-Score</th>
                        <th className="px-4 py-2.5">ROC-AUC</th>
                        <th className="px-4 py-2.5">PR-AUC</th>
                        <th className="px-4 py-2.5">Brier Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {Object.entries(trainingResult.model_comparison).map(([mName, mMetrics]: [string, any]) => (
                        <tr key={mName} className="hover:bg-slate-50/60">
                          <td className="px-4 py-2.5 font-bold text-slate-900">{mName.replace('_', ' ')}</td>
                          <td className="px-4 py-2.5 font-mono">{(mMetrics.sensitivity * 100).toFixed(1)}%</td>
                          <td className="px-4 py-2.5 font-mono">{(mMetrics.specificity * 100).toFixed(1)}%</td>
                          <td className="px-4 py-2.5 font-mono">{(mMetrics.precision * 100).toFixed(1)}%</td>
                          <td className="px-4 py-2.5 font-mono">{mMetrics.f1_score.toFixed(3)}</td>
                          <td className="px-4 py-2.5 font-mono font-bold text-neuro-700">{mMetrics.roc_auc.toFixed(3)}</td>
                          <td className="px-4 py-2.5 font-mono">{mMetrics.pr_auc.toFixed(3)}</td>
                          <td className="px-4 py-2.5 font-mono text-slate-500">{mMetrics.brier_score.toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
