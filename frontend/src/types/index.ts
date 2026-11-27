export interface Patient {
  id: string;
  anonymized_id: string;
  age_months: number;
  biological_sex: string;
  referral_source: string;
  clinical_notes?: string;
  
  // Phase 4 Research Governance
  is_synthetic?: boolean;
  consent_status?: 'granted' | 'pending' | 'withdrawn' | 'declined';
  assent_status?: 'granted' | 'declined' | 'not_applicable';
  guardian_relationship?: string;
  ethics_approval_ref?: string;
  protocol_version?: string;
  consent_date?: string;
  consent_withdrawn_at?: string;
  assessor_id?: string;

  created_at: string;
  updated_at: string;
}

export interface BehavioralInput {
  social_smile_reciprocity: number;
  name_call_orientation: number;
  pointing_proto_declarative: number;
  pretend_play_engagement: number;
  repetitive_motor_mannerisms: number;
  monotropic_focus_intensity: number;
  gaze_alternation_dyadic: number;
  sensory_hypersensitivity: number;
  peer_social_interest: number;
  gestural_communication: number;
  response_latency_mean_sec: number;
}

export interface VisualGazeInput {
  fixation_count: number;
  mean_fixation_duration_ms: number;
  social_roi_dwell_percentage: number;
  joint_attention_latency_ms: number;
  saccade_mean_amplitude_deg: number;
  atypical_scanpath_entropy: number;
}

export interface AcousticProsodyInput {
  fundamental_freq_f0_mean_hz: number;
  f0_pitch_variability_stdev_hz: number;
  vocal_jitter_percent: number;
  vocal_shimmer_db: number;
  pause_to_speech_ratio: number;
  formant_dispersion_hz: number;
  speech_rate_syllables_sec: number;
}

export interface ScreeningSession {
  id: string;
  patient_id: string;
  status: string;
  protocol_version: string;
  composite_risk_score?: number | null;
  risk_tier: string;
  confidence_interval?: { lower: number; upper: number } | null;
  model_version: string;
  is_calibrated: boolean;
  modalities_included: string[];
  created_at: string;
  completed_at?: string;
}

export interface ModalityFeature {
  id: string;
  modality_type: string;
  raw_metrics: Record<string, any>;
  extracted_features: Record<string, any>;
  quality_score: number;
  quality_status?: string;
  is_available?: boolean;
  sensor_metadata?: Record<string, any>;
  created_at: string;
}

export interface FeatureContribution {
  feature_name: string;
  display_name: string;
  modality: 'behavioral' | 'visual_gaze' | 'acoustic_prosody';
  feature_value: number;
  importance_value: number;
  direction: 'risk_increasing' | 'risk_decreasing' | 'neutral';
  clinical_note: string;
}

export interface ExplainabilityRecord {
  id: string;
  session_id: string;
  method: 'SHAP' | 'LIME';
  status?: string;
  base_value: number;
  prediction_value: number;
  is_calibrated: boolean;
  calibration_status_notice: string;
  feature_importances: FeatureContribution[];
  summary_narrative: string;
  modality_breakdown: {
    behavioral: number;
    visual_gaze: number;
    acoustic_prosody: number;
  };
  created_at: string;
}

export interface ModelStatus {
  model_name: string;
  model_key: string;
  model_family: string;
  is_trained: boolean;
  is_calibrated: boolean;
  checkpoint_found: boolean;
  weights_path?: string | null;
  input_feature_dim: number;
  architecture_description: string;
  supported_explainers: string[];
  status_message: string;
}

export interface ScreeningDetail {
  session: ScreeningSession;
  features: ModalityFeature[];
  explanations: ExplainabilityRecord[];
  model_status: ModelStatus;
  clinical_disclaimer: string;
}

export interface FeatureDefinition {
  id: string;
  name: string;
  modality: string;
  typical_range: [number, number];
  mean_norm: number;
  std_norm: number;
  clinical_note: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: 'Administrator' | 'Researcher' | 'Assessor';
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  role: 'Administrator' | 'Researcher' | 'Assessor';
  user_id: string;
  email: string;
  full_name: string;
}

export interface ResearchAssessment {
  id: string;
  patient_id: string;
  form_type: 'caregiver' | 'teacher' | 'professional' | 'multimodal_comprehensive';
  assessor_id: string;
  assessor_role: string;
  assessment_date: string;
  protocol_version: string;
  ethics_approval_ref: string;
  is_synthetic: boolean;
  data_quality_status: 'complete' | 'partial' | 'flagged';
  quality_score: number;
  
  developmental_history: Record<string, any>;
  communication_milestones: Record<string, any>;
  social_interaction_observations: Record<string, any>;
  behavioral_characteristics: Record<string, any>;
  repetitive_behaviors: Record<string, any>;
  caregiver_concerns: Record<string, any>;
  medical_family_history: Record<string, any>;
  multimodal_measurements: Record<string, any>;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface DuplicateRecord {
  anonymized_id: string;
  age_months: number;
  biological_sex: string;
  duplicate_type: string;
  matching_ids: string[];
}

export interface DatasetOverview {
  total_participants: number;
  real_participants: number;
  synthetic_participants: number;
  consented_real_participants: number;
  withdrawn_participants: number;
  
  total_sessions: number;
  real_sessions: number;
  synthetic_sessions: number;
  total_research_assessments: number;
  
  age_distribution: Record<string, number>;
  modality_distribution: Record<string, number>;
  missing_value_percentages: Record<string, number>;
  
  duplicate_count: number;
  duplicates: DuplicateRecord[];
  
  label_distribution: Record<string, number>;
  data_quality_warnings: string[];
  dataset_version: string;
}

export interface MediaAnalysisResult {
  id: string;
  media_id: string;
  pipeline_version: string;
  analysis_status: string;
  data_quality_score: number;
  movement_and_pose: Record<string, any>;
  gesture_and_actions: Record<string, any>;
  gaze_measurements: Record<string, any>;
  joint_attention_observations: Record<string, any>;
  repetitive_movements: Record<string, any>;
  social_interaction_opportunities: Record<string, any>;
  image_quality_and_context: Record<string, any>;
  ethical_safeguards: Record<string, any>;
  limitations_summary?: string;
  clinical_recommendation: string;
  created_at: string;
}

export interface MediaUploadItem {
  id: string;
  patient_id: string;
  session_id?: string | null;
  media_type: 'video' | 'image';
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  duration_seconds?: number | null;
  resolution_width?: number | null;
  resolution_height?: number | null;
  fps?: number | null;
  task_context: string;
  media_quality_status: string;
  media_training_authorized: boolean;
  uploader_id: string;
  uploader_role: string;
  is_synthetic: boolean;
  created_at: string;
  analysis?: MediaAnalysisResult | null;
}

export interface MultimodalSynthesis {
  patient_id: string;
  anonymized_id: string;
  age_months: number;
  screening_session_id?: string | null;
  media_id: string;
  video_observable_features: Record<string, any>;
  developmental_milestones: Record<string, any>;
  caregiver_observations: Record<string, any>;
  teacher_observations: Record<string, any>;
  professional_clinical_findings: Record<string, any>;
  data_quality_status: string;
  screening_support_category: string;
  model_availability: string;
  confidence_interval?: { lower_bound: number; upper_bound: number } | null;
  limitations: string[];
  mandatory_safeguard_disclaimer: string;
  clinical_recommendation: string;
}

export interface SimulationInput {
  participant_id?: string;
  scenario_name?: string;
  age_months: number;
  communication_development: number;
  social_interaction: number;
  response_to_name: number;
  eye_contact_observations: number;
  gesture_usage: number;
  repetitive_behaviours: number;
  play_patterns: number;
  developmental_milestones: number;
  caregiver_observations: number;
  is_incomplete?: boolean;
  notes?: string;
}

export interface ContributingFeature {
  feature_name: string;
  display_name: string;
  modality: string;
  feature_value: number;
  importance_value: number;
  direction: 'risk_increasing' | 'risk_decreasing' | 'neutral';
  clinical_note: string;
}

export interface SimulationResultResponse {
  session_id: string;
  patient_id: string;
  participant_id: string;
  scenario_name: string;
  age_months: number;
  predicted_probability: number;
  risk_tier: string;
  confidence_interval: { lower: number; upper: number };
  model_name: string;
  model_architecture: string;
  is_calibrated: boolean;
  contributing_features: ContributingFeature[];
  positive_contributions: ContributingFeature[];
  negative_contributions: ContributingFeature[];
  summary_narrative: string;
  is_synthetic_demonstration: boolean;
  clinical_disclaimer: string;
  created_at: string;
}

export interface ScenarioDefinition {
  id: string;
  name: string;
  description: string;
  clinical_focus: string;
  inputs: SimulationInput;
}

export interface DatasetColumnInfo {
  name: string;
  inferred_type: string;
  missing_count: number;
  missing_percentage: number;
  unique_values_count: number;
  sample_values: string[];
  is_target: boolean;
  is_id: boolean;
  is_potential_leakage: boolean;
}

export interface DatasetPreviewData {
  row_count: number;
  column_count: number;
  identified_target: string;
  id_columns: string[];
  leakage_columns: string[];
  duplicate_rows_count: number;
  total_missing_cells: number;
  overall_missing_rate: number;
  columns: DatasetColumnInfo[];
  class_balance: {
    counts: Record<string, number>;
    ratios: Record<string, number>;
    total_valid_target_rows: number;
    imbalance_ratio: number;
  };
  preview: Record<string, any>[];
  target_leakage_audit?: {
    total_columns_evaluated: number;
    columns_dropped_count: number;
    dropped_columns: string[];
    retained_columns: string[];
    audit_records: Array<{
      column: string;
      issue: string;
      action: string;
      explanation: string;
    }>;
  };
}

export interface ModelComparisonData {
  timestamp: string;
  dataset_name: string;
  dataset_rows: number;
  asd_positive: number;
  asd_negative: number;
  train_samples: number;
  test_samples: number;
  catboost: {
    model_name: string;
    model_family: string;
    hyperparameters: Record<string, any>;
    training_duration_seconds: number;
    youden_threshold: number;
    cv_evaluation: any;
    test_evaluation_default_threshold: any;
    test_evaluation_youden_threshold: any;
    shap_summary: {
      base_value: number;
      top_features: Array<{ feature: string; mean_abs_shap: number }>;
    };
  };
  random_forest: {
    model_name: string;
    model_family: string;
    hyperparameters: Record<string, any>;
    training_duration_seconds: number;
    cv_evaluation: any;
    test_evaluation: any;
    feature_importance: Array<{ feature: string; importance: number }>;
  };
  lasso_logistic: {
    model_name: string;
    model_family: string;
    hyperparameters: Record<string, any>;
    training_duration_seconds: number;
    cv_evaluation: any;
    test_evaluation: any;
    lasso_selected_features_count: number;
    total_initial_features: number;
    lasso_selected_features: Array<{
      feature: string;
      coefficient: number;
      abs_weight: number;
      direction: string;
    }>;
    top_coefficients: any[];
  };
  target_leakage_audit?: any;
  paper_feature_comparison?: any;
}

export interface ResearchPredictionResponse {
  screening_status: string;
  predicted_probability: number | null;
  is_calibrated: boolean;
  risk_tier: string;
  risk_category_label: string;
  confidence_interval: { lower: number; upper: number };
  threshold_applied: number | null;
  threshold_label: string | null;
  status_message: string;
  model_used: string;
  model_title?: string;
  explanation: {
    method: string;
    base_value?: number;
    prediction_value?: number | null;
    status: string;
    feature_importances: Array<{
      feature: string;
      contribution: number;
      abs_contribution: number;
      direction: string;
    }>;
    positive_risk_drivers?: Array<{
      feature: string;
      contribution: number;
      direction: string;
    }>;
    protective_factors?: Array<{
      feature: string;
      contribution: number;
      direction: string;
    }>;
    summary_narrative: string;
  };
  raw_inputs?: Record<string, any>;
}

