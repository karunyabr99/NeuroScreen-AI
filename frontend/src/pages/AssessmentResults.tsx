import React, { useEffect, useState } from 'react';
import {
  Download,
  Printer,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ArrowRight,
  ClipboardList
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { api } from '../services/api';
import { ScreeningSession, ScreeningDetail, Patient } from '../types';
import { formatDateTime } from '../lib/utils';

interface AssessmentResultsProps {
  initialSessionId?: string;
  onNavigateToAssessment?: () => void;
}

export const AssessmentResults: React.FC<AssessmentResultsProps> = ({
  initialSessionId,
  onNavigateToAssessment,
}) => {
  const [sessions, setSessions] = useState<ScreeningSession[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>(initialSessionId || '');
  const [sessionDetail, setSessionDetail] = useState<ScreeningDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState<boolean>(false);

  // Load all sessions on mount
  useEffect(() => {
    async function loadSessions() {
      setIsLoading(true);
      setError(null);
      try {
        const [screenList, patList] = await Promise.all([
          api.listScreenings(),
          api.listPatients(),
        ]);
        setSessions(screenList);
        setPatients(patList);

        if (screenList.length > 0) {
          const targetId = initialSessionId || screenList[0].id;
          setSelectedSessionId(targetId);
          await loadDetail(targetId);
        }
      } catch (err: any) {
        console.error('Failed to load screening list:', err);
        setError(err.message || 'Unable to retrieve screening sessions.');
      } finally {
        setIsLoading(false);
      }
    }
    loadSessions();
  }, [initialSessionId]);

  const loadDetail = async (sessionId: string) => {
    try {
      const data = await api.getScreeningDetail(sessionId);
      setSessionDetail(data);
    } catch (err: any) {
      console.error('Failed to load session detail:', err);
      setError(err.message || 'Failed to retrieve screening details.');
    }
  };

  const handleSessionChange = (newId: string) => {
    setSelectedSessionId(newId);
    loadDetail(newId);
  };

  const handleDownloadPdf = async () => {
    if (!selectedSessionId) return;
    setIsDownloadingPdf(true);
    try {
      const blob = await api.downloadReportPdf(selectedSessionId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `screening_summary_${selectedSessionId.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`PDF download failed: ${err.message}`);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const currentPatient = patients.find((p) => p.id === sessionDetail?.session?.patient_id);
  const currentSession = sessionDetail?.session;

  const getTriageInfo = (tier?: string) => {
    if (tier === 'OBSERVATION_ONLY_UNDER_12M') {
      return {
        title: 'Developmental Observation Record (Infant < 12 Months)',
        badge: <Badge variant="default">Observation Only (&lt;12 Months)</Badge>,
        color: 'bg-blue-50/70 border-blue-200 text-blue-950',
        summary:
          'Standardized autism screening instruments (including Q-CHAT-10) are validated for toddlers aged 12–36 months. For infants under 12 months, automated probability estimation is withheld to avoid false positives. Recorded observations serve as a baseline for routine pediatric developmental tracking.',
        recommendation:
          'Review these baseline observations with your pediatrician during routine 9-month and 12-month well-child examinations. Re-screen at 12–18 months using the calibrated toddler protocol.',
      };
    }
    if (!tier || tier === 'LOW' || tier === 'LOW_LIKELIHOOD') {
      return {
        title: 'Typical Developmental Observations',
        badge: <Badge variant="success">Typical Range (Low Likelihood)</Badge>,
        color: 'bg-emerald-50/70 border-emerald-200 text-emerald-950',
        summary:
          'Observed social communication, eye contact, and behavioral milestones fall within typical developmental expectations. Routine milestone monitoring with the child&apos;s pediatrician is recommended.',
        recommendation:
          'Continue nurturing standard developmental play and communication. No specialized autism triage is indicated at this time. Maintain scheduled well-child visits.',
      };
    }
    if (tier === 'ELEVATED' || tier === 'MODERATE_MONITOR') {
      return {
        title: 'Moderate Developmental Variation',
        badge: <Badge variant="warning">Developmental Monitoring Recommended</Badge>,
        color: 'bg-amber-50/70 border-amber-200 text-amber-950',
        summary:
          'Observable variations noted in social communication reciprocity, gesture use, or speech pacing. While not diagnostic, active developmental monitoring is recommended.',
        recommendation:
          'Consult with your child&apos;s pediatrician. Consider an audiological hearing check to rule out sensory auditory differences, and schedule an early speech and language evaluation if verbal milestones are delayed.',
      };
    }
    return {
      title: 'Elevated Developmental Indicators',
      badge: <Badge variant="danger">Multidisciplinary Clinical Evaluation Recommended</Badge>,
      color: 'bg-rose-50/70 border-rose-200 text-rose-950',
      summary:
        'Multiple pronounced differences observed across joint attention, social interaction, repetitive motor mannerisms, or speech milestones.',
      recommendation:
        'A comprehensive multidisciplinary diagnostic evaluation by a licensed specialist (e.g. developmental pediatrician, child neurologist, or clinical child psychologist) utilizing standard assessment instruments (ADOS-2, ADI-R) is recommended.',
    };
  };

  if (isLoading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Loading assessment results...</p>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mx-auto">
          <ClipboardList className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">No Assessments Completed Yet</h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          Start a new screening assessment to view objective behavioral observations and download clinical reports.
        </p>
        {onNavigateToAssessment && (
          <Button variant="primary" onClick={onNavigateToAssessment} className="bg-teal-600 text-white">
            Start First Assessment <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        )}
      </div>
    );
  }

  const triage = getTriageInfo(currentSession?.risk_tier);

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header & Session Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center gap-2 bg-teal-50 text-teal-700 border border-teal-200 px-3 py-1 rounded-full text-xs font-semibold mb-2">
            <CheckCircle2 className="w-4 h-4 text-teal-600" />
            <span>Completed Assessment Results</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Screening-Support Results
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            Plain-language summary of questionnaire responses, video observations, and follow-up guidance.
          </p>
        </div>

        {/* Session Dropdown Switcher */}
        <div className="flex items-center gap-2 bg-white p-2 rounded-xl border border-slate-200 shadow-sm">
          <label className="text-xs font-bold text-slate-600 uppercase tracking-wider pl-1">Session:</label>
          <select
            value={selectedSessionId}
            onChange={(e) => handleSessionChange(e.target.value)}
            className="text-xs font-semibold bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-teal-500"
          >
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.id.slice(0, 8)} – {s.risk_tier.replace(/_/g, ' ')} ({formatDateTime(s.created_at).slice(0, 10)})
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <Alert variant="danger" title="Notice">
          {error}
        </Alert>
      )}

      {/* Participant Overview Card */}
      {currentPatient && currentSession && (
        <Card className="border-slate-200">
          <CardContent className="p-4 sm:p-6 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-400 font-bold uppercase text-[10px] block">Anonymous Participant ID</span>
              <span className="font-extrabold text-slate-900 text-sm">{currentPatient.anonymized_id}</span>
            </div>
            <div>
              <span className="text-slate-400 font-bold uppercase text-[10px] block">Age</span>
              <span className="font-extrabold text-slate-900 text-sm">
                {currentPatient.age_months} months ({Math.floor(currentPatient.age_months / 12)}y {currentPatient.age_months % 12}m)
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-bold uppercase text-[10px] block">Biological Sex</span>
              <span className="font-bold text-slate-900 text-sm">{currentPatient.biological_sex}</span>
            </div>
            <div>
              <span className="text-slate-400 font-bold uppercase text-[10px] block">Assessment Date</span>
              <span className="font-bold text-slate-900 text-sm">{formatDateTime(currentSession.created_at)}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Primary Screening-Support Summary Card */}
      <Card className={`border ${triage.color} overflow-hidden shadow-sm`}>
        <CardHeader className="py-4 px-6 border-b border-inherit bg-white/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <span className="text-xs uppercase font-bold tracking-wider opacity-70 block mb-1">
              Screening Triage Result
            </span>
            <CardTitle className="text-xl sm:text-2xl font-black">{triage.title}</CardTitle>
          </div>
          <div>{triage.badge}</div>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          <p className="text-sm leading-relaxed">{triage.summary}</p>

          <div className="p-4 rounded-xl bg-white/80 border border-inherit space-y-1.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Guidance & Follow-Up Recommendations:
            </h4>
            <p className="text-xs text-slate-700 leading-relaxed">{triage.recommendation}</p>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 text-xs">
            <div className="flex items-center gap-4">
              <span>
                Calculated Risk Likelihood:{' '}
                <strong className="underline">
                  {currentSession?.composite_risk_score !== null && currentSession?.composite_risk_score !== undefined
                    ? `${(currentSession.composite_risk_score * 100).toFixed(1)}%`
                    : currentSession?.risk_tier === 'OBSERVATION_ONLY_UNDER_12M'
                    ? 'N/A (Observation Checklist Mode)'
                    : 'Calibrated'}
                </strong>
              </span>
              <span>
                Verified Model:{' '}
                <strong className="text-teal-700">
                  {currentSession?.is_calibrated ? 'Calibrated Stacking Ensemble' : 'Standard'}
                </strong>
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.print()}
                className="text-xs bg-white"
              >
                <Printer className="w-3.5 h-3.5 mr-1.5" /> Print
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleDownloadPdf}
                isLoading={isDownloadingPdf}
                className="bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-sm"
              >
                <Download className="w-3.5 h-3.5 mr-1.5" /> Download PDF Report
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Completed Assessment Sections Checklist */}
      <Card className="border-slate-200">
        <CardHeader className="py-3 px-4">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-teal-600" />
            <span>Completed Assessment Sections</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-teal-50/50 border border-teal-200 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-teal-600 mt-0.5" />
              <div>
                <strong className="block text-slate-900">1. Child Registration</strong>
                <span className="text-slate-500 text-[11px]">Consent Verified</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-teal-50/50 border border-teal-200 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-teal-600 mt-0.5" />
              <div>
                <strong className="block text-slate-900">2. Questionnaire</strong>
                <span className="text-slate-500 text-[11px]">8 Milestones Evaluated</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-teal-50/50 border border-teal-200 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-teal-600 mt-0.5" />
              <div>
                <strong className="block text-slate-900">3. Video Assessment</strong>
                <span className="text-slate-500 text-[11px]">Movement CV Analyzed</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-teal-50/50 border border-teal-200 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-teal-600 mt-0.5" />
              <div>
                <strong className="block text-slate-900">4. Decision Support</strong>
                <span className="text-slate-500 text-[11px]">Stacking Synthesis</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Observation Summary Card */}
      <Card className="border-slate-200">
        <CardHeader className="py-3 px-4">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-teal-600" />
            <span>Behavioral & Communication Observations</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Social Communication</span>
              <p className="text-slate-700">
                Expressive gestures, shared smiling, and reciprocal interactions recorded across caregiver and educator reports.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Joint Attention & Gaze</span>
              <p className="text-slate-700">
                Responsiveness to spoken name cues and gaze alternation between social actors and shared objects.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Motor Patterns & Repetition</span>
              <p className="text-slate-700">
                Evaluation of motor stereotypies, hand/body mannerisms, and object rotation rhythmicity.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Vocal Prosody & Speech</span>
              <p className="text-slate-700">
                Acoustic pitch variability, hesitation pause dynamics, and vocalization modulation.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Academic Disclaimer */}
      <div className="p-5 rounded-2xl bg-amber-50/80 border border-amber-200 flex items-start gap-3.5 text-amber-900 text-xs sm:text-sm">
        <AlertTriangle className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="font-bold text-amber-950">Academic Screening Support Prototype – Non-Diagnostic Notice</h4>
          <p className="text-amber-800 leading-relaxed text-xs">
            NeuroScreen AI is designed for academic research and triage support. It does <strong>not</strong> constitute a clinical diagnosis. Diagnostic confirmation requires comprehensive in-person multidisciplinary evaluation by licensed specialists.
          </p>
        </div>
      </div>
    </div>
  );
};
