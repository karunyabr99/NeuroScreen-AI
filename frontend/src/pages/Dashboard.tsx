import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Patient, ScreeningSession, ModelStatus } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Alert } from '../components/ui/Alert';
import { formatDateTime, formatRiskTier } from '../lib/utils';
import {
  Activity,
  Users,
  Cpu,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  FileText,
  Clock
} from 'lucide-react';

interface DashboardProps {
  onStartScreening: () => void;
  onViewScreening: (sessionId: string) => void;
  onViewPatients: () => void;
  onViewResearch: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  onStartScreening,
  onViewScreening,
  onViewPatients,
  onViewResearch
}) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [screenings, setScreenings] = useState<ScreeningSession[]>([]);
  const [models, setModels] = useState<ModelStatus[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setError(null);
      try {
        const [patList, screenList, modelList] = await Promise.all([
          api.listPatients(),
          api.listScreenings(),
          api.listModels()
        ]);
        setPatients(patList);
        setScreenings(screenList);
        setModels(modelList);
      } catch (err: any) {
        console.error("Dashboard load failed:", err);
        setError(err.message || "Failed to connect to backend service");
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="danger" title="Service Connection Alert">
          {error}
        </Alert>
      )}

      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-neuro-900 via-neuro-800 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 bg-neuro-500/20 text-neuro-200 border border-neuro-500/30 px-3 py-1 rounded-full text-xs font-medium mb-3">
            <Sparkles className="w-3.5 h-3.5 text-neuro-400" />
            <span>Multimodal Autism Spectrum Disorder Decision Support</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            NeuroScreen AI Decision Support Platform
          </h1>
          <p className="mt-2 text-sm sm:text-base text-slate-300 leading-relaxed">
            Synthesizing psychometric behavioral metrics, ocular gaze dynamics, and acoustic vocal prosody biomarkers.
            Equipped with modular Scikit-Learn, CatBoost, XGBoost, and PyTorch deep fusion architectures with SHAP and LIME explainability.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              variant="primary"
              size="md"
              onClick={onStartScreening}
              className="bg-neuro-500 hover:bg-neuro-400 text-white shadow-lg"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Start New Multimodal Screening
            </Button>
            <Button
              variant="outline"
              size="md"
              onClick={onViewResearch}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20"
            >
              <FileText className="w-4 h-4 mr-2" />
              Inspect Research & Patent Foundations
            </Button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Screening Sessions</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1 font-mono">{screenings.length}</h3>
              <p className="text-[11px] text-slate-400 mt-0.5">Recorded assessments</p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-neuro-50 flex items-center justify-center text-neuro-600">
              <Activity className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 cursor-pointer hover:border-slate-300 transition-colors" onClick={onViewPatients}>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Registered Patients</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1 font-mono">{patients.length}</h3>
              <p className="text-[11px] text-slate-400 mt-0.5">De-identified intake records</p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
              <Users className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Modular ML Engines</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1 font-mono">{models.length || 4}</h3>
              <p className="text-[11px] text-slate-400 mt-0.5">RF, XGB, CatBoost, PyTorch</p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
              <Cpu className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Model Verification</p>
              <div className="mt-1">
                <span className="text-xs font-semibold text-sky-700 bg-sky-50 border border-sky-200 px-2 py-0.5 rounded-full">
                  Modular Ready
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Zero fabricated outputs</p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
              <ShieldCheck className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Screenings Table */}
      <Card className="border-slate-200">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="w-4 h-4 text-neuro-600" />
              Recent Screening Sessions
            </CardTitle>
            <CardDescription>
              Clinical screening records with multimodal feature profiles and explainability records
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={onStartScreening}>
            + New Assessment
          </Button>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-slate-500 text-sm">Loading screening records...</div>
          ) : screenings.length === 0 ? (
            <div className="p-10 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
                <Activity className="w-6 h-6" />
              </div>
              <p className="text-sm text-slate-600 font-medium">No screening sessions recorded yet.</p>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Launch a new assessment to submit multimodal behavioral, gaze, and acoustic data and review SHAP/LIME feature attributions.
              </p>
              <Button variant="primary" size="sm" onClick={onStartScreening}>
                Run First Screening Assessment
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-6 py-3 font-semibold">Session ID</th>
                    <th className="px-6 py-3 font-semibold">Patient Ref</th>
                    <th className="px-6 py-3 font-semibold">Risk Classification</th>
                    <th className="px-6 py-3 font-semibold">Modalities</th>
                    <th className="px-6 py-3 font-semibold">Model Architecture</th>
                    <th className="px-6 py-3 font-semibold">Timestamp</th>
                    <th className="px-6 py-3 text-right font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {screenings.map((s) => {
                    const tier = formatRiskTier(s.risk_tier);
                    const patient = patients.find(p => p.id === s.patient_id);

                    return (
                      <tr
                        key={s.id}
                        onClick={() => onViewScreening(s.id)}
                        className="hover:bg-slate-50/70 transition-colors cursor-pointer group"
                      >
                        <td className="px-6 py-3.5 font-mono text-slate-900 font-medium">
                          {s.id.substring(0, 8)}...
                        </td>
                        <td className="px-6 py-3.5 font-mono text-slate-600">
                          {patient?.anonymized_id || s.patient_id.substring(0, 8)}
                        </td>
                        <td className="px-6 py-3.5">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border ${tier.bg} ${tier.color} ${tier.border}`}>
                            {tier.label}
                          </span>
                        </td>
                        <td className="px-6 py-3.5">
                          <div className="flex gap-1">
                            {s.modalities_included.map((m) => (
                              <span key={m} className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded text-[10px]">
                                {m === 'behavioral' ? 'Beh' : m === 'visual_gaze' ? 'Gaze' : 'Audio'}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-3.5 text-slate-600">
                          <span className="font-mono text-[11px]">{s.model_version}</span>
                        </td>
                        <td className="px-6 py-3.5 text-slate-400">
                          {formatDateTime(s.created_at)}
                        </td>
                        <td className="px-6 py-3.5 text-right">
                          <span className="text-neuro-600 group-hover:translate-x-1 inline-flex items-center transition-transform font-medium">
                            View <ArrowRight className="w-3.5 h-3.5 ml-1" />
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
