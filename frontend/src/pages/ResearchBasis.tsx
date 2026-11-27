import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { FeatureDefinition } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import {
  Activity,
  Eye,
  Mic,
  Layers,
  Scale,
  BookOpen
} from 'lucide-react';

export const ResearchBasis: React.FC = () => {
  const [features, setFeatures] = useState<FeatureDefinition[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadCatalog() {
      try {
        const cat = await api.getFeatureCatalog();
        setFeatures(cat);
      } catch (err) {
        console.error("Failed to load feature catalog:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadCatalog();
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 bg-neuro-100 text-neuro-700 px-3 py-1 rounded-full text-xs font-semibold mb-2">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Scientific & Methodological Foundations</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
          Research Papers & Patent Reference Architecture
        </h1>
        <p className="mt-2 text-sm text-slate-600 leading-relaxed max-w-3xl">
          NeuroScreen AI unifies methodologies from two peer-reviewed clinical research papers and two patented multimodal decision-support frameworks to ensure explainable, objective autism screening support.
        </p>
      </div>

      {/* 4 Cards: The 2 Papers + 2 Patents */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Paper 1 */}
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between mb-1">
              <Badge variant="info">Research Paper 1</Badge>
              <span className="text-[10px] text-slate-400 font-mono">Modality 1: Psychometrics</span>
            </div>
            <CardTitle className="text-base text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              Behavioral & Psychometric Feature Modelling
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-slate-600 leading-relaxed">
            <p>
              Formalizes digital transformation of standardized toddler & adolescent screening scales (digitized AQ-10 and M-CHAT-R/F sub-item vectors).
            </p>
            <ul className="list-disc pl-4 space-y-1 text-slate-500 text-[11px]">
              <li>Quantifies reciprocal smiling, name call orientation, and proto-declarative pointing.</li>
              <li>Calculates continuous behavioral response latencies during structured clinician cues.</li>
              <li>Normalizes binary observation items against peer normative reference baselines.</li>
            </ul>
          </CardContent>
        </Card>

        {/* Paper 2 */}
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between mb-1">
              <Badge variant="default" className="bg-purple-50 text-purple-700 border-purple-200">Research Paper 2</Badge>
              <span className="text-[10px] text-slate-400 font-mono">Modality 3: Acoustic</span>
            </div>
            <CardTitle className="text-base text-slate-900 flex items-center gap-2">
              <Mic className="w-4 h-4 text-purple-600" />
              Vocal Prosody & Acoustic Biomarkers
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-slate-600 leading-relaxed">
            <p>
              Isolates acoustic prosodic biomarkers from infant/child vocalizations and conversational turn-taking segments.
            </p>
            <ul className="list-disc pl-4 space-y-1 text-slate-500 text-[11px]">
              <li>Fundamental frequency ($F_0$) mean and pitch modulation standard deviation.</li>
              <li>Short-term cycle-to-cycle frequency jitter (%) and amplitude shimmer (dB).</li>
              <li>Silent hesitation pause-to-speech ratio and vocal tract formant dispersion.</li>
            </ul>
          </CardContent>
        </Card>

        {/* Patent 1 */}
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between mb-1">
              <Badge variant="success">Patent Reference 1</Badge>
              <span className="text-[10px] text-slate-400 font-mono">Modality 2: Visual Gaze</span>
            </div>
            <CardTitle className="text-base text-slate-900 flex items-center gap-2">
              <Eye className="w-4 h-4 text-teal-600" />
              Ocular Fixation & Scanpath Dynamics
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-slate-600 leading-relaxed">
            <p>
              Patented system and ocular tracking methodology measuring dynamic gaze responses during side-by-side social vs. geometric animated stimuli.
            </p>
            <ul className="list-disc pl-4 space-y-1 text-slate-500 text-[11px]">
              <li>Facial region-of-interest (ROI) dwell percentage vs. abstract geometric preference.</li>
              <li>Joint attention saccade latency: time to shift ocular gaze following an actor's head cue.</li>
              <li>Information entropy of ocular scanpaths: characterizes disorganized visual exploration.</li>
            </ul>
          </CardContent>
        </Card>

        {/* Patent 2 */}
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between mb-1">
              <Badge variant="warning">Patent Reference 2</Badge>
              <span className="text-[10px] text-slate-400 font-mono">Explainable Multimodal Fusion</span>
            </div>
            <CardTitle className="text-base text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-neuro-600" />
              Multimodal Late Fusion & Explainability Architecture
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-slate-600 leading-relaxed">
            <p>
              Patented architectural pipeline combining gradient boosted decision trees (CatBoost, XGBoost), Random Forests, and PyTorch deep neural fusion with model-agnostic explainability.
            </p>
            <ul className="list-disc pl-4 space-y-1 text-slate-500 text-[11px]">
              <li>Local and global feature attribution using SHAP (Shapley Additive exPlanations).</li>
              <li>Local linear decision boundaries with LIME (Local Interpretable Model-agnostic Explanations).</li>
              <li>Explicit verification gate: uncalibrated mode active until certified weights are loaded.</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Feature Catalog Table */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Scale className="w-4 h-4 text-neuro-600" />
            24 Aligned Multimodal Biomarker Features Catalog
          </CardTitle>
          <CardDescription>
            Quantitative specifications and normative reference population parameters
          </CardDescription>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading catalog...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-5 py-3 font-semibold">Biomarker Feature</th>
                    <th className="px-5 py-3 font-semibold">Modality</th>
                    <th className="px-5 py-3 font-semibold">Normative Baseline</th>
                    <th className="px-5 py-3 font-semibold">Typical Range</th>
                    <th className="px-5 py-3 font-semibold">Clinical & Research Significance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {features.map((f) => (
                    <tr key={f.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-5 py-3 font-medium text-slate-900">
                        <div>{f.name}</div>
                        <code className="text-[10px] text-slate-400 font-mono">{f.id}</code>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${
                          f.modality === 'behavioral'
                            ? 'bg-blue-50 text-blue-700'
                            : f.modality === 'visual_gaze'
                            ? 'bg-teal-50 text-teal-700'
                            : 'bg-purple-50 text-purple-700'
                        }`}>
                          {f.modality === 'behavioral' ? 'Behavioral' : f.modality === 'visual_gaze' ? 'Visual Gaze' : 'Acoustic'}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-mono text-slate-600">
                        {f.mean_norm} <span className="text-slate-400 text-[10px]">&plusmn;{f.std_norm}</span>
                      </td>
                      <td className="px-5 py-3 font-mono text-slate-500 text-[11px]">
                        [{f.typical_range[0]} — {f.typical_range[1]}]
                      </td>
                      <td className="px-5 py-3 text-slate-600 text-[11px] leading-relaxed max-w-sm">
                        {f.clinical_note}
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
