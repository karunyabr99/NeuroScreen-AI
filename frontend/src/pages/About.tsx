import React from 'react';
import {
  Brain,
  FileText,
  HeartHandshake,
  CheckCircle2,
  AlertTriangle,
  Video,
  Mic,
  Award,
  Microscope,
  ArrowRight
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';

export const About: React.FC<{ onOpenResearchML?: () => void }> = ({ onOpenResearchML }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-10 pb-8">
      {/* Header */}
      <div className="text-center space-y-3 pt-2">
        <div className="inline-flex items-center gap-2 bg-teal-50 text-teal-700 border border-teal-200 px-3 py-1 rounded-full text-xs font-semibold">
          <Brain className="w-4 h-4 text-teal-600" />
          <span>Research Foundations & Ethical Framework</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          About NeuroScreen AI
        </h1>
        <p className="text-base text-slate-600 max-w-2xl mx-auto leading-relaxed">
          An explainable, multimodal screening-support system combining developmental questionnaires, vocal prosody analysis, and live behavioral video observations.
        </p>
      </div>

      {/* Core Mission */}
      <Card className="border-teal-200/80 bg-gradient-to-r from-teal-50/60 to-white">
        <CardContent className="p-6 sm:p-8 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center">
              <HeartHandshake className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Our Research Mission</h2>
              <p className="text-xs text-slate-500">Supporting timely developmental intervention</p>
            </div>
          </div>
          <p className="text-sm text-slate-700 leading-relaxed">
            Early identification of Autism Spectrum Disorder (ASD) is one of the most critical factors in improving developmental outcomes. Traditional clinical diagnostic waiting times often exceed 12 to 18 months. NeuroScreen AI was created to provide accessible, objective, and transparent <strong>screening support</strong> to help parents, educators, and early intervention specialists recognize developmental differences sooner and seek timely professional guidance.
          </p>
        </CardContent>
      </Card>

      {/* Multimodal Modalities */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Multimodal Screening Approach</h2>
        <p className="text-sm text-slate-600">
          Rather than relying on a single questionnaire or isolated sensor, NeuroScreen AI synthesizes three independent streams of developmental information:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          {/* Modality 1 */}
          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center mb-2">
                <FileText className="w-5 h-5" />
              </div>
              <CardTitle className="text-base font-bold text-slate-900">
                1. Caregiver Observations
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-slate-600 space-y-2">
              <p>
                Structured multi-informant reporting covering social smiling, pointing to show interest, response to name, pretend play, and sensory routines.
              </p>
              <div className="text-[11px] font-medium text-teal-800 bg-teal-50/80 p-2 rounded">
                Validated psychometric indicators based on AQ-10 and M-CHAT-R/F item modeling.
              </div>
            </CardContent>
          </Card>

          {/* Modality 2 */}
          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center mb-2">
                <Video className="w-5 h-5" />
              </div>
              <CardTitle className="text-base font-bold text-slate-900">
                2. Live Video Behavior
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-slate-600 space-y-2">
              <p>
                Objective computer vision extracting observable body movement dynamics, repetitive rhythmicity, and joint-attention response latency during natural interactions.
              </p>
              <div className="text-[11px] font-medium text-sky-800 bg-sky-50/80 p-2 rounded">
                Movement stability and interaction opportunities without facial categorization.
              </div>
            </CardContent>
          </Card>

          {/* Modality 3 */}
          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-2">
                <Mic className="w-5 h-5" />
              </div>
              <CardTitle className="text-base font-bold text-slate-900">
                3. Vocal Prosody Biomarkers
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-slate-600 space-y-2">
              <p>
                Acoustic analysis of speech and vocalization patterns, including pitch variability ($F_0$), vocal jitter, shimmer, and hesitation pause-to-speech ratio.
              </p>
              <div className="text-[11px] font-medium text-indigo-800 bg-indigo-50/80 p-2 rounded">
                Prosodic contours reflecting expressive speech cadence and vocal modulation.
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Scientific & Patent References */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Research & Patent Foundations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-teal-600" />
              <h3 className="font-semibold text-sm text-slate-900">Research Paper 1: Psychometrics</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Item response modeling of digitized developmental screening scales, evaluating communicative gesture frequency, social interest, and reaction latencies.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-sky-600" />
              <h3 className="font-semibold text-sm text-slate-900">Research Paper 2: Acoustic Prosody</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Vocal prosody profiling examining acoustic pitch modulation, formant dispersion, and speech-pause balance as non-invasive developmental markers.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-indigo-600" />
              <h3 className="font-semibold text-sm text-slate-900">Patent Reference 1: Oculomotor Tracking</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Measurement of social region-of-interest dwell time, joint attention saccade latency, and scanpath entropy during shared engagement tasks.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-purple-600" />
              <h3 className="font-semibold text-sm text-slate-900">Patent Reference 2: Explainable Fusion</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Multi-tier ensemble machine learning with transparent feature attribution (SHAP and LIME), preventing black-box decisions in clinical contexts.
            </p>
          </div>
        </div>
      </div>

      {/* Research Papers Implementation */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Benchmark Research Foundations</h2>
            <p className="text-xs text-slate-500">Methodological frameworks implemented from leading peer-reviewed literature</p>
          </div>
          {onOpenResearchML && (
            <button
              onClick={onOpenResearchML}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition-colors shadow-xs"
            >
              <Microscope className="w-3.5 h-3.5" />
              <span>Open Research ML Engine</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Paper 1 */}
          <div className="p-5 rounded-2xl border border-teal-200 bg-teal-50/50 space-y-2.5">
            <div className="flex items-center gap-2">
              <span className="p-1.5 bg-teal-100 text-teal-800 rounded-lg text-xs font-bold">Paper 1 (2024)</span>
              <h3 className="font-bold text-sm text-slate-900">Well-Baby Electronic Records Model</h3>
            </div>
            <p className="text-xs text-slate-600 italic">
              &quot;A Prediction Model of Autism Spectrum Diagnosis from Well-Baby Electronic Data Using Machine Learning&quot;
            </p>
            <p className="text-xs text-slate-700 leading-relaxed">
              Implemented with <strong>CatBoost gradient boosting</strong>, 3-fold stratified cross-validation, <strong>Youden J index</strong> cutoff optimization ($T^* = 0.507$), and genuine <strong>SHAP TreeExplainer</strong> feature importance.
            </p>
          </div>

          {/* Paper 2 */}
          <div className="p-5 rounded-2xl border border-sky-200 bg-sky-50/50 space-y-2.5">
            <div className="flex items-center gap-2">
              <span className="p-1.5 bg-sky-100 text-sky-800 rounded-lg text-xs font-bold">Paper 2 (2022)</span>
              <h3 className="font-bold text-sm text-slate-900">Medical Claims Machine Learning</h3>
            </div>
            <p className="text-xs text-slate-600 italic">
              &quot;Early Detection of Autism Spectrum Disorder in Young Children with Machine Learning Using Medical Claims Data&quot;
            </p>
            <p className="text-xs text-slate-700 leading-relaxed">
              Implemented with <strong>Random Forest</strong> and <strong>LASSO Logistic Regression</strong> with L1 sparse feature selection, standardized numerical pipelines, and AUPRC / ROC-AUC benchmarks.
            </p>
          </div>
        </div>
      </div>

      {/* Ethical Safeguards */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Ethical Safeguards & Privacy</h2>
        <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-teal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Strict Participant De-Identification</h4>
              <p className="text-xs text-slate-600 mt-0.5">
                Participants are assigned random anonymous identifiers (e.g. `NS-XXXX`). No personal names, home addresses, or personal contact numbers are stored in training sets.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-teal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Informed Guardian Consent Gating</h4>
              <p className="text-xs text-slate-600 mt-0.5">
                Assessment records require verified caregiver informed consent. If consent is ever withdrawn, associated media is immediately quarantined and deleted.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-teal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-slate-900">No Facial Autism Categorization</h4>
              <p className="text-xs text-slate-600 mt-0.5">
                NeuroScreen AI strictly rejects facial emotion detection, attractiveness scoring, and facial appearance classification. Computer vision is restricted strictly to objective movement dynamics.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Non-Diagnostic Disclaimer */}
      <div className="bg-amber-50/80 border border-amber-200 rounded-2xl p-6 flex items-start gap-4 text-amber-900">
        <div className="p-2.5 bg-amber-100 rounded-xl text-amber-800 flex-shrink-0">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1.5 text-xs sm:text-sm">
          <h4 className="font-bold text-amber-950">Important Clinical Boundary</h4>
          <p className="text-amber-800 leading-relaxed">
            NeuroScreen AI is an academic screening-support prototype designed for research and early developmental observation. <strong>It is not a diagnostic tool</strong> and does not confirm or rule out Autism Spectrum Disorder or any neurodevelopmental condition. Always consult a licensed pediatrician, pediatric neurologist, or licensed psychologist for diagnostic evaluations.
          </p>
        </div>
      </div>
    </div>
  );
};
