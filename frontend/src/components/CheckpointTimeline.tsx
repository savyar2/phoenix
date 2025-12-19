import React from 'react';
import { RotateCcw } from 'lucide-react';

interface Checkpoint {
  checkpoint_id: string;
  step_number: number;
  total_steps: number;
  task_description: string;
  timestamp: string;
}

interface CheckpointTimelineProps {
  checkpoints: Checkpoint[];
  onRestore: (checkpointId: string) => void;
  isRestoring: boolean;
}

const CheckpointTimeline: React.FC<CheckpointTimelineProps> = ({ checkpoints, onRestore, isRestoring }) => {
  const formatTime = (timestamp: string) => new Date(timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const maxStep = Math.max(...checkpoints.map(c => c.total_steps), 1);

  return (
    <div className="glass-panel p-3 h-full w-full flex flex-col overflow-hidden">
      <div className="flex justify-between items-center mb-2 flex-shrink-0">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <span className="text-lg">📸</span> Checkpoints
        </h2>
        <span className="text-xs text-white/50">{checkpoints.length}</span>
      </div>
      
      {/* Timeline bar */}
      <div className="relative h-6 mb-2 flex-shrink-0">
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/10 -translate-y-1/2" />
        {checkpoints.slice(-6).map((checkpoint, idx) => {
          const position = (checkpoint.step_number / maxStep) * 100;
          return (
            <button key={checkpoint.checkpoint_id} onClick={() => onRestore(checkpoint.checkpoint_id)} disabled={isRestoring}
              className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2" style={{ left: `${Math.min(Math.max(position, 8), 92)}%` }} title={`Step ${checkpoint.step_number}`}>
              <div className={`w-3 h-3 rounded-full border ${idx === checkpoints.length - 1 ? 'bg-phoenix-500 border-phoenix-400' : 'bg-white/20 border-white/30 hover:bg-white/40'}`} />
            </button>
          );
        })}
      </div>
      
      <div className="flex-1 overflow-auto min-h-0 space-y-1">
        {checkpoints.slice(0, 3).map((checkpoint, idx) => (
          <div key={checkpoint.checkpoint_id} className={`flex items-center justify-between p-2 rounded text-xs ${idx === 0 ? 'bg-phoenix-500/10' : 'bg-white/5'}`}>
            <span className="text-white/80">Step {checkpoint.step_number} · {formatTime(checkpoint.timestamp)}</span>
            <button onClick={() => onRestore(checkpoint.checkpoint_id)} disabled={isRestoring} className="p-1 rounded bg-white/10 hover:bg-white/20 disabled:opacity-50"><RotateCcw size={12} /></button>
          </div>
        ))}
        {checkpoints.length === 0 && <div className="text-center text-white/30 py-3 text-sm">No checkpoints</div>}
      </div>
    </div>
  );
};

export default CheckpointTimeline;
