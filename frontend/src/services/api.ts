import {
  Patient,
  ScreeningSession,
  ScreeningDetail,
  ModelStatus,
  FeatureDefinition,
  BehavioralInput,
  VisualGazeInput,
  AcousticProsodyInput,
  AuthToken,
  UserProfile,
  ResearchAssessment,
  DatasetOverview,
  MediaUploadItem,
  MediaAnalysisResult,
  MultimodalSynthesis,
  SimulationInput,
  SimulationResultResponse,
  ScenarioDefinition
} from '../types';

const API_BASE = `${(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')}/api/v1`;
const TOKEN_KEY = 'neuroscreen_auth_token';

export const DEFAULT_PERSONAS = {
  Assessor: {
    email: 'assessor@neuroscreen.ai',
    password: 'Assessor@12345',
    role: 'Assessor' as const,
    label: 'Assessor (Clinical Triage Specialist)'
  },
  Administrator: {
    email: 'admin@neuroscreen.ai',
    password: 'Admin@12345',
    role: 'Administrator' as const,
    label: 'Administrator (System & Data Governance)'
  },
  Researcher: {
    email: 'researcher@neuroscreen.ai',
    password: 'Researcher@12345',
    role: 'Researcher' as const,
    label: 'Researcher (Read-Only Analytic Access)'
  }
};

function getStoredAuth(): AuthToken | null {
  try {
    const raw = localStorage.getItem(TOKEN_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // Ignore JSON errors in non-browser or corrupted storage
  }
  return null;
}

function setStoredAuth(auth: AuthToken | null): void {
  try {
    if (auth) {
      localStorage.setItem(TOKEN_KEY, JSON.stringify(auth));
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // Ignore storage errors
  }
}

async function getAuthHeader(): Promise<Record<string, string>> {
  let auth = getStoredAuth();
  if (!auth?.access_token) {
    try {
      // Auto-authenticate as Assessor for seamless out-of-the-box operation
      auth = await api.login(DEFAULT_PERSONAS.Assessor.email, DEFAULT_PERSONAS.Assessor.password);
    } catch {
      // Fallback if backend not reachable yet
    }
  }
  return auth?.access_token ? { Authorization: `Bearer ${auth.access_token}` } : {};
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      setStoredAuth(null);
    }
    const errorText = await response.text();
    let message = `API Error ${response.status}: ${response.statusText}`;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed.detail) message = parsed.detail;
    } catch {
      if (errorText) message = errorText;
    }
    throw new Error(message);
  }
  return response.json();
}

export const api = {
  // Authentication & Session
  getStoredUser(): AuthToken | null {
    return getStoredAuth();
  },

  async login(email: string, password: string): Promise<AuthToken> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data: AuthToken = await handleResponse(res);
    setStoredAuth(data);
    return data;
  },

  logout(): void {
    setStoredAuth(null);
  },

  async switchPersona(role: 'Assessor' | 'Administrator' | 'Researcher'): Promise<AuthToken> {
    const target = DEFAULT_PERSONAS[role];
    return this.login(target.email, target.password);
  },

  async getMe(): Promise<UserProfile> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  // Health
  async getHealth(): Promise<{ status: string; database: any; ml_engine: any; clinical_disclaimer: string }> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse(res);
  },

  // Patients
  async listPatients(): Promise<Patient[]> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/patients/`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async getPatient(id: string): Promise<Patient> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/patients/${id}`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async createPatient(payload: {
    age_months: number;
    biological_sex: string;
    referral_source: string;
    clinical_notes?: string;
    anonymized_id?: string;
    consent_status?: string;
  }): Promise<Patient> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/patients/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async deletePatient(id: string): Promise<{ success: boolean; message: string; patient_id: string }> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/patients/${id}`, {
      method: 'DELETE',
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  // Screenings
  async listScreenings(): Promise<ScreeningSession[]> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/screenings/`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async getScreeningDetail(sessionId: string): Promise<ScreeningDetail> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/screenings/${sessionId}`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async submitScreening(payload: {
    patient_id: string;
    preferred_model?: string;
    behavioral?: BehavioralInput;
    visual_gaze?: VisualGazeInput;
    acoustic_prosody?: AcousticProsodyInput;
  }): Promise<ScreeningDetail> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/screenings/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  // Multimodal Catalog
  async getFeatureCatalog(): Promise<FeatureDefinition[]> {
    const res = await fetch(`${API_BASE}/multimodal/features`);
    return handleResponse(res);
  },

  // Models
  async listModels(): Promise<ModelStatus[]> {
    const res = await fetch(`${API_BASE}/explainability/models`);
    return handleResponse(res);
  },

  // Research Governance & Dataset Management (Phase 4)
  async updateConsent(patientId: string, payload: {
    consent_status: string;
    assent_status?: string;
    guardian_relationship?: string;
    ethics_approval_ref?: string;
    protocol_version?: string;
    notes?: string;
  }): Promise<Patient> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/research/consent/${patientId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async withdrawConsent(patientId: string, reason?: string): Promise<Patient> {
    const authH = await getAuthHeader();
    const url = reason
      ? `${API_BASE}/research/consent/${patientId}/withdraw?reason=${encodeURIComponent(reason)}`
      : `${API_BASE}/research/consent/${patientId}/withdraw`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async createResearchAssessment(payload: {
    patient_id: string;
    form_type: 'caregiver' | 'teacher' | 'professional' | 'multimodal_comprehensive';
    assessor_role: string;
    developmental_history?: Record<string, any>;
    communication_milestones?: Record<string, any>;
    social_interaction_observations?: Record<string, any>;
    behavioral_characteristics?: Record<string, any>;
    repetitive_behaviors?: Record<string, any>;
    caregiver_concerns?: Record<string, any>;
    medical_family_history?: Record<string, any>;
    multimodal_measurements?: Record<string, any>;
    notes?: string;
    is_synthetic?: boolean;
  }): Promise<ResearchAssessment> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/research/assessments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async listPatientAssessments(patientId: string): Promise<ResearchAssessment[]> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/research/assessments/patient/${patientId}`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async getDatasetOverview(): Promise<DatasetOverview> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/research/dataset/overview`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async exportDatasetCsv(exportType: 'real' | 'synthetic' | 'all' = 'real'): Promise<Blob> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/research/dataset/export-csv?export_type=${exportType}`, {
      headers: { ...authH },
    });
    if (!res.ok) {
      throw new Error(`Export failed: ${res.statusText}`);
    }
    return res.blob();
  },

  async generateBenchmarkCohort(sampleSize: number = 60, targetPrevalence: number = 0.5): Promise<{
    status: string;
    message: string;
    synthetic_count: number;
    synthetic_sample_ids: string[];
  }> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/research/dataset/generate-benchmark`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify({ sample_size: sampleSize, target_asd_prevalence: targetPrevalence }),
    });
    return handleResponse(res);
  },

  async downloadReportPdf(sessionId: string): Promise<Blob> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/research/reports/${sessionId}/pdf`, {
      headers: { ...authH },
    });
    if (!res.ok) {
      throw new Error(`PDF generation failed: ${res.statusText}`);
    }
    return res.blob();
  },

  async evaluateTrainingEligibility(): Promise<{
    status: string;
    dataset_version: string;
    eligibility_report: any;
  }> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/research/train/eligibility`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async runTrainingPipeline(trainOnBenchmark: boolean = false, exportCheckpoints: boolean = false): Promise<any> {
    const authH = await getAuthHeader();
    const res = await fetch(
      `${API_BASE}/research/train/run?train_on_benchmark=${trainOnBenchmark}&export_checkpoints=${exportCheckpoints}`,
      {
        method: 'POST',
        headers: { ...authH },
      }
    );
    return handleResponse(res);
  },

  // Real Video and Image Analysis Module (Phase 5)
  async uploadMedia(formData: FormData): Promise<MediaUploadItem> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/media/upload`, {
      method: 'POST',
      headers: {
        ...authH,
      },
      body: formData,
    });
    return handleResponse(res);
  },

  async getPatientMedia(patientId: string): Promise<MediaUploadItem[]> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/media/patient/${patientId}`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async getMediaDetails(mediaId: string): Promise<MediaUploadItem> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/media/${mediaId}`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async fetchMediaBlob(mediaId: string): Promise<Blob> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/media/${mediaId}/stream`, {
      headers: { ...authH },
    });
    if (!res.ok) {
      throw new Error(`Media stream failed: ${res.statusText}`);
    }
    return res.blob();
  },

  async analyzeMedia(
    mediaId: string,
    options: {
      task_context?: string;
      extract_repetitive_patterns?: boolean;
      measure_gaze_orientation?: boolean;
      observe_joint_attention?: boolean;
    } = {}
  ): Promise<MediaAnalysisResult> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/media/${mediaId}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify({
        task_context: options.task_context || 'structured_joint_attention',
        extract_repetitive_patterns: options.extract_repetitive_patterns ?? true,
        measure_gaze_orientation: options.measure_gaze_orientation ?? true,
        observe_joint_attention: options.observe_joint_attention ?? true,
      }),
    });
    return handleResponse(res);
  },

  async getMultimodalScreeningSynthesis(mediaId: string): Promise<MultimodalSynthesis> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/media/${mediaId}/screening-synthesis`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async deleteMedia(mediaId: string): Promise<{ status: string; message: string }> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/media/${mediaId}`, {
      method: 'DELETE',
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  // Stacking Ensemble Simulation Engine
  async getSimulationScenarios(): Promise<ScenarioDefinition[]> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/simulation/scenarios`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async runSimulation(inputs: SimulationInput): Promise<SimulationResultResponse> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/simulation/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify(inputs),
    });
    return handleResponse(res);
  },

  async getSimulationHistory(limit: number = 25): Promise<any[]> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/simulation/history?limit=${limit}`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  // Research Machine Learning Engine (Paper 1 & Paper 2)
  async uploadResearchDataset(file: File): Promise<any> {
    const authH = await getAuthHeader();
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/ml/upload-dataset`, {
      method: 'POST',
      headers: {
        ...authH,
      },
      body: formData,
    });
    return handleResponse(res);
  },

  async listResearchDatasets(): Promise<{ datasets: Array<any>; default_dataset: string }> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/ml/datasets`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async previewResearchDataset(datasetName?: string): Promise<any> {
    const authH = await getAuthHeader();
    const url = datasetName
      ? `${API_BASE}/ml/preview-dataset?dataset_name=${encodeURIComponent(datasetName)}`
      : `${API_BASE}/ml/preview-dataset`;
    const res = await fetch(url, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async triggerResearchTraining(payload?: any): Promise<any> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/ml/train`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify(payload || {}),
    });
    return handleResponse(res);
  },

  async getResearchTrainingStatus(): Promise<any> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/ml/training-status`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async getResearchModelComparison(): Promise<any> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/ml/models/comparison`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async getResearchModelExplainability(modelName: string): Promise<any> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/ml/models/${modelName}/explainability`, {
      headers: { ...authH },
    });
    return handleResponse(res);
  },

  async predictResearchChild(payload: any): Promise<any> {
    const authH = await getAuthHeader();
    const res = await fetch(`${API_BASE}/ml/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authH,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },
};
