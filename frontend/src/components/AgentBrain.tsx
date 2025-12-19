import React from 'react';
import { CheckCircle2, Circle, Loader2, AlertTriangle, Zap } from 'lucide-react';

interface TaskStep {
  step_number: number;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  result?: unknown;
}

interface ConflictInfo {
  preference?: { name: string; value?: string };
  constraint?: { name: string; value?: string };
  resolution?: string;
}

interface AgentBrainProps {
  currentTask: string | null;
  steps: TaskStep[];
  currentStep: number;
  totalSteps: number;
  status: 'idle' | 'running' | 'paused' | 'crashed' | 'completed';
  conflict: ConflictInfo | null;
  finalResponse: string | null;
}

const statusIcons = {
  pending: <Circle className="text-white/30" size={14} />,
  in_progress: <Loader2 className="text-phoenix-500 animate-spin" size={14} />,
  completed: <CheckCircle2 className="text-green-500" size={14} />,
  failed: <AlertTriangle className="text-red-500" size={14} />,
};

const AgentBrain: React.FC<AgentBrainProps> = ({ currentTask, steps, currentStep, totalSteps, status, conflict, finalResponse }) => {
  return (
    <div className="glass-panel p-4 h-full w-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-center mb-3 flex-shrink-0">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <span className="text-lg">🧠</span> Agent Brain
        </h2>
        <div className={`px-2 py-0.5 rounded-full text-xs font-medium ${
          status === 'running' ? 'bg-green-500/20 text-green-400' :
          status === 'crashed' ? 'bg-red-500/20 text-red-400' :
          status === 'completed' ? 'bg-blue-500/20 text-blue-400' :
          'bg-white/10 text-white/60'
        }`}>
          {status.toUpperCase()}
        </div>
      </div>
      
      {/* Progress */}
      <div className="mb-3 flex-shrink-0">
        <div className="flex justify-between text-xs text-white/50 mb-1">
          <span>Progress</span>
          <span>{currentStep}/{totalSteps}</span>
        </div>
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-phoenix-600 to-phoenix-400 transition-all" style={{ width: `${totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0}%` }} />
        </div>
      </div>
      
      {/* Steps */}
      <div className="flex-1 overflow-auto min-h-0">
        <div className="text-xs text-white/50 uppercase mb-2">Steps</div>
        <div className="space-y-1.5">
          {steps.map((step) => (
            <div key={step.step_number} className={`flex items-center gap-2 p-2 rounded text-xs ${step.status === 'in_progress' ? 'bg-phoenix-500/10 border border-phoenix-500/30' : 'bg-white/5'}`}>
              {statusIcons[step.status]}
              <span className="text-white/90 truncate">{step.step_number}. {step.description}</span>
            </div>
          ))}
          {steps.length === 0 && <div className="text-center text-white/30 py-4 text-sm">No active task</div>}
        </div>
      </div>
      
      {/* Conflict */}
      {conflict && (
        <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded flex-shrink-0">
          <div className="flex items-center gap-1 text-red-400 font-semibold text-xs mb-1">
            <AlertTriangle size={12} /> CONFLICT
          </div>
          <div className="text-xs text-white/80">
            {conflict.preference && <div>Pref: {conflict.preference.name}</div>}
            {conflict.constraint && <div>Const: {conflict.constraint.name}</div>}
            {conflict.resolution && <div className="text-phoenix-400 mt-1">→ {conflict.resolution}</div>}
          </div>
        </div>
      )}
      
      {/* Response */}
      {finalResponse && (
        <div className="mt-3 p-2 bg-phoenix-500/10 border border-phoenix-500/30 rounded flex-shrink-0">
          <div className="flex items-center gap-1 text-phoenix-400 font-semibold text-xs mb-1">
            <Zap size={12} /> Response
          </div>
          <div className="text-xs text-white/90">{finalResponse}</div>
        </div>
      )}
    </div>
  );
};

export default AgentBrain;
