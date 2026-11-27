import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Brain,
  Home as HomeIcon,
  Info,
  ClipboardList,
  Video,
  FileCheck2,
  FileText,
  UserCheck,
  Microscope
} from 'lucide-react';
import { api } from '../../services/api';

export type SimpleNavTab = 'home' | 'about' | 'assessment' | 'video' | 'results' | 'reports' | 'research-ml';

interface NavbarProps {
  currentTab: SimpleNavTab;
  onSelectTab: (tab: SimpleNavTab) => void;
  systemStatus?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  systemStatus: _systemStatus = 'healthy',
}) => {
  const [currentRole, setCurrentRole] = useState<'Assessor' | 'Administrator' | 'Researcher'>('Assessor');
  const { t, i18n } = useTranslation();

  useEffect(() => {
    const user = api.getStoredUser();
    if (user?.role) {
      setCurrentRole(user.role);
    } else {
      // Auto-initialize session as Assessor
      api.switchPersona('Assessor').then((res) => setCurrentRole(res.role)).catch(() => {});
    }
  }, []);

  const handleRoleChange = async (newRole: 'Assessor' | 'Administrator' | 'Researcher') => {
    try {
      await api.switchPersona(newRole);
      setCurrentRole(newRole);
    } catch (err) {
      console.error('Failed to switch persona:', err);
    }
  }; 
  

  const navItems: { id: SimpleNavTab; label: string; icon: React.ReactNode }[] = [
  { id: 'home', label: t('home'), icon: <HomeIcon className="w-4 h-4" /> },
  { id: 'about', label: t('about'), icon: <Info className="w-4 h-4" /> },
  { id: 'assessment', label: t('startAssessment'), icon: <ClipboardList className="w-4 h-4" /> },
  { id: 'video', label: t('video'), icon: <Video className="w-4 h-4" /> },
  { id: 'results', label: t('results'), icon: <FileCheck2 className="w-4 h-4" /> },
  { id: 'reports', label: t('reports'), icon: <FileText className="w-4 h-4" /> },
  { id: 'research-ml', label: t('research'), icon: <Microscope className="w-4 h-4" /> },
];
  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <div
          onClick={() => onSelectTab('home')}
          className="flex items-center gap-3 cursor-pointer group flex-shrink-0"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-sky-600 flex items-center justify-center text-white shadow-md shadow-teal-600/20 group-hover:scale-105 transition-transform">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-slate-900 text-lg tracking-tight">NeuroScreen</span>
              <span className="bg-teal-100 text-teal-800 text-[10px] font-black px-1.5 py-0.5 rounded tracking-wide uppercase">AI</span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Early Autism Screening Support</p>
          </div>
        </div>

        {/* Simple 6-item Navigation Menu */}
        <nav className="hidden lg:flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-teal-50 text-teal-800 shadow-xs border border-teal-200'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Status & Role Switcher */}
        <div className="flex items-center gap-3">
          {/* Language Selector */}
<div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5">
  <span className="text-sm">🌐</span>
  <select
    value={i18n.language?.split('-')[0] || 'en'}
    onChange={(e) => i18n.changeLanguage(e.target.value)}
    className="bg-transparent text-xs font-semibold text-slate-700 focus:outline-none cursor-pointer"
    aria-label="Select language"
  >
    <option value="en">English</option>
    <option value="kn">ಕನ್ನಡ</option>
    <option value="hi">हिन्दी</option>
    <option value="te">తెలుగు</option>
    <option value="ta">தமிழ்</option>
  </select>
</div>
          {/* Subtle Persona / Role Indicator */}
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1 text-xs">
            <UserCheck className="w-3.5 h-3.5 text-teal-600" />
            <select
              value={currentRole}
              onChange={(e) => handleRoleChange(e.target.value as any)}
              className="bg-transparent text-xs font-semibold text-slate-700 focus:outline-none cursor-pointer"
              title="Active Role Persona"
            >
              <option value="Assessor">Assessor (Default)</option>
              <option value="Administrator">Administrator</option>
              <option value="Researcher">Researcher</option>
            </select>
          </div>

          {/* System Health Dot */}
          <div
            className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded-lg"
            title="FastAPI + ML Engine Active"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="hidden sm:inline">Online</span>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Row (Horizontal Scrollable) */}
      <div className="lg:hidden flex items-center gap-1 px-4 py-2 bg-slate-50 border-t border-slate-200 overflow-x-auto">
        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-teal-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 bg-white border border-slate-200'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};
