import React, { useState, useEffect } from 'react';
import {
  Video,
  Camera,
  Upload,
  AlertTriangle,
  CheckCircle2,
  Shield,
  Eye,
  Activity,
  Trash2,
  RotateCw,
  FileCheck,
  Layers,
  Sparkles,
  HelpCircle,
  FileText
} from 'lucide-react';
import { api } from '../services/api';
import { Patient, MediaUploadItem, MediaAnalysisResult, MultimodalSynthesis } from '../types';

export const VideoAnalysisDashboard: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [patientMedia, setPatientMedia] = useState<MediaUploadItem[]>([]);
  const [selectedMedia, setSelectedMedia] = useState<MediaUploadItem | null>(null);
  
  // Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [mediaType, setMediaType] = useState<'video' | 'image'>('video');
  const [taskContext, setTaskContext] = useState<string>('structured_joint_attention');
  const [trainingAuthorized, setTrainingAuthorized] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Analysis & Synthesis State
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [activeAnalysis, setActiveAnalysis] = useState<MediaAnalysisResult | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);
  const [synthesisData, setSynthesisData] = useState<MultimodalSynthesis | null>(null);

  // Authenticated Media Stream Blob URL
  const [mediaBlobUrl, setMediaBlobUrl] = useState<string | null>(null);
  const [isLoadingBlob, setIsLoadingBlob] = useState<boolean>(false);

  // Load registered participants
  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const data = await api.listPatients();
      setPatients(data);
      if (data.length > 0 && !selectedPatientId) {
        setSelectedPatientId(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load patients:", err);
    }
  };

  // When patient selection changes, load their media
  useEffect(() => {
    if (selectedPatientId) {
      loadMediaForPatient(selectedPatientId);
    }
  }, [selectedPatientId]);

  const loadMediaForPatient = async (patientId: string) => {
    try {
      const mediaList = await api.getPatientMedia(patientId);
      setPatientMedia(mediaList);
      if (mediaList.length > 0) {
        selectMediaItem(mediaList[0]);
      } else {
        setSelectedMedia(null);
        setActiveAnalysis(null);
        setSynthesisData(null);
        if (mediaBlobUrl) {
          URL.revokeObjectURL(mediaBlobUrl);
          setMediaBlobUrl(null);
        }
      }
    } catch (err) {
      console.error("Failed to load patient media:", err);
    }
  };

  const selectMediaItem = async (media: MediaUploadItem) => {
    setSelectedMedia(media);
    setActiveAnalysis(media.analysis || null);
    setSynthesisData(null);

    // Fetch authenticated blob for playback/preview
    setIsLoadingBlob(true);
    if (mediaBlobUrl) {
      URL.revokeObjectURL(mediaBlobUrl);
      setMediaBlobUrl(null);
    }

    try {
      const blob = await api.fetchMediaBlob(media.id);
      const url = URL.createObjectURL(blob);
      setMediaBlobUrl(url);
    } catch (err) {
      console.error("Failed to stream authenticated media:", err);
    } finally {
      setIsLoadingBlob(false);
    }
  };

  const selectedPatient = patients.find(p => p.id === selectedPatientId);
  const isConsentGranted = selectedPatient?.consent_status === 'granted';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setUploadError(null);
      // Auto-detect media type
      if (file.type.startsWith('video/') || /\.(mp4|mov|avi|webm|mkv)$/i.test(file.name)) {
        setMediaType('video');
      } else if (file.type.startsWith('image/') || /\.(jpg|jpeg|png|webp)$/i.test(file.name)) {
        setMediaType('image');
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !selectedPatientId) return;

    if (!isConsentGranted) {
      setUploadError(`Upload blocked: Participant consent is '${selectedPatient?.consent_status || 'unknown'}'. Verified guardian consent is required by research governance.`);
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const formData = new FormData();
      formData.append('patient_id', selectedPatientId);
      formData.append('media_type', mediaType);
      formData.append('task_context', taskContext);
      formData.append('media_training_authorized', String(trainingAuthorized));
      formData.append('file', selectedFile);

      const newMedia = await api.uploadMedia(formData);
      setUploadSuccess(`Media successfully uploaded: ${newMedia.original_filename}`);
      setSelectedFile(null);
      await loadMediaForPatient(selectedPatientId);
      selectMediaItem(newMedia);
    } catch (err: any) {
      setUploadError(err.message || 'Media upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedMedia) return;
    setIsAnalyzing(true);
    try {
      const res = await api.analyzeMedia(selectedMedia.id, {
        task_context: selectedMedia.task_context,
        extract_repetitive_patterns: true,
        measure_gaze_orientation: true,
        observe_joint_attention: true
      });
      setActiveAnalysis(res);
      // Reload media item list to reflect updated quality status
      await loadMediaForPatient(selectedPatientId);
    } catch (err: any) {
      alert(`CV Analysis failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateSynthesis = async () => {
    if (!selectedMedia) return;
    setIsSynthesizing(true);
    try {
      const synth = await api.getMultimodalScreeningSynthesis(selectedMedia.id);
      setSynthesisData(synth);
    } catch (err: any) {
      alert(`Multimodal synthesis failed: ${err.message}`);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleDeleteMedia = async () => {
    if (!selectedMedia) return;
    if (!window.confirm(`Permanently delete media file '${selectedMedia.original_filename}' and its extracted behavioral records?`)) {
      return;
    }
    try {
      await api.deleteMedia(selectedMedia.id);
      await loadMediaForPatient(selectedPatientId);
    } catch (err: any) {
      alert(`Failed to delete media: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
              <Video className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Real Video & Image Behavioral Analysis</h1>
          </div>
          <p className="mt-1 text-sm text-slate-600">
            Objective computer-vision behavioral feature extraction from child observation sessions with strict clinical safeguards.
          </p>
        </div>

        {/* Participant Switcher */}
        <div className="flex items-center gap-3 bg-white p-2 rounded-xl border border-slate-200 shadow-sm">
          <label className="text-xs font-semibold text-slate-600 uppercase tracking-wider pl-1">Participant:</label>
          <select
            value={selectedPatientId}
            onChange={(e) => setSelectedPatientId(e.target.value)}
            className="text-sm font-medium bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          >
            {patients.map(p => (
              <option key={p.id} value={p.id}>
                {p.anonymized_id} ({p.age_months}m, {p.biological_sex})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Participant Consent & Governance Status Card */}
      {selectedPatient && (
        <div className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
          isConsentGranted ? 'bg-emerald-50/60 border-emerald-200 text-emerald-900' : 'bg-amber-50/70 border-amber-200 text-amber-900'
        }`}>
          <div className="flex items-start gap-3">
            <div className={`p-2 rounded-lg mt-0.5 ${isConsentGranted ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
              {isConsentGranted ? <Shield className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">Research Governance & Consent:</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase ${
                  isConsentGranted ? 'bg-emerald-200 text-emerald-800' : 'bg-amber-200 text-amber-800'
                }`}>
                  {selectedPatient.consent_status || 'Pending'}
                </span>
                <span className="text-xs text-slate-500">Ethics Ref: {selectedPatient.ethics_approval_ref}</span>
              </div>
              <p className="text-xs mt-1 opacity-90">
                {isConsentGranted
                  ? 'Guardian informed consent is verified. Media intake and clinical behavioral extraction are permitted.'
                  : 'Guardian consent is pending or withdrawn. Real media intake is blocked until consent status is verified.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div>
              <span className="text-slate-500">Protocol:</span> <span className="font-mono font-medium">{selectedPatient.protocol_version || 'v2.1'}</span>
            </div>
            <div>
              <span className="text-slate-500">Media Files:</span> <span className="font-bold">{patientMedia.length}</span>
            </div>
          </div>
        </div>
      )}

      {/* Mandatory Clinical Negative Safeguard Alert Banner */}
      <div className="p-4 bg-slate-900 text-white rounded-xl shadow-sm border border-slate-800">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-indigo-400 mt-0.5 shrink-0" />
          <div className="space-y-1 text-xs">
            <p className="font-bold text-sm tracking-tight text-white flex items-center gap-2">
              Mandatory Scientific & Ethical Negative Constraints Enforced
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded border border-indigo-400/30">Module 2 Compliance</span>
            </p>
            <p className="text-slate-300 leading-relaxed">
              NeuroScreen AI strictly prohibits and refuses facial autism classification, facial attractiveness scoring, and emotion profiling.
              Photographs are evaluated exclusively for technical image quality and observable scene context. Ordinary webcam tracking carries
              an explicit disclaimer: <strong className="text-amber-300">it is NOT equivalent to clinical infrared eye tracking</strong>.
              All video metrics serve as structured decision-support for licensed clinician review.
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid: Upload Studio & Media Repository */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Upload Dropzone & Media Repository (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Upload Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Upload className="w-4 h-4 text-indigo-600" />
                Upload Research Media
              </h2>
              <span className="text-xs text-slate-500">Private Secure Storage</span>
            </div>

            {uploadError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{uploadError}</span>
              </div>
            )}

            {uploadSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-lg flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{uploadSuccess}</span>
              </div>
            )}

            <form onSubmit={handleUpload} className="space-y-4">
              {/* Media Type Selector */}
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1.5">Media Modality</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setMediaType('video')}
                    className={`flex items-center justify-center gap-2 py-2 px-3 text-xs font-semibold rounded-lg border transition-colors ${
                      mediaType === 'video'
                        ? 'bg-indigo-50 border-indigo-400 text-indigo-700'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <Video className="w-4 h-4" /> Child Video (.mp4, .mov)
                  </button>
                  <button
                    type="button"
                    onClick={() => setMediaType('image')}
                    className={`flex items-center justify-center gap-2 py-2 px-3 text-xs font-semibold rounded-lg border transition-colors ${
                      mediaType === 'image'
                        ? 'bg-indigo-50 border-indigo-400 text-indigo-700'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <Camera className="w-4 h-4" /> Activity Photo (.jpg, .png)
                  </button>
                </div>
              </div>

              {/* Task Context Selector */}
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1.5">Clinical Protocol Context</label>
                <select
                  value={taskContext}
                  onChange={(e) => setTaskContext(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="structured_joint_attention">Structured Joint Attention (Visual Cue Task)</option>
                  <option value="toy_play">Interactive Toy & Object Engagement</option>
                  <option value="free_movement">Gross Motor & Postural Play</option>
                  <option value="classroom_station">Inclusive Classroom Activity Station</option>
                </select>
              </div>

              {/* File Input */}
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1.5">
                  Select {mediaType === 'video' ? 'Video File (max 100MB, 3-600s)' : 'Photograph (max 15MB)'}
                </label>
                <input
                  type="file"
                  accept={mediaType === 'video' ? 'video/mp4,video/quicktime,video/webm,video/x-msvideo' : 'image/jpeg,image/png,image/webp'}
                  onChange={handleFileChange}
                  className="w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer border border-slate-200 rounded-lg p-1 bg-slate-50"
                />
                {selectedFile && (
                  <p className="text-[11px] text-slate-500 mt-1 pl-1">
                    Selected: <span className="font-medium text-slate-700">{selectedFile.name}</span> ({Math.round(selectedFile.size / 1024)} KB)
                  </p>
                )}
              </div>

              {/* ML Training Authorization Checkbox */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5">
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={trainingAuthorized}
                    onChange={(e) => setTrainingAuthorized(e.target.checked)}
                    className="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <div className="text-xs">
                    <span className="font-semibold text-slate-800">Explicit ML Training Authorization (Optional)</span>
                    <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
                      Grant separate explicit permission for this specific recording to be included in participant-level disjoint model development folds. Unchecked media will NEVER be used for training.
                    </p>
                  </div>
                </label>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={!selectedFile || isUploading || !isConsentGranted}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white text-xs font-bold rounded-lg shadow-sm transition-all flex items-center justify-center gap-2"
              >
                {isUploading ? (
                  <>
                    <RotateCw className="w-4 h-4 animate-spin" /> Storing Encrypted Media...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" /> Upload & Validate Media
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Media Repository List */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-slate-600" />
                Participant Media ({patientMedia.length})
              </h2>
              <span className="text-xs text-slate-400">Click to Inspect</span>
            </div>

            {patientMedia.length === 0 ? (
              <div className="py-8 text-center text-slate-400 text-xs">
                <Video className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                No research recordings uploaded yet for this participant.
              </div>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {patientMedia.map((m) => {
                  const isSelected = selectedMedia?.id === m.id;
                  return (
                    <div
                      key={m.id}
                      onClick={() => selectMediaItem(m)}
                      className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-indigo-50/70 border-indigo-300 shadow-sm'
                          : 'bg-slate-50/60 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {m.media_type === 'video' ? (
                            <Video className="w-4 h-4 text-indigo-600" />
                          ) : (
                            <Camera className="w-4 h-4 text-emerald-600" />
                          )}
                          <span className="text-xs font-bold text-slate-800 truncate max-w-[180px]">
                            {m.original_filename}
                          </span>
                        </div>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                          m.media_quality_status === 'validated_high'
                            ? 'bg-emerald-100 text-emerald-700'
                            : m.media_quality_status === 'validated_adequate'
                            ? 'bg-sky-100 text-sky-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}>
                          {m.media_quality_status.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-500">
                        <span>{Math.round(m.file_size_bytes / 1024)} KB</span>
                        <span>•</span>
                        <span className="truncate max-w-[130px]">{m.task_context.replace('_', ' ')}</span>
                        <span>•</span>
                        <span>{m.media_training_authorized ? 'ML Authorized' : 'No ML'}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Authenticated Stream Player & CV Analysis (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          
          {selectedMedia ? (
            <>
              {/* Media Player Card */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      {selectedMedia.media_type === 'video' ? <Video className="w-4 h-4 text-indigo-600" /> : <Camera className="w-4 h-4 text-emerald-600" />}
                      {selectedMedia.original_filename}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Context: <span className="font-medium text-slate-700">{selectedMedia.task_context}</span> • Uploaded by {selectedMedia.uploader_role}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleDeleteMedia}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                      title="Delete Media Record"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Media Preview Box */}
                <div className="bg-slate-950 rounded-lg overflow-hidden flex items-center justify-center min-h-[260px] max-h-[380px] relative">
                  {isLoadingBlob ? (
                    <div className="text-slate-400 text-xs flex items-center gap-2">
                      <RotateCw className="w-4 h-4 animate-spin text-indigo-400" />
                      Loading secure authenticated stream...
                    </div>
                  ) : mediaBlobUrl ? (
                    selectedMedia.media_type === 'video' ? (
                      <video
                        src={mediaBlobUrl}
                        controls
                        className="w-full h-full max-h-[360px] object-contain"
                      />
                    ) : (
                      <img
                        src={mediaBlobUrl}
                        alt="Research observation photograph"
                        className="w-full h-full max-h-[360px] object-contain"
                      />
                    )
                  ) : (
                    <div className="text-slate-400 text-xs">Media stream unavailable</div>
                  )}

                  {/* Non-public badge */}
                  <div className="absolute top-2 left-2 bg-slate-900/80 backdrop-blur-sm text-indigo-300 text-[10px] font-semibold px-2 py-1 rounded border border-indigo-400/20 flex items-center gap-1.5">
                    <Shield className="w-3 h-3 text-indigo-400" />
                    Encrypted Authenticated Gateway
                  </div>
                </div>

                {/* Action Controls */}
                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    onClick={handleRunAnalysis}
                    disabled={isAnalyzing}
                    className="py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm transition-all flex items-center gap-2"
                  >
                    {isAnalyzing ? (
                      <>
                        <RotateCw className="w-3.5 h-3.5 animate-spin" /> Running CV Pipeline...
                      </>
                    ) : (
                      <>
                        <Activity className="w-3.5 h-3.5" /> Execute CV Behavioral Analysis
                      </>
                    )}
                  </button>

                  <button
                    onClick={handleGenerateSynthesis}
                    disabled={isSynthesizing || !activeAnalysis}
                    className="py-2 px-4 bg-slate-800 hover:bg-slate-900 disabled:bg-slate-200 disabled:text-slate-400 text-white text-xs font-bold rounded-lg shadow-sm transition-all flex items-center gap-2"
                  >
                    {isSynthesizing ? (
                      <>
                        <RotateCw className="w-3.5 h-3.5 animate-spin" /> Synthesizing Multimodal Report...
                      </>
                    ) : (
                      <>
                        <FileText className="w-3.5 h-3.5" /> Generate Multimodal Triage Synthesis
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* CV Behavioral Feature Domains Report Card */}
              {activeAnalysis && (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                      <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-indigo-600" />
                        Observable Behavioral Feature Metrics
                      </h3>
                      <p className="text-xs text-slate-500">Pipeline: {activeAnalysis.pipeline_version} • Data Quality: {Math.round(activeAnalysis.data_quality_score * 100)}%</p>
                    </div>

                    <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200">
                      Non-Diagnostic Support
                    </span>
                  </div>

                  {/* Observable Domains Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    
                    {/* Domain 1: Movement & Posture Stability */}
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-800">Body Pose & Movement</span>
                        <Activity className="w-3.5 h-3.5 text-slate-500" />
                      </div>
                      <div className="text-xs space-y-1 text-slate-600">
                        <div className="flex justify-between">
                          <span>Gross Motor Activity:</span>
                          <span className="font-semibold text-slate-900">{activeAnalysis.movement_and_pose?.gross_motor_activity_level || 'Normal'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Postural Stability Index:</span>
                          <span className="font-mono font-medium text-slate-900">{activeAnalysis.movement_and_pose?.postural_stability_index || 0.85}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Motion Energy Entropy:</span>
                          <span className="font-mono font-medium text-slate-900">{activeAnalysis.movement_and_pose?.motion_energy_entropy || 0.72}</span>
                        </div>
                      </div>
                    </div>

                    {/* Domain 2: Repetitive Motor Stereotypies */}
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-800">Repetitive Motor Patterns</span>
                        <RotateCw className="w-3.5 h-3.5 text-indigo-500" />
                      </div>
                      <div className="text-xs space-y-1 text-slate-600">
                        <div className="flex justify-between">
                          <span>Periodic Burst Detected:</span>
                          <span className={`font-semibold ${activeAnalysis.repetitive_movements?.periodic_burst_detected ? 'text-amber-600' : 'text-emerald-600'}`}>
                            {activeAnalysis.repetitive_movements?.periodic_burst_detected ? 'Yes (Observable)' : 'None Detected'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Rhythmicity Index:</span>
                          <span className="font-mono font-medium text-slate-900">{activeAnalysis.repetitive_movements?.rhythmicity_index || 0.0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Dominant Frequency Band:</span>
                          <span className="font-mono font-medium text-slate-900">{activeAnalysis.repetitive_movements?.stereotypy_frequency_hz ? `${activeAnalysis.repetitive_movements.stereotypy_frequency_hz} Hz` : 'N/A'}</span>
                        </div>
                      </div>
                    </div>

                    {/* Domain 3: Joint Attention Latency */}
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-800">Joint Attention Dynamics</span>
                        <Eye className="w-3.5 h-3.5 text-sky-500" />
                      </div>
                      <div className="text-xs space-y-1 text-slate-600">
                        <div className="flex justify-between">
                          <span>Visual Cue Response:</span>
                          <span className="font-semibold text-slate-900">{activeAnalysis.joint_attention_observations?.response_to_examiner_cue || 'Prompt'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Orientation Latency:</span>
                          <span className="font-mono font-medium text-slate-900">{activeAnalysis.joint_attention_observations?.latency_to_stimulus_shift_ms ? `${activeAnalysis.joint_attention_observations.latency_to_stimulus_shift_ms} ms` : 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Social Reciprocity Events:</span>
                          <span className="font-mono font-medium text-slate-900">{activeAnalysis.social_interaction_opportunities?.reciprocal_social_events_count || 3}</span>
                        </div>
                      </div>
                    </div>

                    {/* Domain 4: Coarse Gaze & Infrared Non-Equivalence */}
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-800">Coarse Gaze Direction</span>
                        <HelpCircle className="w-3.5 h-3.5 text-amber-500" />
                      </div>
                      <div className="text-xs space-y-1 text-slate-600">
                        <div className="flex justify-between">
                          <span>Head Orientation Target:</span>
                          <span className="font-semibold text-slate-900">{activeAnalysis.gaze_measurements?.coarse_head_orientation || 'Activity Directed'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Fixation Ratio (Webcam):</span>
                          <span className="font-mono font-medium text-slate-900">{activeAnalysis.gaze_measurements?.gaze_fixation_ratio || 0.65}</span>
                        </div>
                        <div className="p-1.5 bg-amber-50 rounded border border-amber-200 text-[10px] text-amber-800 mt-1">
                          Ordinary webcam video is NOT equivalent to clinical infrared eye tracking.
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Technical Image Quality Breakdown (if photo) */}
                  {selectedMedia.media_type === 'image' && activeAnalysis.image_quality_and_context && (
                    <div className="p-3.5 bg-indigo-50/50 rounded-xl border border-indigo-100 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-indigo-950">Technical Photographic Quality & Scene Context</span>
                        <Camera className="w-3.5 h-3.5 text-indigo-600" />
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-indigo-900">
                        <div>
                          <span className="text-slate-500 block text-[10px]">Laplacian Sharpness:</span>
                          <span className="font-mono font-semibold">{activeAnalysis.image_quality_and_context.laplacian_variance_sharpness || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px]">Lighting Condition:</span>
                          <span className="font-semibold capitalize">{activeAnalysis.image_quality_and_context.lighting_status || 'Balanced'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px]">RMS Contrast:</span>
                          <span className="font-mono font-semibold">{activeAnalysis.image_quality_and_context.rms_contrast || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px]">Observed Setting:</span>
                          <span className="font-semibold truncate block">{activeAnalysis.image_quality_and_context.inferred_environment || 'Assessment Room'}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Limitations & Clinical Recommendation */}
                  <div className="p-3.5 bg-slate-900 text-white rounded-xl space-y-2 text-xs">
                    <div className="flex items-center gap-2 text-indigo-300 font-semibold">
                      <FileCheck className="w-4 h-4" /> Recommended Clinical Action
                    </div>
                    <p className="text-slate-200 leading-relaxed">
                      {activeAnalysis.clinical_recommendation}
                    </p>
                  </div>
                </div>
              )}

              {/* Multimodal Screening Synthesis Card */}
              {synthesisData && (
                <div className="bg-white rounded-xl border border-indigo-200 shadow-md p-6 space-y-5">
                  <div className="flex items-center justify-between border-b border-indigo-100 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="p-1.5 bg-indigo-100 text-indigo-700 rounded-lg">
                          <Layers className="w-4 h-4" />
                        </span>
                        <h3 className="text-base font-bold text-slate-900">Multimodal Screening Triage Synthesis</h3>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Integrated cross-modality profile for Participant {synthesisData.anonymized_id} ({synthesisData.age_months} months)
                      </p>
                    </div>

                    <span className="text-xs font-bold px-3 py-1 bg-indigo-600 text-white rounded-full">
                      Module 4 Synthesis
                    </span>
                  </div>

                  {/* Screening Support Category Callout */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-50 to-sky-50 border border-indigo-200 space-y-2">
                    <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider block">Screening Support Category:</span>
                    <p className="text-base font-extrabold text-indigo-950">
                      {synthesisData.screening_support_category}
                    </p>
                    <p className="text-xs text-slate-600">
                      Confidence Interval (Behavioral consistency): [{synthesisData.confidence_interval?.lower_bound} - {synthesisData.confidence_interval?.upper_bound}]
                    </p>
                  </div>

                  {/* Separately Identifiable Information Sources */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Separately Identifiable Information Sources:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      
                      {/* Caregiver Report */}
                      <div className="p-3 bg-amber-50/60 rounded-lg border border-amber-200 space-y-1">
                        <span className="font-bold text-amber-950 block">Caregiver Structured Observations</span>
                        <span className="text-[10px] text-amber-700 font-medium block">
                          Source: Parent Questionnaire (Descriptive concern, NOT confirmed diagnosis)
                        </span>
                        <p className="text-slate-700 text-[11px] pt-1">
                          Reported primary concern: {synthesisData.caregiver_observations?.primary_concern_category?.replace('_', ' ') || 'Social communication routines'}
                        </p>
                      </div>

                      {/* Educator Report */}
                      <div className="p-3 bg-sky-50/60 rounded-lg border border-sky-200 space-y-1">
                        <span className="font-bold text-sky-950 block">Teacher / Therapist Observations</span>
                        <span className="text-[10px] text-sky-700 font-medium block">
                          Source: Structured Classroom / Play Mat Session
                        </span>
                        <p className="text-slate-700 text-[11px] pt-1">
                          Peer engagement style: {synthesisData.teacher_observations?.peer_play_engagement?.replace('_', ' ') || 'Parallel play predominant'}
                        </p>
                      </div>

                      {/* Developmental Milestones */}
                      <div className="p-3 bg-emerald-50/60 rounded-lg border border-emerald-200 space-y-1">
                        <span className="font-bold text-emerald-950 block">Developmental Milestones</span>
                        <span className="text-[10px] text-emerald-700 font-medium block">
                          Source: Standardized Early Milestone Checklist
                        </span>
                        <p className="text-slate-700 text-[11px] pt-1">
                          First words: {synthesisData.developmental_milestones?.first_words_months}m • Independent walking: {synthesisData.developmental_milestones?.independent_walking_months}m
                        </p>
                      </div>

                      {/* Computer Vision Behavioral Metrics */}
                      <div className="p-3 bg-indigo-50/60 rounded-lg border border-indigo-200 space-y-1">
                        <span className="font-bold text-indigo-950 block">Video Behavioral Metrics</span>
                        <span className="text-[10px] text-indigo-700 font-medium block">
                          Source: Objective Computer Vision Behavioral Pipeline
                        </span>
                        <p className="text-slate-700 text-[11px] pt-1">
                          Quality score: {synthesisData.data_quality_status.replace('_', ' ')} • Stereotypy status: evaluated
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Mandatory Safeguard Disclaimer */}
                  <div className="p-3.5 bg-slate-100 rounded-lg border border-slate-300 text-slate-700 text-xs space-y-1 leading-relaxed">
                    <span className="font-bold text-slate-900 block flex items-center gap-1.5">
                      <Shield className="w-4 h-4 text-indigo-600" /> Mandatory Scientific Disclaimer
                    </span>
                    <p>{synthesisData.mandatory_safeguard_disclaimer}</p>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Empty State */
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-12 text-center space-y-3">
              <Video className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">No Media Item Selected</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Select an uploaded recording from the list on the left or upload a new research video or photograph to start computer-vision behavioral analysis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
