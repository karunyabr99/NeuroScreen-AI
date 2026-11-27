import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Patient } from '../types';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { formatDateTime } from '../lib/utils';
import { Users, UserPlus, Sparkles, Search, Info } from 'lucide-react';

interface PatientsViewProps {
  onStartScreeningWithPatient: (patientId: string) => void;
}

export const PatientsView: React.FC<PatientsViewProps> = ({ onStartScreeningWithPatient }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showModal, setShowModal] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // New Patient form state
  const [ageMonths, setAgeMonths] = useState<number>(36);
  const [sex, setSex] = useState<string>('male');
  const [referral, setReferral] = useState<string>('Pediatric Clinic');
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    async function loadPatients() {
      setIsLoading(true);
      try {
        const list = await api.listPatients();
        setPatients(list);
      } catch (err) {
        console.error("Failed to load patients:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadPatients();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const created = await api.createPatient({
        age_months: ageMonths,
        biological_sex: sex,
        referral_source: referral,
        clinical_notes: notes
      });
      setPatients([created, ...patients]);
      setShowModal(false);
      setNotes('');
    } catch (err: any) {
      alert("Error creating patient: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filtered = patients.filter(p =>
    p.anonymized_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.referral_source.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.clinical_notes && p.clinical_notes.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-neuro-600" />
            De-Identified Participant Intake Directory
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Governed by the De-identified Research Identifier Scheme preserving participant confidentiality
          </p>
        </div>

        <Button variant="primary" size="sm" onClick={() => setShowModal(true)}>
          <UserPlus className="w-4 h-4 mr-1.5" /> Register New Intake
        </Button>
      </div>

      {/* Compliance & Governance Safeguard Notice */}
      <div className="bg-sky-50/70 border border-sky-200/80 rounded-xl p-3.5 flex items-start gap-3">
        <Info className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-sky-900 leading-relaxed">
          <span className="font-semibold">Research Data Governance Notice: </span>
          NeuroScreen AI operates strictly under a <strong>De-identified Research Identifier Scheme</strong>.
          Formal Institutional Review Board (IRB) / Ethics Committee approval, signed participant/guardian informed consent,
          and jurisdictional data privacy impact assessments are required prior to enrolling real clinical participants or collecting live multimodal data.
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Filter by anonymized ID (e.g. NS-2026-...) or referral clinic..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-200 bg-white shadow-xs focus:ring-2 focus:ring-neuro-500"
        />
      </div>

      {/* Patients Table Card */}
      <Card className="border-slate-200">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-10 text-center text-sm text-slate-500">Loading patient records...</div>
          ) : filtered.length === 0 ? (
            <div className="p-10 text-center space-y-3">
              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
                <Users className="w-5 h-5" />
              </div>
              <p className="text-sm font-medium text-slate-700">No patient records match the filter.</p>
              <Button variant="outline" size="sm" onClick={() => setShowModal(true)}>
                + Register First Patient
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-6 py-3 font-semibold">Anonymized Ref</th>
                    <th className="px-6 py-3 font-semibold">Age at Screening</th>
                    <th className="px-6 py-3 font-semibold">Biological Sex</th>
                    <th className="px-6 py-3 font-semibold">Referral Clinic</th>
                    <th className="px-6 py-3 font-semibold">Intake Notes</th>
                    <th className="px-6 py-3 font-semibold">Registered</th>
                    <th className="px-6 py-3 text-right font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filtered.map((patient) => {
                    const years = Math.floor(patient.age_months / 12);
                    const months = patient.age_months % 12;

                    return (
                      <tr key={patient.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-6 py-3.5 font-mono font-bold text-slate-900">
                          {patient.anonymized_id}
                        </td>
                        <td className="px-6 py-3.5 font-mono">
                          {patient.age_months}m ({years}y {months}m)
                        </td>
                        <td className="px-6 py-3.5 capitalize">
                          {patient.biological_sex}
                        </td>
                        <td className="px-6 py-3.5">
                          {patient.referral_source}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500 max-w-xs truncate">
                          {patient.clinical_notes || <span className="text-slate-300 italic">None</span>}
                        </td>
                        <td className="px-6 py-3.5 text-slate-400 font-mono text-[11px]">
                          {formatDateTime(patient.created_at)}
                        </td>
                        <td className="px-6 py-3.5 text-right">
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => onStartScreeningWithPatient(patient.id)}
                            className="text-xs py-1 px-2.5"
                          >
                            <Sparkles className="w-3.5 h-3.5 mr-1" /> Assess
                          </Button>
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

      {/* Modal Dialog */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-1">
              <UserPlus className="w-4 h-4 text-neuro-600" />
              Register New Patient Intake
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              An anonymized identifier (<code className="font-mono">NS-2026-XXXX</code>) will be generated automatically.
            </p>

            <form onSubmit={handleCreate} className="space-y-3.5">
              <div>
                <label className="text-xs font-semibold text-slate-700">Patient Age in Completed Months</label>
                <input
                  type="number"
                  min="12"
                  max="240"
                  value={ageMonths}
                  onChange={(e) => setAgeMonths(parseInt(e.target.value))}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700">Biological Sex</label>
                <select
                  value={sex}
                  onChange={(e) => setSex(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-slate-300 bg-white focus:ring-2 focus:ring-neuro-500"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other / Non-Binary</option>
                  <option value="unspecified">Unspecified</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700">Referral Source / Origin Clinic</label>
                <input
                  type="text"
                  value={referral}
                  onChange={(e) => setReferral(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700">Initial Clinical Notes (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Primary parental or teacher concerns..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
                  Register Intake
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
