import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  reasoning?: string;
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
  pending: <Circle className="text-white/30" size={18} />,
  in_progress: <Loader2 className="text-phoenix-500 animate-spin" size={18} />,
  completed: <CheckCircle2 className="text-green-500" size={18} />,
  failed: <AlertTriangle className="text-red-500" size={18} />,
};

const AgentBrain: React.FC<AgentBrainProps> = ({
  currentTask,
  steps,
  currentStep,
  totalSteps,
  status,
  conflict,
  finalResponse,
}) => {
  return (
    <motion.div
      className="glass-panel p-6 h-full flex flex-col"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          Agent Brain
        </h2>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
          status === 'running' ? 'bg-green-500/20 text-green-400' :
          status === 'crashed' ? 'bg-red-500/20 text-red-400' :
          status === 'completed' ? 'bg-blue-500/20 text-blue-400' :
          'bg-white/10 text-white/60'
        }`}>
          {status.toUpperCase()}
        </div>
      </div>
      
      {/* Current Task */}
      {currentTask && (
        <div className="mb-6">
          <div className="text-xs text-white/50 uppercase tracking-wider mb-2">
            Current Task
          </div>
          <div className="text-white/90 bg-white/5 p-3 rounded-lg">
            "{currentTask}"
          </div>
        </div>
      )}
      
      {/* Progress */}
      <div className="mb-6">
        <div className="flex justify-between text-xs text-white/50 mb-2">
          <span>Progress</span>
          <span>{currentStep}/{totalSteps} steps</span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-phoenix-600 to-phoenix-400"
            initial={{ width: 0 }}
            animate={{ width: `${totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>
      
      {/* Steps */}
      <div className="flex-1 overflow-auto mb-6">
        <div className="text-xs text-white/50 uppercase tracking-wider mb-3">
          Execution Steps
        </div>
        <div className="space-y-2">
          <AnimatePresence>
            {steps.map((step, idx) => (
              <motion.div
                key={step.step_number}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className={`flex items-start gap-3 p-3 rounded-lg ${
                  step.status === 'in_progress' 
                    ? 'bg-phoenix-500/10 border border-phoenix-500/30' 
                    : 'bg-white/5'
                }`}
              >
                <div className="mt-0.5">
                  {statusIcons[step.status]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white/90">
                    Step {step.step_number}: {step.description}
                  </div>
                  {step.result && (
                    <div className="text-xs text-white/50 mt-1 truncate">
                      {typeof step.result === 'string' 
                        ? step.result 
                        : JSON.stringify(step.result).slice(0, 100)}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {steps.length === 0 && (
            <div className="text-center text-white/30 py-8">
              No active task
            </div>
          )}
        </div>
      </div>
      
      {/* Conflict Alert */}
      <AnimatePresence>
        {conflict && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl"
          >
            <div className="flex items-center gap-2 text-red-400 font-semibold mb-2">
              <AlertTriangle size={18} />
              CONFLICT DETECTED
            </div>
            <div className="text-sm space-y-1 text-white/80">
              {conflict.preference && (
                <div>
                  <span className="text-white/50">Preference:</span>{' '}
                  {conflict.preference.name}
                </div>
              )}
              {conflict.constraint && (
                <div>
                  <span className="text-white/50">Constraint:</span>{' '}
                  {conflict.constraint.name}
                </div>
              )}
              {conflict.resolution && (
                <div className="mt-2 pt-2 border-t border-white/10">
                  <span className="text-phoenix-400">Resolution:</span>{' '}
                  {conflict.resolution}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Final Response */}
      <AnimatePresence>
        {finalResponse && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-gradient-to-br from-phoenix-500/20 to-purple-500/20 border border-phoenix-500/30 rounded-xl"
          >
            <div className="flex items-center gap-2 text-phoenix-400 font-semibold mb-2">
              <Zap size={18} />
              Response
            </div>
            <div className="text-sm text-white/90">
              {finalResponse}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default AgentBrain;

