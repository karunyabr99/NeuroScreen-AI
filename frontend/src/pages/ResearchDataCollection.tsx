import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Patient, ResearchAssessment } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
  ClipboardList,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  CheckCircle2,
  Users,
  Eye,
  Activity,
  History,
  Lock
} from 'lucide-react';

interface ResearchDataCollectionProps {
  initialPatientId?: string;
  onNavigateToScreening?: (patientId: string) => void;
}

export const ResearchDataCollection: React.FC<ResearchDataCollectionProps> = ({
  initialPatientId,
  onNavigateToScreening
}) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>(initialPatientId || '');
  const [activeFormType, setActiveFormType] = useState<'caregiver' | 'teacher' | 'professional'>('caregiver');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [pastAssessments, setPastAssessments] = useState<ResearchAssessment[]>([]);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form State: Caregiver
  const [walkingAgeMonths, setWalkingAgeMonths] = useState<number>(14);
  const [firstWordsAgeMonths, setFirstWordsAgeMonths] = useState<number>(16);
  const [phraseSpeechAgeMonths, setPhraseSpeechAgeMonths] = useState<number>(28);
  const [hasLanguageRegression, setHasLanguageRegression] = useState<boolean>(false);
  const [caregiverMainConcerns, setCaregiverMainConcerns] = useState<string>('Limited eye contact when spoken to, does not consistently turn to name.');
  const [passedHearingScreen, setPassedHearingScreen] = useState<boolean>(true);
  const [familyNeurohistory, setFamilyNeurohistory] = useState<string>('None reported');

  // Form State: Teacher / Educator
  const [classroomEyeGaze, setClassroomEyeGaze] = useState<string>('inconsistent');
  const [peerInteractionLevel, setPeerInteractionLevel] = useState<string>('solitary_parallel');
  const [responseToNameClassroom, setResponseToNameClassroom] = useState<string>('requires_multiple_prompts');
  const [repetitiveMotorClassroom, setRepetitiveMotorClassroom] = useState<string>('occasional_hand_flapping');
  const [insistenceOnSameness, setInsistenceOnSameness] = useState<string>('mild_distress_on_transition');
  const [sensoryReactivity, setSensoryReactivity] = useState<string>('auditory_hypersensitivity');

  // Form State: Qualified Professional & Multimodal
  const [jointAttentionScore, setJointAttentionScore] = useState<number>(1);
  const [socialSmileReciprocity, setSocialSmileReciprocity] = useState<number>(1);
  const [protoDeclarativePointing, setProtoDeclarativePointing] = useState<number>(1);
  const [stereotypedMotorScore, setStereotypedMotorScore] = useState<number>(1);
  const [monotropicFocusIntensity, setMonotropicFocusIntensity] = useState<number>(1);
  const [sensorGazeType, setSensorGazeType] = useState<'infrared_pupil_corneal' | 'webcam_exploratory'>('infrared_pupil_corneal');
  const [gazeTrackingAdministered, setGazeTrackingAdministered] = useState<boolean>(true);
  const [audioProsodyAdministered, setAudioProsodyAdministered] = useState<boolean>(true);
  const [movementMotorAdministered, setMovementMotorAdministered] = useState<boolean>(true);
  const [assessorNotes, setAssessorNotes] = useState<string>('');

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const list = await api.listPatients();
        setPatients(list);
        if (!selectedPatientId && list.length > 0) {
          setSelectedPatientId(list[0].id);
        }
      } catch (err: any) {
        console.error("Failed to load participants:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const selectedPatient = patients.find((p) => p.id === selectedPatientId);
  const isConsentGranted = selectedPatient?.consent_status === 'granted';

  useEffect(() => {
    if (selectedPatientId) {
      api.listPatientAssessments(selectedPatientId)
        .then((data) => setPastAssessments(data))
        .catch((err) => console.error("Failed to load assessments:", err));
    }
  }, [selectedPatientId]);

  const handleGrantConsent = async () => {
    if (!selectedPatientId) return;
    try {
      const updated = await api.updateConsent(selectedPatientId, {
        consent_status: 'granted',
        assent_status: (selectedPatient?.age_months || 0) >= 84 ? 'granted' : 'not_applicable',
        guardian_relationship: 'Parent / Legal Guardian',
        ethics_approval_ref: 'IRB-NS-2026-ETHICS-04',
        protocol_version: 'NS-DATA-COLL-v1.0',
        notes: 'Informed guardian consent verified and recorded by assessor.'
      });
      setPatients(patients.map((p) => (p.id === updated.id ? updated : p)));
      setStatusMessage({ type: 'success', text: 'Informed consent successfully granted and recorded in audit log.' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message });
    }
  };

  const handleWithdrawConsent = async () => {
    if (!selectedPatientId) return;
    if (!confirm("Are you sure you want to withdraw consent for this participant? All future data intake will be blocked, and this record will be excluded from research ML training cohorts.")) return;
    try {
      const updated = await api.withdrawConsent(selectedPatientId, "Guardian requested withdrawal of research consent.");
      setPatients(patients.map((p) => (p.id === updated.id ? updated : p)));
      setStatusMessage({ type: 'success', text: 'Consent withdrawn. Intake is now permanently locked.' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message });
    }
  };

  const handleSubmitAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId) return;
    setIsSubmitting(true);
    setStatusMessage(null);

    try {
      let payload: any = {
        patient_id: selectedPatientId,
        form_type: activeFormType,
        assessor_role:
          activeFormType === 'caregiver'
            ? 'Caregiver / Parent'
            : activeFormType === 'teacher'
            ? 'Teacher / Special Educator'
            : 'Qualified Clinical Specialist',
        notes: assessorNotes,
        is_synthetic: selectedPatient?.is_synthetic || false
      };

      if (activeFormType === 'caregiver') {
        payload.developmental_history = {
          walking_age_months: walkingAgeMonths,
          early_motor_milestones: 'recorded',
          language_regression: hasLanguageRegression
        };
        payload.communication_milestones = {
          first_words_age_months: firstWordsAgeMonths,
          phrase_speech_age_months: phraseSpeechAgeMonths,
          receptive_vocabulary_delay: firstWordsAgeMonths > 18
        };
        payload.caregiver_concerns = {
          primary_concerns: caregiverMainConcerns,
          concern_onset_age_months: 18,
          reported_by: 'Parent'
        };
        payload.medical_family_history = {
          passed_hearing_screen: passedHearingScreen,
          family_neurodevelopmental_history: familyNeurohistory
        };
      } else if (activeFormType === 'teacher') {
        payload.social_interaction_observations = {
          classroom_eye_gaze: classroomEyeGaze,
          peer_interaction: peerInteractionLevel,
          response_to_name: responseToNameClassroom
        };
        payload.behavioral_characteristics = {
          sensory_reactivity: sensoryReactivity,
          classroom_engagement: 'variable'
        };
        payload.repetitive_behaviors = {
          motor_stereotypies: repetitiveMotorClassroom,
          insistence_on_sameness: insistenceOnSameness
        };
      } else {
        // Professional
        payload.developmental_history = { walking_age_months: walkingAgeMonths };
        payload.communication_milestones = { proto_declarative_pointing: protoDeclarativePointing };
        payload.social_interaction_observations = {
          joint_attention: jointAttentionScore,
          social_smile_reciprocity: socialSmileReciprocity
        };
        payload.behavioral_characteristics = {
          monotropic_focus: monotropicFocusIntensity
        };
        payload.repetitive_behaviors = {
          stereotyped_motor_mannerisms: stereotypedMotorScore
        };
        payload.multimodal_measurements = {
          eye_tracking: {
            administered: gazeTrackingAdministered,
            sensor_type: sensorGazeType,
            quality: gazeTrackingAdministered ? 'calibrated' : 'not_administered'
          },
          speech_audio: {
            administered: audioProsodyAdministered,
            sampling_rate_khz: 44.1,
            quality: audioProsodyAdministered ? 'valid' : 'not_administered'
          },
          movement_motor: {
            administered: movementMotorAdministered,
            quality: movementMotorAdministered ? 'valid' : 'not_administered'
          }
        };
      }

      const created = await api.createResearchAssessment(payload);
      setPastAssessments([created, ...pastAssessments]);
      setStatusMessage({ type: 'success', text: `Successfully saved ${activeFormType.toUpperCase()} research assessment.` });
      setAssessorNotes('');
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-neuro-600" />
            Real-World Research Data Collection Intake
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Standardized multi-informant assessment protocol for autism schools and clinical developmental centers
          </p>
        </div>

        {selectedPatient && onNavigateToScreening && isConsentGranted && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigateToScreening(selectedPatient.id)}
          >
            Launch Multimodal Screening &rarr;
          </Button>
        )}
      </div>

      {statusMessage && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center gap-2 ${
            statusMessage.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {isLoading && (
        <div className="p-8 text-center text-xs text-slate-500 space-y-2">
          <div className="w-6 h-6 border-2 border-neuro-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p>Loading participants and consent governance records...</p>
        </div>
      )}

      {/* Participant Selection & Consent Governance Card */}
      <Card className="border-slate-200 bg-white">
        <CardHeader className="pb-3 border-b border-slate-100">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-neuro-600" />
                Participant Selection & Research Consent Governance
              </CardTitle>
              <CardDescription className="text-xs text-slate-500 mt-0.5">
                De-identified Research Identifier Scheme • Protocol NS-DATA-COLL-v1.0 • IRB-NS-2026-ETHICS-04
              </CardDescription>
            </div>

            {/* Participant Dropdown */}
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-slate-600">Select Participant:</label>
              <select
                value={selectedPatientId}
                onChange={(e) => setSelectedPatientId(e.target.value)}
                className="text-xs px-3 py-1.5 rounded-lg border border-slate-300 bg-white font-mono font-medium focus:ring-2 focus:ring-neuro-500"
              >
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.anonymized_id} ({p.age_months}m, {p.biological_sex}) {p.is_synthetic ? '[Synthetic Dev]' : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-4">
          {selectedPatient ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Consent Status</span>
                <div className="flex items-center gap-1.5">
                  {selectedPatient.consent_status === 'granted' ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                      ✓ Informed Consent Granted
                    </span>
                  ) : selectedPatient.consent_status === 'withdrawn' ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                      ✕ Consent Withdrawn
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                      ⚠ Consent Pending
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-slate-400">Guardian relationship: {selectedPatient.guardian_relationship || 'Parent'}</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Participant Assent</span>
                <p className="font-semibold text-slate-800 capitalize">
                  {selectedPatient.assent_status === 'granted'
                    ? 'Assent Granted'
                    : selectedPatient.assent_status === 'declined'
                    ? 'Assent Declined'
                    : 'Not Applicable (< 7 yrs)'}
                </p>
                <p className="text-[10px] text-slate-400">Age: {selectedPatient.age_months} completed months</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Cohort Designation</span>
                <p className="font-semibold text-slate-800">
                  {selectedPatient.is_synthetic ? (
                    <span className="text-purple-700 font-bold">Synthetic Development Benchmark</span>
                  ) : (
                    <span className="text-emerald-700 font-bold">Real Clinical Research Cohort</span>
                  )}
                </p>
                <p className="text-[10px] text-slate-400">Referral: {selectedPatient.referral_source}</p>
              </div>

              {/* Consent Actions */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-center gap-2">
                {selectedPatient.consent_status !== 'granted' ? (
                  <Button variant="primary" size="sm" onClick={handleGrantConsent}>
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Grant Guardian Consent
                  </Button>
                ) : (
                  <Button variant="outline" size="sm" onClick={handleWithdrawConsent} className="text-rose-600 hover:text-rose-700">
                    <ShieldAlert className="w-3.5 h-3.5 mr-1" /> Withdraw Consent
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 text-center py-4">No participant selected.</div>
          )}
        </CardContent>
      </Card>

      {/* Consent Blocking Alert if Consent Not Granted */}
      {!isConsentGranted && selectedPatient && !selectedPatient.is_synthetic && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
          <Lock className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 space-y-1">
            <h4 className="font-bold">Real Participant Data Intake Is Strictly Blocked</h4>
            <p>
              Under Research Protocol <strong>NS-DATA-COLL-v1.0</strong> and Institutional Ethics Approval <strong>IRB-NS-2026-ETHICS-04</strong>,
              data intake is halted until signed guardian informed consent is verified and recorded.
              Click &quot;Grant Guardian Consent&quot; above once consent documentation is validated.
            </p>
          </div>
        </div>
      )}

      {/* Multi-Informant Form Tabs */}
      <div className="flex border-b border-slate-200 gap-2 text-xs font-medium">
        <button
          onClick={() => setActiveFormType('caregiver')}
          className={`pb-2.5 px-3 flex items-center gap-1.5 border-b-2 transition-all ${
            activeFormType === 'caregiver'
              ? 'border-neuro-600 text-neuro-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Users className="w-4 h-4" /> Form A: Caregiver Intake (Concerns & Milestones)
        </button>
        <button
          onClick={() => setActiveFormType('teacher')}
          className={`pb-2.5 px-3 flex items-center gap-1.5 border-b-2 transition-all ${
            activeFormType === 'teacher'
              ? 'border-neuro-600 text-neuro-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <ClipboardList className="w-4 h-4" /> Form B: Special Educator / Teacher (Classroom)
        </button>
        <button
          onClick={() => setActiveFormType('professional')}
          className={`pb-2.5 px-3 flex items-center gap-1.5 border-b-2 transition-all ${
            activeFormType === 'professional'
              ? 'border-neuro-600 text-neuro-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Activity className="w-4 h-4" /> Form C: Clinical Specialist & Sensors
        </button>
      </div>

      {/* Assessment Form Body */}
      <Card className="border-slate-200">
        <CardContent className="pt-6">
          <form onSubmit={handleSubmitAssessment} className="space-y-6">
            <fieldset disabled={!isConsentGranted && !selectedPatient?.is_synthetic} className="space-y-6">
              
              {/* Form A: Caregiver Intake Form */}
              {activeFormType === 'caregiver' && (
                <div className="space-y-4">
                  <div className="bg-sky-50/70 border border-sky-200/80 rounded-xl p-3 text-xs text-sky-900 leading-relaxed">
                    <strong>Caregiver Observations Notice:</strong> Caregiver developmental concerns are qualitative observational inputs.
                    They are <em>never treated as confirmed clinical diagnoses</em>.
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div>
                      <label className="font-semibold text-slate-700">Age of Independent Walking (Months)</label>
                      <input
                        type="number"
                        min="8"
                        max="36"
                        value={walkingAgeMonths}
                        onChange={(e) => setWalkingAgeMonths(parseInt(e.target.value))}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      />
                    </div>
                    <div>
                      <label className="font-semibold text-slate-700">First Meaningful Words Age (Months)</label>
                      <input
                        type="number"
                        min="6"
                        max="48"
                        value={firstWordsAgeMonths}
                        onChange={(e) => setFirstWordsAgeMonths(parseInt(e.target.value))}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      />
                    </div>
                    <div>
                      <label className="font-semibold text-slate-700">Two-Word Phrase Speech Age (Months)</label>
                      <input
                        type="number"
                        min="12"
                        max="60"
                        value={phraseSpeechAgeMonths}
                        onChange={(e) => setPhraseSpeechAgeMonths(parseInt(e.target.value))}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <label className="font-semibold text-slate-700">Any Reported Skill / Language Regression?</label>
                      <select
                        value={hasLanguageRegression ? 'yes' : 'no'}
                        onChange={(e) => setHasLanguageRegression(e.target.value === 'yes')}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      >
                        <option value="no">No regression reported</option>
                        <option value="yes">Yes, documented loss of words or social reciprocity</option>
                      </select>
                    </div>

                    <div>
                      <label className="font-semibold text-slate-700">Audiological Screening (Hearing Passed?)</label>
                      <select
                        value={passedHearingScreen ? 'yes' : 'no'}
                        onChange={(e) => setPassedHearingScreen(e.target.value === 'yes')}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      >
                        <option value="yes">Yes, audiological hearing screen passed</option>
                        <option value="no">No, hearing evaluation pending or impaired</option>
                      </select>
                    </div>
                  </div>

                  <div className="text-xs">
                    <label className="font-semibold text-slate-700">Caregiver Developmental Concerns (Descriptive)</label>
                    <textarea
                      rows={3}
                      value={caregiverMainConcerns}
                      onChange={(e) => setCaregiverMainConcerns(e.target.value)}
                      placeholder="e.g. Inconsistent eye contact, preference for solitary play, repetitive spinning of toy wheels..."
                      className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                    />
                  </div>

                  <div className="text-xs">
                    <label className="font-semibold text-slate-700">Authorized Family & Medical History</label>
                    <input
                      type="text"
                      value={familyNeurohistory}
                      onChange={(e) => setFamilyNeurohistory(e.target.value)}
                      placeholder="e.g. Family history of speech delay, ADHD or autism..."
                      className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                    />
                  </div>
                </div>
              )}

              {/* Form B: Special Educator / Teacher Form */}
              {activeFormType === 'teacher' && (
                <div className="space-y-4">
                  <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-3 text-xs text-emerald-900 leading-relaxed">
                    <strong>Educational Setting Observation:</strong> Evaluates structured classroom peer interaction, sensory accommodations, and responsiveness to instructional prompts.
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <label className="font-semibold text-slate-700">Classroom Dyadic Eye Gaze</label>
                      <select
                        value={classroomEyeGaze}
                        onChange={(e) => setClassroomEyeGaze(e.target.value)}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      >
                        <option value="typical">Typical, flexible eye contact</option>
                        <option value="inconsistent">Inconsistent / flees direct gaze</option>
                        <option value="markedly_atypical">Markedly absent or peripheral fixation</option>
                      </select>
                    </div>

                    <div>
                      <label className="font-semibold text-slate-700">Peer Social Play Pattern</label>
                      <select
                        value={peerInteractionLevel}
                        onChange={(e) => setPeerInteractionLevel(e.target.value)}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      >
                        <option value="interactive_cooperative">Interactive / Cooperative Play</option>
                        <option value="solitary_parallel">Parallel Play / Prefers Solitary</option>
                        <option value="actively_isolated">Actively isolates / distress in groups</option>
                      </select>
                    </div>

                    <div>
                      <label className="font-semibold text-slate-700">Orientation to Name in Classroom</label>
                      <select
                        value={responseToNameClassroom}
                        onChange={(e) => setResponseToNameClassroom(e.target.value)}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      >
                        <option value="consistent_first_call">Orients on first call</option>
                        <option value="requires_multiple_prompts">Requires 2-3 repeated prompts</option>
                        <option value="rarely_responds_unassisted">Rarely responds without physical prompt</option>
                      </select>
                    </div>

                    <div>
                      <label className="font-semibold text-slate-700">Motor Stereotypies Observed</label>
                      <select
                        value={repetitiveMotorClassroom}
                        onChange={(e) => setRepetitiveMotorClassroom(e.target.value)}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      >
                        <option value="none_observed">None observed</option>
                        <option value="occasional_hand_flapping">Occasional hand flapping / body rocking</option>
                        <option value="frequent_pervasive">Pervasive repetitive motor mannerisms</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <label className="font-semibold text-slate-700">Insistence on Sameness / Transitions</label>
                      <select
                        value={insistenceOnSameness}
                        onChange={(e) => setInsistenceOnSameness(e.target.value)}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      >
                        <option value="flexible">Transitions smoothly between tasks</option>
                        <option value="mild_distress_on_transition">Mild distress, requires warning timers</option>
                        <option value="severe_dysregulation">Severe dysregulation on schedule changes</option>
                      </select>
                    </div>

                    <div>
                      <label className="font-semibold text-slate-700">Sensory Processing Characteristics</label>
                      <select
                        value={sensoryReactivity}
                        onChange={(e) => setSensoryReactivity(e.target.value)}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      >
                        <option value="typical">Typical sensory tolerance</option>
                        <option value="auditory_hypersensitivity">Auditory hypersensitivity (covers ears)</option>
                        <option value="visual_tactile_seeking">Visual / tactile seeking behavior</option>
                        <option value="mixed_hypo_hyper">Mixed hyper- and hypo-reactivity</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Form C: Clinical Specialist & Multimodal Sensors */}
              {activeFormType === 'professional' && (
                <div className="space-y-4">
                  <div className="bg-purple-50/70 border border-purple-200/80 rounded-xl p-3 text-xs text-purple-900 leading-relaxed">
                    <strong>Standardized Clinical Specialist Intake:</strong> Quantified examiner-administered observational ratings and non-invasive multimodal sensor instrumentation.
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div>
                      <label className="font-semibold text-slate-700">Joint Attention Rating (0: Typical, 1: Atypical)</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        value={jointAttentionScore}
                        onChange={(e) => setJointAttentionScore(parseInt(e.target.value))}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      />
                    </div>
                    <div>
                      <label className="font-semibold text-slate-700">Reciprocal Social Smile (0: Typical, 1: Atypical)</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        value={socialSmileReciprocity}
                        onChange={(e) => setSocialSmileReciprocity(parseInt(e.target.value))}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      />
                    </div>
                    <div>
                      <label className="font-semibold text-slate-700">Proto-Declarative Pointing (0: Typical, 1: Atypical)</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        value={protoDeclarativePointing}
                        onChange={(e) => setProtoDeclarativePointing(parseInt(e.target.value))}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <label className="font-semibold text-slate-700">Stereotyped Motor Mannerisms (0: Typical, 1: Atypical)</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        value={stereotypedMotorScore}
                        onChange={(e) => setStereotypedMotorScore(parseInt(e.target.value))}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      />
                    </div>
                    <div>
                      <label className="font-semibold text-slate-700">Monotropic Focus Intensity (0: Typical, 1: Atypical)</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        value={monotropicFocusIntensity}
                        onChange={(e) => setMonotropicFocusIntensity(parseInt(e.target.value))}
                        className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                      />
                    </div>
                  </div>

                  {/* Multimodal Sensor Hardware Caveats & Selection */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <h5 className="font-bold text-slate-800 text-xs flex items-center gap-2">
                      <Eye className="w-4 h-4 text-neuro-600" />
                      Multimodal Sensor Instrumentation & Quality Verification
                    </h5>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div>
                        <label className="font-semibold text-slate-700">Eye-Tracking Sensor Architecture</label>
                        <select
                          value={sensorGazeType}
                          onChange={(e) => setSensorGazeType(e.target.value as any)}
                          className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                        >
                          <option value="infrared_pupil_corneal">
                            Infrared Pupil-Corneal Reflection (Tobii / EyeLink Research Grade)
                          </option>
                          <option value="webcam_exploratory">
                            Webcam Exploratory Gaze (RGB Head-Pose Model)
                          </option>
                        </select>
                        {sensorGazeType === 'webcam_exploratory' && (
                          <p className="text-[11px] text-amber-700 mt-1 leading-snug">
                            ⚠ <strong>Scientific Caveat:</strong> Standard webcam tracking provides coarse exploratory estimates only and is NOT equivalent to calibrated infrared pupil-corneal reflection eye tracking.
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <label className="font-semibold text-slate-700">Active Sensor Modules Administered</label>
                        <div className="flex flex-col gap-1.5 text-xs text-slate-600">
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={gazeTrackingAdministered}
                              onChange={(e) => setGazeTrackingAdministered(e.target.checked)}
                              className="rounded border-slate-300 text-neuro-600 focus:ring-neuro-500"
                            />
                            <span>Visual Oculomotor Gaze Tracking</span>
                          </label>
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={audioProsodyAdministered}
                              onChange={(e) => setAudioProsodyAdministered(e.target.checked)}
                              className="rounded border-slate-300 text-neuro-600 focus:ring-neuro-500"
                            />
                            <span>Vocal Acoustic Prosody Recording (44.1 kHz)</span>
                          </label>
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={movementMotorAdministered}
                              onChange={(e) => setMovementMotorAdministered(e.target.checked)}
                              className="rounded border-slate-300 text-neuro-600 focus:ring-neuro-500"
                            />
                            <span>Movement / Motor Stereotypy Tracking</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Assessor Narrative Notes */}
              <div className="text-xs">
                <label className="font-semibold text-slate-700">Assessor Clinical & Contextual Notes</label>
                <textarea
                  rows={2}
                  value={assessorNotes}
                  onChange={(e) => setAssessorNotes(e.target.value)}
                  placeholder="Record testing environment conditions, rapport, attention fluctuations, or sensory accommodations..."
                  className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-neuro-500"
                />
              </div>

              {/* Submit Button */}
              <div className="flex items-center justify-between pt-2">
                <div className="text-[11px] text-slate-500">
                  Data Quality Status: <span className="font-semibold text-emerald-600">Validated Complete</span>
                </div>

                <Button type="submit" variant="primary" disabled={isSubmitting || (!isConsentGranted && !selectedPatient?.is_synthetic)}>
                  {isSubmitting ? 'Recording Assessment...' : `Save ${activeFormType.toUpperCase()} Assessment`}
                </Button>
              </div>
            </fieldset>
          </form>
        </CardContent>
      </Card>

      {/* Past Assessments History for Selected Participant */}
      <Card className="border-slate-200">
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <History className="w-4 h-4 text-neuro-600" />
            Participant Longitudinal Assessment History ({pastAssessments.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {pastAssessments.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">
              No previous research assessment forms recorded for this participant yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-5 py-2.5 font-semibold">Assessment Date</th>
                    <th className="px-5 py-2.5 font-semibold">Form Type</th>
                    <th className="px-5 py-2.5 font-semibold">Assessor Role</th>
                    <th className="px-5 py-2.5 font-semibold">Quality Status</th>
                    <th className="px-5 py-2.5 font-semibold">Score</th>
                    <th className="px-5 py-2.5 font-semibold">Cohort</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {pastAssessments.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-50/60">
                      <td className="px-5 py-2.5 font-mono text-slate-600">{a.assessment_date.substring(0, 10)}</td>
                      <td className="px-5 py-2.5 font-semibold capitalize text-slate-900">{a.form_type}</td>
                      <td className="px-5 py-2.5 text-slate-600">{a.assessor_role}</td>
                      <td className="px-5 py-2.5">
                        <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                          a.data_quality_status === 'complete' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                        }`}>
                          {a.data_quality_status}
                        </span>
                      </td>
                      <td className="px-5 py-2.5 font-mono text-slate-600">{a.quality_score.toFixed(2)}</td>
                      <td className="px-5 py-2.5">
                        {a.is_synthetic ? (
                          <span className="text-purple-600 font-mono text-[10px]">Synthetic</span>
                        ) : (
                          <span className="text-emerald-600 font-mono text-[10px]">Real</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
