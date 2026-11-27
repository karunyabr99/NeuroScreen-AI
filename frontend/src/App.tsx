import React, { useState } from 'react';
import { Navbar, SimpleNavTab } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { Home } from './pages/Home';
import { About } from './pages/About';
import { SimpleAssessment } from './pages/SimpleAssessment';
import { LiveVideoAssessment } from './pages/LiveVideoAssessment';
import { AssessmentResults } from './pages/AssessmentResults';
import { ReportsArchive } from './pages/ReportsArchive';
import { MLResearchHub } from './components/research/MLResearchHub';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<SimpleNavTab>('home');
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>(undefined);
  const [selectedPatientId, setSelectedPatientId] = useState<string | undefined>(undefined);

  const handleStartAssessmentWithPatient = (patientId?: string) => {
    setSelectedPatientId(patientId);
    setCurrentTab('assessment');
  };

  const handleOpenLiveVideo = () => {
    setCurrentTab('video');
  };

  const handleViewResults = (sessionId?: string) => {
    if (sessionId) {
      setSelectedSessionId(sessionId);
    }
    setCurrentTab('results');
  };

  const handleViewReports = () => {
    setCurrentTab('reports');
  };

  const handleViewAbout = () => {
    setCurrentTab('about');
  };

  const handleCompleteScreening = (sessionId: string) => {
    setSelectedSessionId(sessionId);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans antialiased">
      {/* Restored Simple Healthcare Header with 6 Clear Navigation Tabs */}
      <Navbar currentTab={currentTab} onSelectTab={setCurrentTab} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-16">
        {currentTab === 'home' && (
          <Home
            onStartAssessment={() => handleStartAssessmentWithPatient()}
            onOpenLiveVideo={handleOpenLiveVideo}
            onViewResults={handleViewResults}
            onViewReports={handleViewReports}
            onViewAbout={handleViewAbout}
            onOpenResearchML={() => setCurrentTab('research-ml')}
          />
        )}

        {currentTab === 'about' && (
          <About onOpenResearchML={() => setCurrentTab('research-ml')} />
        )}

        {currentTab === 'assessment' && (
          <SimpleAssessment
            initialPatientId={selectedPatientId}
            onCompleteScreening={handleCompleteScreening}
            onNavigateToResults={handleViewResults}
          />
        )}

        {currentTab === 'video' && (
          <LiveVideoAssessment
            onNavigateToAssessment={() => handleStartAssessmentWithPatient()}
          />
        )}

        {currentTab === 'results' && (
          <AssessmentResults
            initialSessionId={selectedSessionId}
            onNavigateToAssessment={() => handleStartAssessmentWithPatient()}
          />
        )}

        {currentTab === 'reports' && (
          <ReportsArchive
            onSelectSession={(sessionId) => handleViewResults(sessionId)}
            onNavigateToAssessment={() => handleStartAssessmentWithPatient()}
          />
        )}

        {currentTab === 'research-ml' && (
          <MLResearchHub
            onNavigateToAssessment={() => handleStartAssessmentWithPatient()}
          />
        )}
      </main>

      {/* Clean Research Footer */}
      <Footer />
    </div>
  );
};

export default App;
