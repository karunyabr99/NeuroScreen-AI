import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Patient,
  BehavioralInput,
  VisualGazeInput,
  AcousticProsodyInput,
  ModelStatus
} from '../types';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Alert } from '../components/ui/Alert';
import { ClinicalPresetSelector } from '../components/screening/ClinicalPresetSelector';
import { BehavioralAssessment } from '../components/screening/BehavioralAssessment';
import { VisualGazeAssessment } from '../components/screening/VisualGazeAssessment';
import { AcousticProsodyAssessment } from '../components/screening/AcousticProsodyAssessment';
import {
  Sparkles,
  UserPlus,
  Cpu,
  Activity,
  Eye,
  Mic,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

interface ScreeningWizardProps {
  initialPatientId?: string;
  onSuccess: (sessionId: string) => void;
  onCancel: () => void;
}

export const ScreeningWizard: React.FC<ScreeningWizardProps> = ({
  initialPatientId,
  onSuccess,
  onCancel
}) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [models, setModels] = useState<ModelStatus[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>(initialPatientId || '');
  const [preferredModel, setPreferredModel] = useState<string>('random_forest');
  const [activeModalityTab, setActiveModalityTab] = useState<'behavioral' | 'visual_gaze' | 'acoustic_prosody'>('behavioral');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Quick Patient Intake State
  const [showNewPatientModal, setShowNewPatientModal] = useState<boolean>(false);
  const [newAgeMonths, setNewAgeMonths] = useState<number>(36);
  const [newSex, setNewSex] = useState<string>('male');
  const [newReferral, setNewReferral] = useState<string>('Developmental Pediatrics');
  const [newNotes, setNewNotes] = useState<string>('');

  // Modality States
  const [behavioral, setBehavioral] = useState<BehavioralInput>({
    social_smile_reciprocity: 1,
    name_call_orientation: 1,
    pointing_proto_declarative: 0,
    pretend_play_engagement: 1,
    repetitive_motor_mannerisms: 0,
    monotropic_focus_intensity: 1,
    gaze_alternation_dyadic: 1,
    sensory_hypersensitivity: 1,
    peer_social_interest: 0,
    gestural_communication: 1,
    response_latency_mean_sec: 2.8
  });

  const [visualGaze, setVisualGaze] = useState<VisualGazeInput>({
    fixation_count: 42,
    mean_fixation_duration_ms: 280.0,
    social_roi_dwell_percentage: 52.0,
    joint_attention_latency_ms: 680.0,
    saccade_mean_amplitude_deg: 7.4,
    atypical_scanpath_entropy: 0.46
  });

  const [acousticProsody, setAcousticProsody] = useState<AcousticProsodyInput>({
    fundamental_freq_f0_mean_hz: 245.0,
    f0_pitch_variability_stdev_hz: 28.5,
    vocal_jitter_percent: 1.25,
    vocal_shimmer_db: 0.42,
    pause_to_speech_ratio: 0.38,
    formant_dispersion_hz: 1110.0,
    speech_rate_syllables_sec: 3.1
  });

  useEffect(() => {
    async function loadData() {
      try {
        const [patList, modelList] = await Promise.all([
          api.listPatients(),
          api.listModels()
        ]);
        setPatients(patList);
        setModels(modelList);
        if (initialPatientId && patList.some(p => p.id === initialPatientId)) {
          setSelectedPatientId(initialPatientId);
        } else if (patList.length > 0 && !initialPatientId) {
          setSelectedPatientId(patList[0].id);
        }
      } catch (err: any) {
        console.error("Error loading wizard metadata:", err);
      }
    }
    loadData();
  }, [initialPatientId]);

  useEffect(() => {
    if (initialPatientId) {
      setSelectedPatientId(initialPatientId);
    }
  }, [initialPatientId]);

  const handleCreatePatient = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const created = await api.createPatient({
        age_months: newAgeMonths,
        biological_sex: newSex,
        referral_source: newReferral,
        clinical_notes: newNotes
      });
      setPatients([created, ...patients]);
      setSelectedPatientId(created.id);
      setShowNewPatientModal(false);
      setNewNotes('');
    } catch (err: any) {
      setError(err.message || "Failed to register patient");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyPreset = (
    beh: BehavioralInput,
    vis: VisualGazeInput,
    aud: AcousticProsodyInput,
    _presetName: string
  ) => {
    setBehavioral(beh);
    setVisualGaze(vis);
    setAcousticProsody(aud);
  };

  const handleSubmitScreening = async () => {
    if (!selectedPatientId) {
      setError("Please select or register a patient intake first.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await api.submitScreening({
        patient_id: selectedPatientId,
        preferred_model: preferredModel,
        behavioral,
        visual_gaze: visualGaze,
        acoustic_prosody: acousticProsody
      });

      onSuccess(result.session.id);
    } catch (err: any) {
      console.error("Screening submission failed:", err);
      setError(err.message || "Screening assessment failed to evaluate.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-neuro-600" />
            New Multimodal ASD Screening Assessment
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Multimodal evaluation fusing psychometric indicators, ocular gaze tracking, and acoustic vocal biomarkers
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmitScreening}
            isLoading={isLoading}
            className="shadow-md"
          >
            Compute Multimodal Triage <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="danger" title="Evaluation Error">
          {error}
        </Alert>
      )}

      {/* Preset Selector */}
      <ClinicalPresetSelector onApplyPreset={handleApplyPreset} />

      {/* Step 1: Patient Selection & Model Architecture */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Patient Selection Card */}
        <Card className="border-slate-200 md:col-span-2">
          <CardHeader className="py-3 px-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                <span>1. De-Identified Patient Intake:</span>
              </CardTitle>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowNewPatientModal(!showNewPatientModal)}
                className="text-xs py-1 px-2.5"
              >
                <UserPlus className="w-3.5 h-3.5 mr-1 text-neuro-600" />
                {showNewPatientModal ? 'Select Existing' : '+ Register New'}
              </Button>
            </div>
          </CardHeader>

          <CardContent className="p-4 pt-1">
            {showNewPatientModal ? (
              <form onSubmit={handleCreatePatient} className="space-y-3 pt-2">
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-700">Age (Months)</label>
                    <input
                      type="number"
                      min="12"
                      max="240"
                      value={newAgeMonths}
                      onChange={(e) => setNewAgeMonths(parseInt(e.target.value))}
                      className="w-full mt-1 px-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-700">Biological Sex</label>
                    <select
                      value={newSex}
                      onChange={(e) => setNewSex(e.target.value)}
                      className="w-full mt-1 px-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-700">Referral Source</label>
                    <input
                      type="text"
                      value={newReferral}
                      onChange={(e) => setNewReferral(e.target.value)}
                      className="w-full mt-1 px-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-700">Clinical Observations (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Speech delay, reduced pointing noticed by preschool teacher"
                    value={newNotes}
                    onChange={(e) => setNewNotes(e.target.value)}
                    className="w-full mt-1 px-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <Button type="button" variant="ghost" size="sm" onClick={() => setShowNewPatientModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" size="sm" isLoading={isLoading}>
                    Save Patient
                  </Button>
                </div>
              </form>
            ) : patients.length === 0 ? (
              <div className="text-xs text-slate-500 py-3 text-center">
                No patients registered yet. Click "+ Register New" to create an anonymized profile.
              </div>
            ) : (
              <div className="space-y-2 pt-1">
                <select
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-800 focus:ring-2 focus:ring-neuro-500"
                >
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.anonymized_id} — {p.age_months} months ({Math.floor(p.age_months / 12)}y {p.age_months % 12}m), {p.biological_sex} — {p.referral_source}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Model Architecture Selector */}
        <Card className="border-slate-200">
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-neuro-600" />
              <span>2. Decision Engine ({models.length || 4} available):</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-1">
            <select
              value={preferredModel}
              onChange={(e) => setPreferredModel(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-800 focus:ring-2 focus:ring-neuro-500"
            >
              <option value="random_forest">Random Forest (Scikit-Learn)</option>
              <option value="xgboost">XGBoost Classifier</option>
              <option value="catboost">CatBoost Classifier</option>
              <option value="pytorch_fusion">PyTorch Multimodal Cross-Modal Net</option>
            </select>
            <div className="mt-2 text-[10px] text-slate-400 leading-tight">
              Modular ML interface active. Checkpoints cleanly detected; uncalibrated baseline mode active when weights unmounted.
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Step 2: Modality Tabs */}
      <div className="space-y-4">
        {/* Modality Nav */}
        <div className="flex border-b border-slate-200 gap-2">
          <button
            onClick={() => setActiveModalityTab('behavioral')}
            className={`pb-2.5 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeModalityTab === 'behavioral'
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Activity className="w-4 h-4 text-blue-600" />
            <span>Behavioral & Psychometrics (11)</span>
          </button>

          <button
            onClick={() => setActiveModalityTab('visual_gaze')}
            className={`pb-2.5 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeModalityTab === 'visual_gaze'
                ? 'border-teal-600 text-teal-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Eye className="w-4 h-4 text-teal-600" />
            <span>Visual Ocular & Scanpath (6)</span>
          </button>

          <button
            onClick={() => setActiveModalityTab('acoustic_prosody')}
            className={`pb-2.5 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeModalityTab === 'acoustic_prosody'
                ? 'border-purple-600 text-purple-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Mic className="w-4 h-4 text-purple-600" />
            <span>Acoustic Vocal Prosody (7)</span>
          </button>
        </div>

        {/* Tab Panels */}
        {activeModalityTab === 'behavioral' && (
          <BehavioralAssessment value={behavioral} onChange={setBehavioral} />
        )}

        {activeModalityTab === 'visual_gaze' && (
          <VisualGazeAssessment value={visualGaze} onChange={setVisualGaze} />
        )}

        {activeModalityTab === 'acoustic_prosody' && (
          <AcousticProsodyAssessment value={acousticProsody} onChange={setAcousticProsody} />
        )}
      </div>

      {/* Footer Submit CTA */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>24 aligned multimodal features ready. Full SHAP waterfall and LIME explanations generated on submission.</span>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="md" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleSubmitScreening}
            isLoading={isLoading}
            className="shadow-md"
          >
            Run Multimodal Triage Assessment <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        </div>
      </div>
    </div>
  );
};
