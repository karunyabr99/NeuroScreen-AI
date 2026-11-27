import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Sparkles,
  Play,
  RotateCw,
  AlertTriangle,
  Shield,
  Layers,
  Sliders,
  History,
  TrendingUp,
  TrendingDown,
  Activity,
  Eye,
  MessageSquare,
  HelpCircle,
  FileText,
  UserCheck
} from 'lucide-react';
import { api } from '../services/api';
import {
  SimulationInput,
  SimulationResultResponse,
  ScenarioDefinition
} from '../types';

export const SimulationDashboard: React.FC = () => {
  const [scenarios, setScenarios] = useState<ScenarioDefinition[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario_a');
  
  // Simulation Inputs State
  const [participantId, setParticipantId] = useState<string>('SIM-TYPICAL-01');
  const [scenarioName, setScenarioName] = useState<string>('Scenario A: Typical Developmental Observations');
  const [ageMonths, setAgeMonths] = useState<number>(36);
  
  const [communication, setCommunication] = useState<number>(0.0);
  const [socialInteraction, setSocialInteraction] = useState<number>(0.0);
  const [responseToName, setResponseToName] = useState<number>(0.0);
  const [eyeContact, setEyeContact] = useState<number>(0.0);
  const [gestureUsage, setGestureUsage] = useState<number>(0.0);
  const [repetitiveBehaviours, setRepetitiveBehaviours] = useState<number>(0.0);
  const [playPatterns, setPlayPatterns] = useState<number>(0.0);
  const [milestones, setMilestones] = useState<number>(0.0);
  const [caregiverObs, setCaregiverObs] = useState<number>(0.0);
  
  const [isIncomplete, setIsIncomplete] = useState<boolean>(false);
  const [clinicalNotes, setClinicalNotes] = useState<string>('');

  // Execution & Results State
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<SimulationResultResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);

  // Load scenarios on mount
  useEffect(() => {
    loadScenarios();
    loadHistory();
  }, []);

  const loadScenarios = async () => {
    try {
      const data = await api.getSimulationScenarios();
      setScenarios(data);
      if (data.length > 0) {
        applyScenario(data[0]);
      }
    } catch (err: any) {
      console.error("Failed to load simulation scenarios:", err);
    }
  };

  const loadHistory = async () => {
    try {
      const hist = await api.getSimulationHistory(10);
      setHistory(hist);
    } catch (err) {
      console.error("Failed to load simulation history:", err);
    }
  };

  const applyScenario = (sc: ScenarioDefinition) => {
    setSelectedScenarioId(sc.id);
    const inp = sc.inputs;
    setParticipantId(inp.participant_id || `SIM-${sc.id.toUpperCase()}`);
    setScenarioName(sc.name);
    setAgeMonths(inp.age_months || 36);
    setCommunication(inp.communication_development ?? 0);
    setSocialInteraction(inp.social_interaction ?? 0);
    setResponseToName(inp.response_to_name ?? 0);
    setEyeContact(inp.eye_contact_observations ?? 0);
    setGestureUsage(inp.gesture_usage ?? 0);
    setRepetitiveBehaviours(inp.repetitive_behaviours ?? 0);
    setPlayPatterns(inp.play_patterns ?? 0);
    setMilestones(inp.developmental_milestones ?? 0);
    setCaregiverObs(inp.caregiver_observations ?? 0);
    setIsIncomplete(inp.is_incomplete ?? false);
    setClinicalNotes(inp.notes || '');
    setErrorMessage(null);
  };

  const generateNewId = () => {
    const randomHex = Math.random().toString(36).substring(2, 8).toUpperCase();
    setParticipantId(`SIM-CHILD-${randomHex}`);
  };

  const handleRunSimulation = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsRunning(true);
    setErrorMessage(null);

    const payload: SimulationInput = {
      participant_id: participantId,
      scenario_name: scenarioName,
      age_months: Number(ageMonths),
      communication_development: Number(communication),
      social_interaction: Number(socialInteraction),
      response_to_name: Number(responseToName),
      eye_contact_observations: Number(eyeContact),
      gesture_usage: Number(gestureUsage),
      repetitive_behaviours: Number(repetitiveBehaviours),
      play_patterns: Number(playPatterns),
      developmental_milestones: Number(milestones),
      caregiver_observations: Number(caregiverObs),
      is_incomplete: isIncomplete,
      notes: clinicalNotes
    };

    try {
      const result = await api.runSimulation(payload);
      setSimulationResult(result);
      await loadHistory();
    } catch (err: any) {
      console.error("Simulation run failed:", err);
      setErrorMessage(err.message || "Failed to execute simulation pipeline.");
    } finally {
      setIsRunning(false);
    }
  };

  const getLevelLabel = (val: number, _type?: string) => {
    if (val === 0) return '0: Age-Typical / Normative';
    if (val <= 1.0) return '1: Mild Variation / Isolated';
    if (val <= 2.0) return '2: Moderate Atypicality';
    return '3: Marked / Clinically Significant';
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
              <Cpu className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Interactive ML Screening Simulation Engine
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-600">
            Stacking Ensemble (Random Forest + SVM + Gradient Boosting &rarr; Logistic Regression) with real-time SHAP explainability.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 p-1.5 rounded-xl text-xs font-semibold text-slate-700">
          <span className="px-2.5 py-1 bg-white rounded-lg shadow-sm border border-slate-200 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Stacking Model Calibrated & Active
          </span>
        </div>
      </div>

      {/* Mandatory Demonstration Notice Banner */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 flex items-start gap-3 shadow-sm">
        <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <p className="font-bold text-sm">DEMONSTRATION SIMULATION DATA – NOT REAL CLINICAL DIAGNOSIS</p>
          <p className="text-amber-800 leading-relaxed">
            All profiles in this engine are synthetic software test simulations (<code className="font-mono bg-amber-100/80 px-1 py-0.5 rounded">is_synthetic = True</code>) and are segregated from clinical datasets.
            NeuroScreen AI is an investigational screening-support research prototype. Autism Spectrum Disorder diagnosis requires comprehensive in-person evaluation (e.g., ADOS-2, ADI-R) administered by licensed medical specialists.
          </p>
        </div>
      </div>

      {/* Dynamic Scenario Preset Selector */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            Dynamic Clinical Research Scenarios
          </h2>
          <span className="text-xs text-slate-500">Click to Auto-Populate Inputs</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-1">
          {scenarios.map((sc) => {
            const isSelected = selectedScenarioId === sc.id;
            return (
              <button
                key={sc.id}
                type="button"
                onClick={() => applyScenario(sc)}
                className={`p-3 rounded-lg border text-left transition-all flex flex-col justify-between ${
                  isSelected
                    ? 'bg-indigo-50/80 border-indigo-400 ring-2 ring-indigo-200 shadow-sm'
                    : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <div>
                  <span className={`text-[11px] font-bold block ${isSelected ? 'text-indigo-900' : 'text-slate-800'}`}>
                    {sc.name.split(':')[0]}
                  </span>
                  <span className="text-[10px] text-slate-500 block line-clamp-1 mt-0.5 font-medium">
                    {sc.clinical_focus}
                  </span>
                </div>
                <span className={`text-[10px] font-semibold mt-2 ${isSelected ? 'text-indigo-600' : 'text-slate-400'}`}>
                  {isSelected ? '✓ Selected' : 'Load Scenario &rarr;'}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Simulation Form and Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Assessment Input Form (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-600" />
                Assessment Observation Inputs
              </h2>
              <button
                type="button"
                onClick={generateNewId}
                className="text-xs text-indigo-600 hover:text-indigo-700 font-semibold flex items-center gap-1"
              >
                <RotateCw className="w-3.5 h-3.5" /> Randomize ID
              </button>
            </div>

            {errorMessage && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleRunSimulation} className="space-y-5">
              {/* Profile Meta Fields */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">Participant ID</label>
                  <input
                    type="text"
                    value={participantId}
                    onChange={(e) => setParticipantId(e.target.value)}
                    className="w-full text-xs font-mono font-semibold bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">Age in Months ({ageMonths}m)</label>
                  <input
                    type="number"
                    min="12"
                    max="120"
                    value={ageMonths}
                    onChange={(e) => setAgeMonths(Number(e.target.value))}
                    className="w-full text-xs font-semibold bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">Scenario Designation</label>
                  <input
                    type="text"
                    value={scenarioName}
                    onChange={(e) => setScenarioName(e.target.value)}
                    className="w-full text-xs bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* 9 Clinical Dimension Sliders */}
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Observation Dimensions (0.0 = Normative, 3.0 = High Atypicality)
                </h3>

                {/* 1. Communication Development */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <MessageSquare className="w-3.5 h-3.5 text-indigo-500" />
                      1. Communication & Language Development
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{communication.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={communication}
                    onChange={(e) => setCommunication(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(communication, 'comm')}</span>
                  </div>
                </div>

                {/* 2. Social Interaction */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-sky-500" />
                      2. Social Interaction & Reciprocity
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{socialInteraction.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={socialInteraction}
                    onChange={(e) => setSocialInteraction(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(socialInteraction, 'social')}</span>
                  </div>
                </div>

                {/* 3. Response to Name */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <UserCheck className="w-3.5 h-3.5 text-teal-500" />
                      3. Response to Name Call (Orienting Latency)
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{responseToName.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={responseToName}
                    onChange={(e) => setResponseToName(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(responseToName, 'name')}</span>
                  </div>
                </div>

                {/* 4. Eye-Contact Observations */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-amber-500" />
                      4. Eye-Contact Observations & Dwell Dynamics
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{eyeContact.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={eyeContact}
                    onChange={(e) => setEyeContact(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(eyeContact, 'gaze')}</span>
                  </div>
                </div>

                {/* 5. Gesture Usage & Pointing */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-purple-500" />
                      5. Gesture Usage & Proto-Declarative Pointing
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{gestureUsage.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={gestureUsage}
                    onChange={(e) => setGestureUsage(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(gestureUsage, 'gesture')}</span>
                  </div>
                </div>

                {/* 6. Repetitive Behaviours & Motor Stereotypies */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <RotateCw className="w-3.5 h-3.5 text-rose-500" />
                      6. Repetitive Behaviours & Motor Stereotypies
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{repetitiveBehaviours.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={repetitiveBehaviours}
                    onChange={(e) => setRepetitiveBehaviours(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(repetitiveBehaviours, 'rep')}</span>
                  </div>
                </div>

                {/* 7. Play Patterns & Focus */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-emerald-500" />
                      7. Play Patterns (Symbolic vs Monotropic Lining)
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{playPatterns.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={playPatterns}
                    onChange={(e) => setPlayPatterns(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(playPatterns, 'play')}</span>
                  </div>
                </div>

                {/* 8. Developmental Milestones */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-orange-500" />
                      8. Developmental Milestones Attainment
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{milestones.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={milestones}
                    onChange={(e) => setMilestones(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(milestones, 'miles')}</span>
                  </div>
                </div>

                {/* 9. Caregiver Observations & Concerns */}
                <div className="space-y-1.5 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <HelpCircle className="w-3.5 h-3.5 text-blue-500" />
                      9. Caregiver Observations & Sensory Concerns
                    </span>
                    <span className="font-mono font-bold text-indigo-700">{caregiverObs.toFixed(1)} / 3.0</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="0.5"
                    value={caregiverObs}
                    onChange={(e) => setCaregiverObs(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                    <span>{getLevelLabel(caregiverObs, 'care')}</span>
                  </div>
                </div>
              </div>

              {/* Incomplete assessment toggle */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <label className="flex items-center gap-2 cursor-pointer text-xs">
                  <input
                    type="checkbox"
                    checked={isIncomplete}
                    onChange={(e) => setIsIncomplete(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <span className="font-semibold text-slate-700">
                    Simulate Incomplete Assessment / Missing Modalities (Oculomotor Sensor Unavailable)
                  </span>
                </label>
              </div>

              {/* Action Button */}
              <button
                type="submit"
                disabled={isRunning}
                className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-sm font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
              >
                {isRunning ? (
                  <>
                    <RotateCw className="w-4 h-4 animate-spin" /> Evaluating Stacking Ensemble...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" /> RUN SIMULATION (CALIBRATED MODEL)
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Real-Time Results & SHAP Explainability (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {simulationResult ? (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6 animate-fadeIn">
              
              {/* Header Badge */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                    Simulation Result
                  </span>
                  <h3 className="text-base font-bold text-slate-900 font-mono">
                    {simulationResult.participant_id}
                  </h3>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full">
                  Saved to DB
                </span>
              </div>

              {/* Probability & Risk Tier Banner */}
              <div className={`p-4 rounded-xl border space-y-2 ${
                simulationResult.risk_tier === 'ELEVATED_TRIAGE_RECOMMENDED'
                  ? 'bg-rose-50 border-rose-200 text-rose-950'
                  : simulationResult.risk_tier === 'MODERATE_MONITOR'
                  ? 'bg-amber-50 border-amber-200 text-amber-950'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-950'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider">
                    Screening Triage Index:
                  </span>
                  <span className="text-2xl font-extrabold font-mono">
                    {(simulationResult.predicted_probability * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs pt-1 border-t border-current/10">
                  <span className="font-bold">Risk Stratification:</span>
                  <span className="font-extrabold tracking-wide uppercase px-2 py-0.5 rounded bg-white/70">
                    {simulationResult.risk_tier.replace(/_/g, ' ')}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[11px] opacity-80 pt-0.5">
                  <span>95% Confidence Interval:</span>
                  <span className="font-mono">
                    [{(simulationResult.confidence_interval.lower * 100).toFixed(1)}% – {(simulationResult.confidence_interval.upper * 100).toFixed(1)}%]
                  </span>
                </div>
              </div>

              {/* Model Architecture Info */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
                <span className="font-bold text-slate-800 block flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-indigo-600" />
                  Model Pipeline: {simulationResult.model_name}
                </span>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {simulationResult.model_architecture}
                </p>
              </div>

              {/* AI Explainability & Contributing Features */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  SHAP Local Feature Contributions
                </h4>

                {/* Positive (Risk Increasing) Features */}
                {simulationResult.positive_contributions.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-rose-700 flex items-center gap-1">
                      <TrendingUp className="w-3.5 h-3.5" /> Indicators Increasing Risk Estimate:
                    </span>
                    <div className="space-y-1.5">
                      {simulationResult.positive_contributions.map((feat, idx) => (
                        <div key={idx} className="p-2 bg-rose-50/60 rounded-lg border border-rose-100 text-xs">
                          <div className="flex justify-between font-semibold text-rose-950">
                            <span>{feat.display_name}</span>
                            <span className="font-mono text-rose-700">+{feat.importance_value.toFixed(3)}</span>
                          </div>
                          {feat.clinical_note && (
                            <p className="text-[10px] text-slate-500 mt-0.5">{feat.clinical_note}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Negative (Risk Mitigating) Features */}
                {simulationResult.negative_contributions.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-emerald-700 flex items-center gap-1">
                      <TrendingDown className="w-3.5 h-3.5" /> Age-Typical Factors Mitigating Risk:
                    </span>
                    <div className="space-y-1.5">
                      {simulationResult.negative_contributions.map((feat, idx) => (
                        <div key={idx} className="p-2 bg-emerald-50/60 rounded-lg border border-emerald-100 text-xs">
                          <div className="flex justify-between font-semibold text-emerald-950">
                            <span>{feat.display_name}</span>
                            <span className="font-mono text-emerald-700">{feat.importance_value.toFixed(3)}</span>
                          </div>
                          {feat.clinical_note && (
                            <p className="text-[10px] text-slate-500 mt-0.5">{feat.clinical_note}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Narrative Summary */}
                <div className="p-3 bg-indigo-50/50 rounded-xl border border-indigo-100 text-xs text-indigo-950 leading-relaxed">
                  <span className="font-bold block mb-1">Clinical AI Summary:</span>
                  <p>{simulationResult.summary_narrative}</p>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-2.5 bg-slate-100 rounded-lg text-[10px] text-slate-500 leading-tight">
                {simulationResult.clinical_disclaimer}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-12 text-center space-y-3">
              <Cpu className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">Ready for Simulation</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Select a research scenario above or adjust the developmental observation sliders, then click <strong>RUN SIMULATION</strong> to evaluate the Stacking Ensemble model.
              </p>
            </div>
          )}

          {/* Past Simulation History */}
          {history.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h3 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <History className="w-3.5 h-3.5 text-slate-500" />
                  Recent Simulation Runs in Database
                </h3>
                <span className="text-[10px] text-slate-400 font-mono">{history.length} runs</span>
              </div>

              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {history.map((h, i) => (
                  <div key={i} className="p-2 bg-slate-50 rounded-lg border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <span className="font-mono font-bold text-slate-800">{h.participant_id}</span>
                      <span className="text-[10px] text-slate-400 block">{h.created_at.slice(0, 16).replace('T', ' ')}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-mono font-bold text-indigo-700">
                        {h.composite_risk_score !== null ? `${(h.composite_risk_score * 100).toFixed(1)}%` : 'N/A'}
                      </span>
                      <span className="text-[9px] uppercase font-semibold text-slate-500 block">
                        {h.risk_tier.split('_')[0]}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
