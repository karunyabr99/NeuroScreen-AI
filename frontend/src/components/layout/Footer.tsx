import React from 'react';
import { AlertCircle, FileCheck2, Scale } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-16 py-8 text-slate-500 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Clinical Disclaimer Callout */}
        <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h5 className="font-semibold text-amber-900 text-xs">Clinical & Ethical Research Safeguard Notice</h5>
            <p className="text-amber-800 leading-relaxed text-[11px]">
              NeuroScreen AI is designed strictly as a clinical decision-support and screening-triaging aid for qualified specialists.
              It is <strong>not an authorized medical diagnosis</strong> and cannot replace comprehensive multidisciplinary evaluations
              (e.g., ADOS-2, ADI-R, or DSM-5/ICD-11 clinical assessments). Synthetic or unverified model weights are never fabricated.
            </p>
            <p className="text-amber-800/90 leading-relaxed text-[11px] pt-1">
              <strong>De-identified Research Identifier Scheme:</strong> Institutional Review Board (IRB) / Ethics Committee approval,
              informed consent, and jurisdictional privacy assessments are mandatory prerequisites prior to real participant data intake.
            </p>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-100 text-[11px]">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-slate-400" />
            <span>Methodologies derived from 2 Research Papers & 2 Patent Reference Architectures</span>
          </div>

          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5 text-slate-600">
              <FileCheck2 className="w-3.5 h-3.5 text-neuro-600" />
              <span>Full-Stack Modular ML Integration</span>
            </span>
            <span>&copy; {new Date().getFullYear()} NeuroScreen AI Project</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

