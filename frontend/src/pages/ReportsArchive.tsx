import React, { useEffect, useState } from 'react';
import {
  FileText,
  Download,
  Search,
  Filter,
  ShieldCheck,
  Calendar,
  Sparkles
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { api } from '../services/api';
import { ScreeningSession, Patient } from '../types';
import { formatDateTime, downloadBlobAsFile } from '../lib/utils';

interface ReportsArchiveProps {
  onSelectSession: (sessionId: string) => void;
  onNavigateToAssessment: () => void;
}

export const ReportsArchive: React.FC<ReportsArchiveProps> = ({
  onSelectSession,
  onNavigateToAssessment,
}) => {
  const [sessions, setSessions] = useState<ScreeningSession[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filterTier, setFilterTier] = useState<string>('ALL');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    async function loadReports() {
      setIsLoading(true);
      try {
        const [screenList, patList] = await Promise.all([
          api.listScreenings(),
          api.listPatients(),
        ]);
        setSessions(screenList);
        setPatients(patList);
      } catch (err) {
        console.error('Failed to load reports archive:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadReports();
  }, []);

  const getPatient = (patientId: string): Patient | undefined => {
    return patients.find((p) => p.id === patientId);
  };

  const handleDownload = async (sessionId: string, anonId: string) => {
    setDownloadingId(sessionId);
    try {
      const blob = await api.downloadReportPdf(sessionId);
      const filename = `screening_report_${anonId}_${sessionId.slice(0, 8)}.pdf`;
      downloadBlobAsFile(blob, filename);
    } catch (err: any) {
      alert(`PDF download failed: ${err.message}`);
    } finally {
      setDownloadingId(null);
    }
  };

  const filteredSessions = sessions.filter((session) => {
    const patient = getPatient(session.patient_id);
    const anonId = patient ? patient.anonymized_id.toLowerCase() : '';
    const matchesSearch =
      anonId.includes(searchTerm.toLowerCase()) ||
      session.id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      filterTier === 'ALL' || session.risk_tier === filterTier;

    return matchesSearch && matchesFilter;
  });

  const getBadge = (tier: string) => {
    if (tier === 'LOW_LIKELIHOOD') {
      return <Badge variant="success">Typical Range</Badge>;
    }
    if (tier === 'MODERATE_MONITOR') {
      return <Badge variant="warning">Monitoring</Badge>;
    }
    if (tier === 'ELEVATED_TRIAGE_RECOMMENDED') {
      return <Badge variant="danger">Clinical Evaluation</Badge>;
    }
    return <Badge variant="default">{tier.replace(/_/g, ' ')}</Badge>;
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 border border-indigo-200 px-3 py-1 rounded-full text-xs font-semibold mb-2">
            <FileText className="w-4 h-4 text-indigo-600" />
            <span>Official Clinical Documentation</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Assessment Reports
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            Browse completed screening assessments, view summaries, and download publication-grade PDF reports.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={onNavigateToAssessment}
          className="bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-sm"
        >
          <Sparkles className="w-4 h-4 mr-1.5" /> Start New Assessment
        </Button>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-sm">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by participant ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full text-xs bg-slate-50 border border-slate-300 rounded-xl pl-9 pr-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-500 font-medium">Outcome:</span>
          <select
            value={filterTier}
            onChange={(e) => setFilterTier(e.target.value)}
            className="text-xs font-semibold bg-slate-50 border border-slate-300 rounded-xl px-2.5 py-1.5 focus:ring-2 focus:ring-teal-500"
          >
            <option value="ALL">All Outcomes ({sessions.length})</option>
            <option value="LOW_LIKELIHOOD">Typical Range</option>
            <option value="MODERATE_MONITOR">Monitoring Recommended</option>
            <option value="ELEVATED_TRIAGE_RECOMMENDED">Evaluation Recommended</option>
          </select>
        </div>
      </div>

      {/* Reports List / Table */}
      {isLoading ? (
        <div className="py-20 text-center space-y-2">
          <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500">Loading reports archive...</p>
        </div>
      ) : filteredSessions.length === 0 ? (
        <Card className="border-slate-200 text-center p-12 space-y-3">
          <FileText className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-base font-bold text-slate-800">No Assessment Reports Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {searchTerm || filterTier !== 'ALL'
              ? 'No reports match your search criteria. Try resetting the filter.'
              : 'Complete your first screening assessment to generate a report.'}
          </p>
          <div className="pt-2">
            <Button variant="primary" onClick={onNavigateToAssessment} className="bg-teal-600 text-white text-xs">
              Start Assessment Now
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredSessions.map((session) => {
            const patient = getPatient(session.patient_id);
            const anonId = patient ? patient.anonymized_id : 'De-identified';
            const ageText = patient
              ? `${patient.age_months}m (${Math.floor(patient.age_months / 12)}y ${patient.age_months % 12}m)`
              : 'Age N/A';

            return (
              <Card
                key={session.id}
                className="border-slate-200 hover:border-teal-300 transition-colors shadow-sm"
              >
                <CardContent className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  {/* Left Metadata */}
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-slate-900 text-sm">{anonId}</span>
                      <span className="text-xs text-slate-500 font-medium">• {ageText}</span>
                      {patient?.biological_sex && (
                        <span className="text-xs text-slate-400">({patient.biological_sex})</span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        {formatDateTime(session.created_at)}
                      </span>
                      <span>
                        Session ID: <code className="text-slate-600 font-mono text-[11px]">{session.id.slice(0, 8)}</code>
                      </span>
                    </div>

                    <div className="flex items-center gap-2 pt-1">
                      {getBadge(session.risk_tier)}
                      <span className="text-[11px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                        Calibrated Model Verified
                      </span>
                    </div>
                  </div>

                  {/* Right Actions */}
                  <div className="flex items-center gap-2.5 sm:self-center">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onSelectSession(session.id)}
                      className="text-xs"
                    >
                      View Summary
                    </Button>

                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleDownload(session.id, anonId)}
                      isLoading={downloadingId === session.id}
                      className="bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold"
                    >
                      <Download className="w-3.5 h-3.5 mr-1.5" /> Download PDF
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Information Footer */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3 text-xs text-slate-600">
        <ShieldCheck className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <strong className="text-slate-800">Research Archive & Participant Privacy:</strong>
          <p className="leading-relaxed">
            All reports are strictly de-identified in compliance with ethical research guidelines. PDF reports include protocol references, objective behavioral observations, and clinical triage disclaimers.
          </p>
        </div>
      </div>
    </div>
  );
};
