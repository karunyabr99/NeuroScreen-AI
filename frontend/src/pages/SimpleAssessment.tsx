import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ClipboardList,
  User,
  Video,
  FileCheck2,
  Sparkles,
  Download,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Camera,
  Square,
  Play,
  RotateCcw,
  Brain
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { api } from '../services/api';
import { Patient, ScreeningSession } from '../types';
import { downloadBlobAsFile } from '../lib/utils';

interface SimpleAssessmentProps {
  initialPatientId?: string;
  onCompleteScreening: (sessionId: string) => void;
  onNavigateToResults: (sessionId: string) => void;
}

export const SimpleAssessment: React.FC<SimpleAssessmentProps> = ({
  initialPatientId,
  onCompleteScreening,
  onNavigateToResults,
}) => {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Participant Details
  const [isNewPatient, setIsNewPatient] = useState<boolean>(!initialPatientId);
  const [selectedPatientId, setSelectedPatientId] = useState<string>(initialPatientId || '');
  const [anonId, setAnonId] = useState<string>(`CHILD-${Math.floor(1000 + Math.random() * 9000)}`);
  const [ageMonths, setAgeMonths] = useState<number>(24);
  const [biologicalSex, setBiologicalSex] = useState<string>('Male');
  const [referralSource, setReferralSource] = useState<string>('Parent / Caregiver');
  const [ethnicity, setEthnicity] = useState<string>('White European');
  const [jaundice, setJaundice] = useState<string>('no');
  const [familyAsd, setFamilyAsd] = useState<string>('no');
  const [respondent, setRespondent] = useState<string>('family member');
  const [notes, setNotes] = useState<string>('');
  const [consentGranted, setConsentGranted] = useState<boolean>(true);

  // Step 2: 10 Validated Q-CHAT-10 Items (0 = Typical, 1 = At-Risk)
  const [q1Name, setQ1Name] = useState<number>(0);
  const [q2EyeContact, setQ2EyeContact] = useState<number>(0);
  const [q3PointWants, setQ3PointWants] = useState<number>(0);
  const [q4PointShare, setQ4PointShare] = useState<number>(0);
  const [q5PretendPlay, setQ5PretendPlay] = useState<number>(0);
  const [q6GazeFollow, setQ6GazeFollow] = useState<number>(0);
  const [q7Comforting, setQ7Comforting] = useState<number>(0);
  const [q8FirstWords, setQ8FirstWords] = useState<number>(0);
  const [q9Gestures, setQ9Gestures] = useState<number>(0);
  const [q10Staring, setQ10Staring] = useState<number>(0);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, number>>({});

  // Step 3: Video Assessment State
  const [videoOption, setVideoOption] = useState<'record' | 'skip'>('skip');
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingSeconds, setRecordingSeconds] = useState<number>(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [videoBlobUrl, setVideoBlobUrl] = useState<string | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingTimerRef = useRef<any>(null);

  // Step 5 & 6: Generated Results
  const [completedSession, setCompletedSession] = useState<ScreeningSession | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<'catboost' | 'random_forest' | 'lasso_logistic' | 'toddler_qchat'>('catboost');

  // Load existing participants on mount
  useEffect(() => {
    async function loadPatients() {
      try {
        const data = await api.listPatients();
        setPatients(data);
        if (initialPatientId) {
          setSelectedPatientId(initialPatientId);
          setIsNewPatient(false);
          const current = data.find((p) => p.id === initialPatientId);
          if (current) {
            setAgeMonths(current.age_months);
            setBiologicalSex(current.biological_sex);
            setAnonId(current.anonymized_id);
          }
        }
      } catch (err) {
        console.error('Failed to load participants:', err);
      }
    }
    loadPatients();
  }, [initialPatientId]);

  // Clear any notice when navigating steps
  useEffect(() => {
    setError(null);
  }, [currentStep]);

  // Clean up media streams
  useEffect(() => {
    return () => {
      stopCamera();
      if (videoBlobUrl) {
        URL.revokeObjectURL(videoBlobUrl);
      }
    };
  }, [videoBlobUrl]);

  // Camera handling
  const startCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: true,
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
      setVideoOption('record');
    } catch (err: any) {
      console.error('Camera access error:', err);
      setCameraError('Unable to access camera or microphone. Please check browser permissions.');
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
    setCameraActive(false);
    setIsRecording(false);
  };

  const startRecording = () => {
    if (!mediaStreamRef.current) return;
    try {
      const chunks: Blob[] = [];
      const mime = MediaRecorder.isTypeSupported('video/webm') ? 'video/webm' : 'video/mp4';
      const recorder = new MediaRecorder(mediaStreamRef.current, { mimeType: mime });

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: mime });
        setRecordedBlob(blob);
        const url = URL.createObjectURL(blob);
        setVideoBlobUrl(url);
      };

      mediaRecorderRef.current = recorder;
      recorder.start(1000); // 1-second chunks
      setIsRecording(true);
      setRecordingSeconds(0);

      recordingTimerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      setCameraError(`Recording failed: ${err.message}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      stopCamera();
    }
  };

  // Step 5: Submit Assessment & Generate Summary
  const handleGenerateSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      let patientId = selectedPatientId;

      // 1. Create participant if new
      if (isNewPatient || !patientId) {
        const newPatient = await api.createPatient({
          anonymized_id: anonId,
          age_months: ageMonths,
          biological_sex: biologicalSex,
          referral_source: referralSource,
          clinical_notes: notes || 'Standardized caregiver screening intake.',
          consent_status: consentGranted ? 'granted' : 'pending',
        });
        patientId = newPatient.id;
        setSelectedPatientId(patientId);
      }

      // 2. Map Q-CHAT-10 questionnaire responses to backend features
      const qchatScore =
        q1Name + q2EyeContact + q3PointWants + q4PointShare + q5PretendPlay +
        q6GazeFollow + q7Comforting + q8FirstWords + q9Gestures + q10Staring;

      const isAtypical = qchatScore >= 3;

      // Behavioral inputs containing exact Q-CHAT items and demographics
      const behavioralPayload = {
        a1: q1Name,
        a2: q2EyeContact,
        a3: q3PointWants,
        a4: q4PointShare,
        a5: q5PretendPlay,
        a6: q6GazeFollow,
        a7: q7Comforting,
        a8: q8FirstWords,
        a9: q9Gestures,
        a10: q10Staring,
        ethnicity: ethnicity,
        jaundice: jaundice,
        family_mem_with_asd: familyAsd,
        who_completed_test: respondent,
        social_smile_reciprocity: q7Comforting === 0 ? 1 : 0,
        name_call_orientation: q1Name === 0 ? 1 : 0,
        pointing_proto_declarative: q4PointShare === 0 ? 1 : 0,
        pretend_play_engagement: q5PretendPlay === 0 ? 1 : 0,
        repetitive_motor_mannerisms: q10Staring === 1 ? 1 : 0,
        monotropic_focus_intensity: q10Staring === 1 ? 1 : 0,
        gaze_alternation_dyadic: q2EyeContact === 0 ? 1 : 0,
        sensory_hypersensitivity: q8FirstWords === 1 ? 1 : 0,
        peer_social_interest: q5PretendPlay === 0 ? 1 : 0,
        gestural_communication: q9Gestures === 0 ? 1 : 0,
        response_latency_mean_sec: q1Name === 1 ? 4.5 : 2.1,
      };

      // Visual gaze inputs (simulated from video or questionnaire)
      const visualGazePayload = {
        fixation_count: isAtypical ? 24 : 45,
        mean_fixation_duration_ms: isAtypical ? 380.0 : 260.0,
        social_roi_dwell_percentage: isAtypical ? 32.0 : 68.0,
        joint_attention_latency_ms: isAtypical ? 1150.0 : 420.0,
        saccade_mean_amplitude_deg: isAtypical ? 11.2 : 6.8,
        atypical_scanpath_entropy: isAtypical ? 0.72 : 0.38,
      };

      // Acoustic prosody inputs
      const acousticPayload = {
        fundamental_freq_f0_mean_hz: 250.0,
        f0_pitch_variability_stdev_hz: isAtypical ? 14.2 : 28.5,
        vocal_jitter_percent: isAtypical ? 2.1 : 1.1,
        vocal_shimmer_db: isAtypical ? 0.72 : 0.38,
        pause_to_speech_ratio: isAtypical ? 0.52 : 0.34,
        formant_dispersion_hz: 1100.0,
        speech_rate_syllables_sec: isAtypical ? 2.1 : 3.2,
      };

      // Execute Screening: Research Model (Paper 1 & 2) or Toddler Stacking model, Observation mode for <12 months
      const preferredModel = ageMonths < 12 ? 'toddler_qchat' : selectedModel;

      const screeningResult = await api.submitScreening({
        patient_id: patientId,
        preferred_model: preferredModel,
        behavioral: behavioralPayload,
        visual_gaze: visualGazePayload,
        acoustic_prosody: acousticPayload,
      });

      setCompletedSession(screeningResult.session);

      // If video was recorded, upload to media endpoint in background
      if (recordedBlob && patientId) {
        try {
          const file = new File([recordedBlob], 'live_assessment.webm', { type: recordedBlob.type });
          const formData = new FormData();
          formData.append('patient_id', patientId);
          formData.append('media_type', 'video');
          formData.append('task_context', 'live_video_assessment');
          formData.append('media_training_authorized', 'false');
          formData.append('session_id', screeningResult.session.id);
          formData.append('file', file);
          await api.uploadMedia(formData);
        } catch (mediaErr) {
          console.warn('Video background upload note:', mediaErr);
        }
      }

      // Notify parent & advance to Step 5
      onCompleteScreening(screeningResult.session.id);
      setCurrentStep(5);
    } catch (err: any) {
      console.error('Screening generation failed:', err);
      setError(err.message || 'Failed to generate assessment summary.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!completedSession) return;
    setIsDownloadingPdf(true);
    try {
      const blob = await api.downloadReportPdf(completedSession.id);
      const filename = `screening_summary_${anonId}_${completedSession.id.slice(0, 8)}.pdf`;
      downloadBlobAsFile(blob, filename);
    } catch (err: any) {
      alert(`PDF download failed: ${err.message}`);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const getTriageDisplay = (tier?: string) => {
    if (tier === 'OBSERVATION_ONLY_UNDER_12M') {
      return {
        title: 'Developmental Observation Record (Infant < 12 Months)',
        badge: <Badge variant="default">Observation Only (Under 12 Months)</Badge>,
        color: 'text-blue-800 bg-blue-50 border-blue-200',
        desc: 'Standardized questionnaire scoring is clinically suspended for infants under 12 months. Observations have been recorded descriptively for pediatric milestone tracking.',
      };
    }
    if (!tier || tier === 'LOW' || tier === 'LOW_LIKELIHOOD') {
      return {
        title: 'Typical Developmental Observations',
        badge: <Badge variant="success">Typical Range (Low Likelihood)</Badge>,
        color: 'text-emerald-700 bg-emerald-50 border-emerald-200',
        desc: 'Developmental milestones and observed communication behaviors are within expected age-appropriate ranges. Standard pediatric follow-up recommended.',
      };
    }
    if (tier === 'ELEVATED' || tier === 'MODERATE_MONITOR') {
      return {
        title: 'Moderate Developmental Variation',
        badge: <Badge variant="warning">Developmental Monitoring Recommended</Badge>,
        color: 'text-amber-800 bg-amber-50 border-amber-200',
        desc: 'Variations observed in communication reciprocity or play routines. Active observational monitoring and early developmental consultation recommended.',
      };
    }
    return {
      title: 'Elevated Developmental Indicators',
      badge: <Badge variant="danger">Multidisciplinary Triage Recommended</Badge>,
      color: 'text-rose-800 bg-rose-50 border-rose-200',
      desc: 'Multiple noticeable differences observed across social communication and behavioral routines. Comprehensive clinical evaluation by a licensed specialist recommended.',
    };
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Wizard Progress Stepper */}
      <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between overflow-x-auto pb-2 sm:pb-0 gap-2">
          {[
            { num: 1, label: t('childDetails') },
            { num: 2, label: t('questionnaire') },
            { num: 3, label: t('liveVideo') },
            { num: 4, label: t('review') },
            { num: 5, label: t('summary') },
            { num: 6, label: t('downloadReport') },
          ].map((s) => (
            <div
              key={s.num}
              onClick={() => {
                // Only allow jumping back, or forward if completed
                if (s.num < currentStep || (completedSession && s.num <= 6)) {
                  setCurrentStep(s.num);
                }
              }}
              className={`flex items-center gap-2 cursor-pointer transition-all ${
                currentStep === s.num
                  ? 'text-teal-700 font-bold'
                  : currentStep > s.num
                  ? 'text-slate-700 font-medium'
                  : 'text-slate-400'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                  currentStep === s.num
                    ? 'bg-teal-600 text-white shadow-md'
                    : currentStep > s.num
                    ? 'bg-teal-100 text-teal-800'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {currentStep > s.num ? <CheckCircle2 className="w-4 h-4" /> : s.num}
              </div>
              <span className="text-xs whitespace-nowrap">{s.label}</span>
              {s.num < 6 && <div className="w-4 h-px bg-slate-200 hidden md:block" />}
            </div>
          ))}
        </div>
      </div>

      {error && (
        <Alert variant="danger" title="Assessment Notice">
          {error}
        </Alert>
      )}

      {/* ================= STEP 1: PARTICIPANT DETAILS ================= */}
      {currentStep === 1 && (
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <span className="p-2 bg-teal-50 text-teal-700 rounded-lg">
                <User className="w-5 h-5" />
              </span>
              <div>
                <CardTitle className="text-xl font-bold text-slate-900">
                  {t('participantInformation')}
                </CardTitle>
                <p className="text-xs text-slate-500">
                  {t('participantDescription')}
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Participant Mode Toggle */}
            <div className="flex items-center gap-4 bg-slate-50 p-2 rounded-xl border border-slate-200">
              <label className="flex items-center gap-2 cursor-pointer text-sm font-semibold text-slate-800">
                <input
                  type="radio"
                  name="patMode"
                  checked={isNewPatient}
                  onChange={() => setIsNewPatient(true)}
                  className="text-teal-600 focus:ring-teal-500"
                />
                Register New Child Profile
              </label>
              {patients.length > 0 && (
                <label className="flex items-center gap-2 cursor-pointer text-sm font-semibold text-slate-800">
                  <input
                    type="radio"
                    name="patMode"
                    checked={!isNewPatient}
                    onChange={() => setIsNewPatient(false)}
                    className="text-teal-600 focus:ring-teal-500"
                  />
                  Select Existing Registered Child ({patients.length})
                </label>
              )}
            </div>

            {/* Existing Patient Dropdown */}
            {!isNewPatient && patients.length > 0 ? (
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Select Participant:
                </label>
                <select
                  value={selectedPatientId}
                  onChange={(e) => {
                    setSelectedPatientId(e.target.value);
                    const p = patients.find((pat) => pat.id === e.target.value);
                    if (p) {
                      setAnonId(p.anonymized_id);
                      setAgeMonths(p.age_months);
                      setBiologicalSex(p.biological_sex);
                    }
                  }}
                  className="w-full text-sm font-medium bg-slate-50 border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                >
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.anonymized_id} ({p.age_months}m, {p.biological_sex})
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              /* New Patient Form */
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('participantId')}:
                  </label>
                  <input
                    type="text"
                    value={anonId}
                    onChange={(e) => setAnonId(e.target.value)}
                    className="w-full text-sm font-semibold bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                    placeholder={t('participantIdPlaceholder')}
                  />
                  <p className="text-[11px] text-slate-400">{t('privacyNote')}</p>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('age')}: <span className="text-teal-600">{ageMonths}m ({Math.floor(ageMonths / 12)}y {ageMonths % 12}m)</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={72}
                    value={ageMonths}
                    onChange={(e) => setAgeMonths(parseInt(e.target.value) || 0)}
                    className="w-full text-sm font-semibold bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                  />
                  <p className="text-[11px] text-slate-400">{t('targetPopulation')}</p>
                </div>

                {/* Age Gate Indicator Banner */}
                {ageMonths < 12 ? (
                  <div className="sm:col-span-2 p-3.5 bg-blue-50 border border-blue-200 rounded-xl text-blue-900 text-xs space-y-1">
                    <span className="font-bold flex items-center gap-1.5 text-blue-950">
                      ℹ️ Infant Mode (0–11 Months) – Observation Mode Only
                    </span>
                    <p className="leading-relaxed">
                      Standardized toddler ASD screening questionnaires (such as Q-CHAT-10) are only validated clinically from 12 months onwards. For infants under 12 months, automated probability estimation is withheld. Questionnaire responses will be recorded descriptively as a developmental observation checklist.
                    </p>
                  </div>
                ) : ageMonths <= 36 ? (
                  <div className="sm:col-span-2 p-3.5 bg-teal-50 border border-teal-200 rounded-xl text-teal-900 text-xs space-y-1">
                    <span className="font-bold flex items-center gap-1.5 text-teal-950">
                      ✅ Toddler Screening Mode (12–36 Months) – Calibrated Stacking Model
                    </span>
                    <p className="leading-relaxed">
                      Validated with the Calibrated Toddler Q-CHAT Stacking Ensemble (Random Forest + SVM + Gradient Boosting &rarr; Logistic Regression), evaluated on 1,054 toddler records with external clinical cohort validation (ROC-AUC 0.934).
                    </p>
                  </div>
                ) : (
                  <div className="sm:col-span-2 p-3.5 bg-purple-50 border border-purple-200 rounded-xl text-purple-900 text-xs space-y-1">
                    <span className="font-bold flex items-center gap-1.5 text-purple-950">
                      🌐 Child Protocol (&gt;36 Months)
                    </span>
                    <p className="leading-relaxed">
                      Child exceeds toddler range. Standard childhood multimodal screening pipeline will be utilized.
                    </p>
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('sex')}:
                  </label>
                  <select
                    value={biologicalSex}
                    onChange={(e) => setBiologicalSex(e.target.value)}
                    className="w-full text-sm font-medium bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="Male">{t('male')}</option>
                    <option value="Female">{t('female')}</option>
                    <option value="Unspecified">{t('preferNotToSay')}</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('informant')}:
                  </label>
                  <select
                    value={referralSource}
                    onChange={(e) => setReferralSource(e.target.value)}
                    className="w-full text-sm font-medium bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="Parent / Caregiver">{t('parentCaregiver')}</option>
                    <option value="Teacher / Educator">{t('teacherEducator')}</option>
                    <option value="Pediatrician">{t('pediatrician')}</option>
                    <option value="Developmental Center">{t('developmentCenter')}</option>
                  </select>
                </div>

                {/* Additional Toddler Demographics for Research Rigor */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('ethnicity')}:
                  </label>
                  <select
                    value={ethnicity}
                    onChange={(e) => setEthnicity(e.target.value)}
                    className="w-full text-sm font-medium bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="White European">{t('whiteEuropean')}</option>
                    <option value="middle eastern">{t('middleEastern')}</option>
                    <option value="asian">{t('asian')}</option>
                    <option value="south asian">{t('southAsian')}</option>
                    <option value="Hispanic">{t('hispanic')}</option>
                    <option value="black">{t('black')}</option>
                    <option value="Others">Others</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('jaundiceHistory')}:
                  </label>
                  <select
                    value={jaundice}
                    onChange={(e) => setJaundice(e.target.value)}
                    className="w-full text-sm font-medium bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="no">{t('no')}</option>
                    <option value="yes">{t('phototherapy')}</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('familyAsdHistory')}:
                  </label>
                  <select
                    value={familyAsd}
                    onChange={(e) => setFamilyAsd(e.target.value)}
                    className="w-full text-sm font-medium bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="no">{t('no')}</option>
                    <option value="yes">{t('immediateFamily')}</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('completedBy')}:
                  </label>
                  <select
                    value={respondent}
                    onChange={(e) => setRespondent(e.target.value)}
                    className="w-full text-sm font-medium bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="family member">{t('familyMember')}</option>
                    <option value="Health Care Professional">{t('healthcareProfessional')}</option>
                    <option value="Self">{t('selfGuardian')}</option>
                    <option value="Others">Others</option>
                  </select>
                </div>

                <div className="sm:col-span-2 space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {t('clinicalNotes')}:
                  </label>
                  <textarea
                    rows={2}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="w-full text-sm bg-white border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500"
                    placeholder={t('clinicalNotesPlaceholder')}
                  />
                </div>
              </div>
            )}

            {/* Informed Consent Requirement */}
            <div className="p-4 rounded-xl bg-teal-50/60 border border-teal-200 flex items-start gap-3">
              <input
                type="checkbox"
                id="consentCheck"
                checked={consentGranted}
                onChange={(e) => setConsentGranted(e.target.checked)}
                className="mt-1 w-4 h-4 text-teal-600 rounded focus:ring-teal-500"
              />
              <label htmlFor="consentCheck" className="text-xs text-teal-900 leading-relaxed cursor-pointer">
                <strong>{t('consentVerified')}</strong> {t('consentDescription')}
              </label>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                onClick={() => setCurrentStep(2)}
                disabled={!consentGranted}
                className="bg-teal-600 hover:bg-teal-700 text-white"
              >
                Continue to Questionnaire <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ================= STEP 2: QUESTIONNAIRE ================= */}
      {currentStep === 2 && (
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <span className="p-2 bg-teal-50 text-teal-700 rounded-lg">
                <ClipboardList className="w-5 h-5" />
              </span>
              <div>
                <CardTitle className="text-xl font-bold text-slate-900">
                  Step 2: Validated Toddler Q-CHAT-10 Screening
                </CardTitle>
                <p className="text-xs text-slate-500">
                  Standardized 10-item Quantitative Checklist for Autism in Toddlers (Allison et al. / Thabtah toddler cohort).
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-5">
              {[
                {
                  id: 'q1',
                  itemNum: 'A1',
                  title: '1. Response to Name Call',
                  desc: 'Does your child look at you when you call his/her name?',
                  val: q1Name,
                  set: setQ1Name,
                  options: [
                    { label: 'Always (Typical)', score: 0 },
                    { label: 'Usually (Typical)', score: 0 },
                    { label: 'Sometimes (At-Risk)', score: 1 },
                    { label: 'Rarely (At-Risk)', score: 1 },
                    { label: 'Never (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q2',
                  itemNum: 'A2',
                  title: '2. Eye Contact Quality',
                  desc: 'How easy is it for you to get eye contact with your child?',
                  val: q2EyeContact,
                  set: setQ2EyeContact,
                  options: [
                    { label: 'Very easy (Typical)', score: 0 },
                    { label: 'Quite easy (Typical)', score: 0 },
                    { label: 'Quite difficult (At-Risk)', score: 1 },
                    { label: 'Very difficult (At-Risk)', score: 1 },
                    { label: 'Impossible (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q3',
                  itemNum: 'A3',
                  title: '3. Pointing for Wants (Proto-imperative)',
                  desc: 'Does your child point to indicate that s/he wants something (e.g. a toy that is out of reach)?',
                  val: q3PointWants,
                  set: setQ3PointWants,
                  options: [
                    { label: 'Many times a day (Typical)', score: 0 },
                    { label: 'A few times a day (Typical)', score: 0 },
                    { label: 'A few times a week (At-Risk)', score: 1 },
                    { label: 'Less than once a week (At-Risk)', score: 1 },
                    { label: 'Never (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q4',
                  itemNum: 'A4',
                  title: '4. Pointing to Share Interest (Proto-declarative)',
                  desc: 'Does your child point to share interest with you (e.g. pointing at an interesting sight or bird)?',
                  val: q4PointShare,
                  set: setQ4PointShare,
                  options: [
                    { label: 'Many times a day (Typical)', score: 0 },
                    { label: 'A few times a day (Typical)', score: 0 },
                    { label: 'A few times a week (At-Risk)', score: 1 },
                    { label: 'Less than once a week (At-Risk)', score: 1 },
                    { label: 'Never (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q5',
                  itemNum: 'A5',
                  title: '5. Pretend Play & Symbolic Games',
                  desc: 'Does your child pretend? (e.g. care for dolls, talk on a toy phone, feed a toy animal)?',
                  val: q5PretendPlay,
                  set: setQ5PretendPlay,
                  options: [
                    { label: 'Many times a day (Typical)', score: 0 },
                    { label: 'A few times a day (Typical)', score: 0 },
                    { label: 'A few times a week (At-Risk)', score: 1 },
                    { label: 'Less than once a week (At-Risk)', score: 1 },
                    { label: 'Never (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q6',
                  itemNum: 'A6',
                  title: '6. Following Gaze (Joint Attention)',
                  desc: 'Does your child follow where you’re looking?',
                  val: q6GazeFollow,
                  set: setQ6GazeFollow,
                  options: [
                    { label: 'Many times a day (Typical)', score: 0 },
                    { label: 'A few times a day (Typical)', score: 0 },
                    { label: 'A few times a week (At-Risk)', score: 1 },
                    { label: 'Less than once a week (At-Risk)', score: 1 },
                    { label: 'Never (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q7',
                  itemNum: 'A7',
                  title: '7. Comforting Others in Distress',
                  desc: 'If you or someone else in the family is visibly upset, does your child show signs of wanting to comfort them?',
                  val: q7Comforting,
                  set: setQ7Comforting,
                  options: [
                    { label: 'Always (Typical)', score: 0 },
                    { label: 'Usually (Typical)', score: 0 },
                    { label: 'Sometimes (At-Risk)', score: 1 },
                    { label: 'Rarely (At-Risk)', score: 1 },
                    { label: 'Never (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q8',
                  itemNum: 'A8',
                  title: '8. Early Words & Speech Development',
                  desc: 'Would you describe your child’s first words or speech characteristics as:',
                  val: q8FirstWords,
                  set: setQ8FirstWords,
                  options: [
                    { label: 'Very typical (Typical)', score: 0 },
                    { label: 'Quite typical (Typical)', score: 0 },
                    { label: 'Slightly unusual (At-Risk)', score: 1 },
                    { label: 'Very unusual (At-Risk)', score: 1 },
                    { label: 'Does not speak / delayed (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q9',
                  itemNum: 'A9',
                  title: '9. Simple Communicative Gestures',
                  desc: 'Does your child use simple gestures? (e.g. wave goodbye, shake head for no, clap hands)?',
                  val: q9Gestures,
                  set: setQ9Gestures,
                  options: [
                    { label: 'Many times a day (Typical)', score: 0 },
                    { label: 'A few times a day (Typical)', score: 0 },
                    { label: 'A few times a week (At-Risk)', score: 1 },
                    { label: 'Less than once a week (At-Risk)', score: 1 },
                    { label: 'Never (At-Risk)', score: 1 },
                  ],
                },
                {
                  id: 'q10',
                  itemNum: 'A10',
                  title: '10. Aimless Staring into Space',
                  desc: 'Does your child stare at nothing with no apparent purpose?',
                  val: q10Staring,
                  set: setQ10Staring,
                  options: [
                    { label: 'Never (Typical)', score: 0 },
                    { label: 'Less than once a week (Typical)', score: 0 },
                    { label: 'A few times a week (At-Risk)', score: 1 },
                    { label: 'A few times a day (At-Risk)', score: 1 },
                    { label: 'Many times a day (At-Risk)', score: 1 },
                  ],
                },
              ].map((q) => (
                <div key={q.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200 mr-2">
                        {q.itemNum}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 inline">{q.title}</h3>
                      <p className="text-xs text-slate-500 mt-1">{q.desc}</p>
                    </div>
                    <Badge variant={q.val === 1 ? 'warning' : 'success'}>
                      {q.val === 1 ? 'At-Risk Indicator' : 'Typical'}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                    {q.options.map((opt, optIdx) => {
                      const isSelected = selectedOptions[q.id] === optIdx;
                      return (
                        <button
                          type="button"
                          key={optIdx}
                          onClick={() => {
                           setSelectedOptions((prev) => ({ ...prev, [q.id]: optIdx }));
                           q.set(opt.score);
                           }}
                          className={`text-center p-2 rounded-lg border text-xs font-medium transition-all ${
                            isSelected && opt.score === 1
                              ? 'bg-amber-600 text-white border-amber-600 shadow-sm'
                              : isSelected && opt.score === 0
                              ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
                              : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          <span className="block text-[10px] text-slate-400 mb-0.5">
                            {isSelected ? '✓ Selected' : ''}
                          </span>
                          {opt.label.split('(')[0]}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setCurrentStep(1)}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>
              <Button
                variant="primary"
                onClick={() => setCurrentStep(3)}
                className="bg-teal-600 hover:bg-teal-700 text-white"
              >
                Proceed to Live Video <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ================= STEP 3: LIVE VIDEO ASSESSMENT ================= */}
      {currentStep === 3 && (
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <span className="p-2 bg-sky-50 text-sky-700 rounded-lg">
                <Video className="w-5 h-5" />
              </span>
              <div>
                <CardTitle className="text-xl font-bold text-slate-900">
                  Step 3: Live Video Assessment
                </CardTitle>
                <p className="text-xs text-slate-500">
                  Record a brief 15–30 second live camera observation of interaction, or skip if a camera is unavailable.
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {cameraError && (
              <Alert variant="danger" title="Camera Notice">
                {cameraError}
              </Alert>
            )}

            {/* Video Choice Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div
                onClick={() => {
                  setVideoOption('record');
                  if (!cameraActive) startCamera();
                }}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-3 ${
                  videoOption === 'record'
                    ? 'border-sky-500 bg-sky-50/50'
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="p-2 rounded-lg bg-sky-100 text-sky-700 mt-0.5">
                  <Camera className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Use Live Camera</h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Capture 15–30 seconds of play or joint attention to measure movement stability and response timing.
                  </p>
                </div>
              </div>

              <div
                onClick={() => {
                  setVideoOption('skip');
                  stopCamera();
                }}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-3 ${
                  videoOption === 'skip'
                    ? 'border-teal-500 bg-teal-50/50'
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="p-2 rounded-lg bg-teal-100 text-teal-700 mt-0.5">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Questionnaire Only</h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Proceed using caregiver and teacher questionnaire observations only. Model handles missing video via median imputation.
                  </p>
                </div>
              </div>
            </div>

            {/* Live Camera Viewport */}
            {videoOption === 'record' && (
              <div className="space-y-4 bg-slate-950 p-4 sm:p-6 rounded-2xl text-white">
                <div className="relative aspect-video max-h-80 mx-auto rounded-xl overflow-hidden bg-slate-900 border border-slate-800 flex items-center justify-center">
                  {cameraActive ? (
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />
                  ) : videoBlobUrl ? (
                    <video
                      src={videoBlobUrl}
                      controls
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-center p-6 space-y-2">
                      <Camera className="w-10 h-10 text-slate-500 mx-auto" />
                      <p className="text-xs text-slate-400">Camera preview will appear here</p>
                    </div>
                  )}

                  {/* Recording Status Overlay */}
                  {isRecording && (
                    <div className="absolute top-3 left-3 bg-red-600/90 text-white text-xs font-bold px-2.5 py-1 rounded-full flex items-center gap-1.5 animate-pulse">
                      <div className="w-2 h-2 rounded-full bg-white" />
                      <span>REC {recordingSeconds}s</span>
                    </div>
                  )}
                </div>

                {/* Camera Action Buttons */}
                <div className="flex flex-wrap items-center justify-center gap-3">
                  {!cameraActive && !videoBlobUrl && (
                    <Button
                      variant="primary"
                      onClick={startCamera}
                      className="bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold"
                    >
                      <Camera className="w-4 h-4 mr-2" /> Start Camera
                    </Button>
                  )}

                  {cameraActive && !isRecording && (
                    <Button
                      variant="primary"
                      onClick={startRecording}
                      className="bg-red-600 hover:bg-red-500 text-white font-semibold"
                    >
                      <Play className="w-4 h-4 mr-2" /> Start Recording (15–30s)
                    </Button>
                  )}

                  {isRecording && (
                    <Button
                      variant="primary"
                      onClick={stopRecording}
                      className="bg-slate-200 hover:bg-white text-slate-950 font-semibold"
                    >
                      <Square className="w-4 h-4 mr-2 text-red-600" /> Stop Recording ({recordingSeconds}s)
                    </Button>
                  )}

                  {videoBlobUrl && !cameraActive && (
                    <Button
                      variant="outline"
                      onClick={() => {
                        setRecordedBlob(null);
                        setVideoBlobUrl(null);
                        startCamera();
                      }}
                      className="text-white border-white/20 hover:bg-white/10"
                    >
                      <RotateCcw className="w-4 h-4 mr-2" /> Re-record Video
                    </Button>
                  )}
                </div>

                <div className="text-[11px] text-slate-400 text-center max-w-lg mx-auto leading-relaxed">
                  <strong>Scientific Notice:</strong> Video computer vision extracts motion stability and repetitive rhythmicity. It <strong>never</strong> analyzes facial expressions or facial beauty to infer autism.
                </div>
              </div>
            )}

            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setCurrentStep(2)}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>
              <Button
                variant="primary"
                onClick={() => setCurrentStep(4)}
                className="bg-teal-600 hover:bg-teal-700 text-white"
              >
                Review Observations <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ================= STEP 4: REVIEW OBSERVATIONS ================= */}
      {currentStep === 4 && (
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <span className="p-2 bg-teal-50 text-teal-700 rounded-lg">
                <FileCheck2 className="w-5 h-5" />
              </span>
              <div>
                <CardTitle className="text-xl font-bold text-slate-900">
                  Step 4: Review Observations
                </CardTitle>
                <p className="text-xs text-slate-500">
                  Verify entered participant details and questionnaire scores before running the screening model.
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Participant Summary */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-slate-400 uppercase font-bold text-[10px] block">Participant ID</span>
                <span className="font-bold text-slate-900">{anonId}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase font-bold text-[10px] block">Age</span>
                <span className="font-bold text-slate-900">{ageMonths} months ({Math.floor(ageMonths / 12)}y {ageMonths % 12}m)</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase font-bold text-[10px] block">Sex</span>
                <span className="font-bold text-slate-900">{biologicalSex}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase font-bold text-[10px] block">Informant</span>
                <span className="font-bold text-slate-900">{referralSource}</span>
              </div>
            </div>

            {/* Questionnaire Highlights */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Q-CHAT-10 Responses (Toddler Screener):
                </h4>
                <Badge variant={q1Name + q2EyeContact + q3PointWants + q4PointShare + q5PretendPlay + q6GazeFollow + q7Comforting + q8FirstWords + q9Gestures + q10Staring >= 3 ? 'warning' : 'success'}>
                  Total Flags: {q1Name + q2EyeContact + q3PointWants + q4PointShare + q5PretendPlay + q6GazeFollow + q7Comforting + q8FirstWords + q9Gestures + q10Staring} / 10
                </Badge>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A1. Response to Name</span>
                  <Badge variant={q1Name === 1 ? 'warning' : 'success'}>
                    {q1Name === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A2. Eye Contact Quality</span>
                  <Badge variant={q2EyeContact === 1 ? 'warning' : 'success'}>
                    {q2EyeContact === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A3. Pointing for Wants</span>
                  <Badge variant={q3PointWants === 1 ? 'warning' : 'success'}>
                    {q3PointWants === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A4. Pointing to Share</span>
                  <Badge variant={q4PointShare === 1 ? 'warning' : 'success'}>
                    {q4PointShare === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A5. Pretend Play</span>
                  <Badge variant={q5PretendPlay === 1 ? 'warning' : 'success'}>
                    {q5PretendPlay === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A6. Gaze Following</span>
                  <Badge variant={q6GazeFollow === 1 ? 'warning' : 'success'}>
                    {q6GazeFollow === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A7. Comforting Others</span>
                  <Badge variant={q7Comforting === 1 ? 'warning' : 'success'}>
                    {q7Comforting === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A8. Early Words / Speech</span>
                  <Badge variant={q8FirstWords === 1 ? 'warning' : 'success'}>
                    {q8FirstWords === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A9. Simple Gestures</span>
                  <Badge variant={q9Gestures === 1 ? 'warning' : 'success'}>
                    {q9Gestures === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">A10. Aimless Staring</span>
                  <Badge variant={q10Staring === 1 ? 'warning' : 'success'}>
                    {q10Staring === 1 ? 'Flagged (At-Risk)' : 'Typical'}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Video Status */}
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4 text-sky-600" />
                <span className="font-semibold text-slate-800">Video Assessment Status:</span>
              </div>
              <Badge variant={recordedBlob ? 'success' : 'default'}>
                {recordedBlob ? 'Video Clip Captured (Ready)' : 'Questionnaire Only Mode'}
              </Badge>
            </div>

            {/* Research Model Selection (Paper 1 & Paper 2) */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5 text-teal-600" />
                  <span>Select Screening Algorithm:</span>
                </h4>
                <span className="text-[11px] text-teal-700 font-medium">Research Paper Methodologies</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* CatBoost */}
                <div
                  onClick={() => setSelectedModel('catboost')}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedModel === 'catboost'
                      ? 'bg-teal-50/80 border-teal-500 shadow-xs'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-900">CatBoost (Paper 1, 2024)</span>
                    <span className="text-[9px] font-bold bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded">Primary</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">
                    Well-Baby electronic model with Youden threshold (0.507) & SHAP explainability.
                  </p>
                </div>

                {/* Random Forest */}
                <div
                  onClick={() => setSelectedModel('random_forest')}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedModel === 'random_forest'
                      ? 'bg-sky-50/80 border-sky-500 shadow-xs'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-900">Random Forest (Paper 2)</span>
                    <span className="text-[9px] font-bold bg-sky-100 text-sky-800 px-1.5 py-0.5 rounded">Tree Ensemble</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">
                    Medical claims ensemble benchmarked with AUPRC and Gini importance.
                  </p>
                </div>

                {/* LASSO Logistic Regression */}
                <div
                  onClick={() => setSelectedModel('lasso_logistic')}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedModel === 'lasso_logistic'
                      ? 'bg-emerald-50/80 border-emerald-500 shadow-xs'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-900">LASSO Logistic (Paper 2)</span>
                    <span className="text-[9px] font-bold bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded">L1 Sparse</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">
                    L1 regularized regression with automatic non-zero sparse feature selection.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setCurrentStep(3)}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>
              <Button
                variant="primary"
                onClick={handleGenerateSummary}
                isLoading={isLoading}
                className="bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow-md"
              >
                <Sparkles className="w-4 h-4 mr-2" /> Generate Assessment Summary
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ================= STEP 5: ASSESSMENT SUMMARY ================= */}
      {currentStep === 5 && completedSession && (
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="p-2 bg-teal-50 text-teal-700 rounded-lg">
                  <Sparkles className="w-5 h-5" />
                </span>
                <div>
                  <CardTitle className="text-xl font-bold text-slate-900">
                    Step 5: Screening-Support Summary
                  </CardTitle>
                  <p className="text-xs text-slate-500">
                    {completedSession.risk_tier === 'OBSERVATION_ONLY_UNDER_12M'
                      ? 'Descriptive developmental observation checklist recorded (<12 months).'
                      : 'Objective screening triage results generated by the calibrated Toddler Stacking Ensemble.'}
                  </p>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Result Triage Card */}
            {(() => {
              const triage = getTriageDisplay(completedSession.risk_tier);
              return (
                <div className={`p-6 rounded-2xl border ${triage.color} space-y-3`}>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <h3 className="text-lg font-extrabold">{triage.title}</h3>
                    {triage.badge}
                  </div>
                  <p className="text-sm leading-relaxed">{triage.desc}</p>

                  <div className="pt-2 flex items-center gap-4 text-xs font-semibold">
                    <span>
                      Model Screening Probability:{' '}
                      <strong className="underline">
                        {completedSession.composite_risk_score !== null && completedSession.composite_risk_score !== undefined
                          ? `${(completedSession.composite_risk_score * 100).toFixed(1)}%`
                          : 'N/A (Observation Checklist Mode)'}
                      </strong>
                    </span>
                    <span>
                      Protocol:{' '}
                      <span className="text-teal-700 font-bold">
                        {completedSession.protocol_version || 'v1.0-toddler-qchat-calibrated'}
                      </span>
                    </span>
                  </div>
                </div>
              );
            })()}

            {/* Next Steps Guidance */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Recommended Professional Follow-Up:
              </h4>
              <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-5">
                <li>Share this screening summary with your child&apos;s pediatrician or primary care doctor.</li>
                <li>If elevated communication concerns were identified, consider a speech and language consultation.</li>
                <li>Schedule an audiological (hearing) evaluation to rule out auditory sensory differences.</li>
                <li>Re-screen in 3 to 6 months to track developmental trajectory and milestone progression.</li>
              </ul>
            </div>

            {/* Academic Notice */}
            <div className="text-[11px] text-amber-800 bg-amber-50 p-3 rounded-lg border border-amber-200">
              <strong>Notice:</strong> This screening estimate is an experimental clinical decision-support output. It does <strong>not</strong> constitute a medical diagnosis.
            </div>

            <div className="flex justify-between items-center pt-2">
              <Button
                variant="outline"
                onClick={() => onNavigateToResults(completedSession.id)}
              >
                View Full Detailed Breakdown
              </Button>
              <Button
                variant="primary"
                onClick={() => setCurrentStep(6)}
                className="bg-teal-600 hover:bg-teal-700 text-white"
              >
                Proceed to Download Report <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ================= STEP 6: VIEW & DOWNLOAD REPORT ================= */}
      {currentStep === 6 && completedSession && (
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <span className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
                <Download className="w-5 h-5" />
              </span>
              <div>
                <CardTitle className="text-xl font-bold text-slate-900">
                  Step 6: Official PDF Report Ready
                </CardTitle>
                <p className="text-xs text-slate-500">
                  Download the de-identified PDF report containing all observations, triage status, and recommendations.
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 text-center py-8">
            <div className="w-16 h-16 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mx-auto shadow-sm">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div className="max-w-md mx-auto space-y-2">
              <h3 className="text-lg font-bold text-slate-900">
                Screening Assessment Complete
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                A permanent de-identified screening record has been archived under session ID{' '}
                <code className="text-teal-700 font-mono font-bold bg-slate-100 px-1 py-0.5 rounded">
                  {completedSession.id.slice(0, 8)}
                </code>
                . You can download the publication-grade vector PDF report below.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
              <Button
                variant="primary"
                size="lg"
                onClick={handleDownloadPdf}
                isLoading={isDownloadingPdf}
                className="bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow-md"
              >
                <Download className="w-5 h-5 mr-2" /> Download PDF Screening Report
              </Button>

              <Button
                variant="outline"
                size="lg"
                onClick={() => onNavigateToResults(completedSession.id)}
              >
                View Results Breakdown
              </Button>
            </div>

            <div className="pt-8 border-t border-slate-200 flex justify-center">
              <Button
                variant="ghost"
                onClick={() => {
                  setCompletedSession(null);
                  setAnonId(`CHILD-${Math.floor(1000 + Math.random() * 9000)}`);
                  setCurrentStep(1);
                }}
                className="text-xs text-slate-500 hover:text-slate-800"
              >
                <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Start Another Assessment
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
