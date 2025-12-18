import React from 'react';
import { motion } from 'framer-motion';
import { Camera, RotateCcw, Clock } from 'lucide-react';

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

const CheckpointTimeline: React.FC<CheckpointTimelineProps> = ({
  checkpoints,
  onRestore,
  isRestoring,
}) => {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const maxStep = Math.max(...checkpoints.map(c => c.total_steps), 1);

  return (
    <motion.div
      className="glass-panel p-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span className="text-2xl">📸</span>
          Checkpoint Timeline
        </h2>
        <div className="text-xs text-white/50">
          {checkpoints.length} snapshots
        </div>
      </div>
      
      {/* Timeline visualization */}
      <div className="relative h-16 mb-4">
        {/* Timeline bar */}
        <div className="absolute top-1/2 left-0 right-0 h-1 bg-white/10 rounded-full transform -translate-y-1/2" />
        
        {/* Checkpoint dots */}
        {checkpoints.map((checkpoint, idx) => {
          const position = (checkpoint.step_number / maxStep) * 100;
          return (
            <motion.button
              key={checkpoint.checkpoint_id}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              onClick={() => onRestore(checkpoint.checkpoint_id)}
              disabled={isRestoring}
              className="absolute top-1/2 transform -translate-y-1/2 -translate-x-1/2 group"
              style={{ left: `${Math.min(position, 95)}%` }}
            >
              <div className={`w-4 h-4 rounded-full border-2 transition-all ${
                idx === checkpoints.length - 1
                  ? 'bg-phoenix-500 border-phoenix-400 shadow-lg shadow-phoenix-500/50'
                  : 'bg-white/20 border-white/30 hover:bg-white/40 hover:border-white/50'
              }`} />
              
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-black/90 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                Step {checkpoint.step_number}
                <br />
                {formatTime(checkpoint.timestamp)}
              </div>
            </motion.button>
          );
        })}
      </div>
      
      {/* Checkpoint list */}
      <div className="space-y-2 max-h-32 overflow-auto">
        {checkpoints.slice(0, 5).map((checkpoint, idx) => (
          <div
            key={checkpoint.checkpoint_id}
            className={`flex items-center justify-between p-2 rounded-lg text-sm ${
              idx === 0 ? 'bg-phoenix-500/10' : 'bg-white/5'
            }`}
          >
            <div className="flex items-center gap-2">
              <Camera size={14} className={idx === 0 ? 'text-phoenix-400' : 'text-white/40'} />
              <span className="text-white/80">
                Step {checkpoint.step_number}/{checkpoint.total_steps}
              </span>
              <span className="text-white/40 text-xs flex items-center gap-1">
                <Clock size={10} />
                {formatTime(checkpoint.timestamp)}
              </span>
            </div>
            <button
              onClick={() => onRestore(checkpoint.checkpoint_id)}
              disabled={isRestoring}
              className="flex items-center gap-1 px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-xs transition-colors disabled:opacity-50"
            >
              <RotateCcw size={12} />
              Restore
            </button>
          </div>
        ))}
        
        {checkpoints.length === 0 && (
          <div className="text-center text-white/30 py-4 text-sm">
            No checkpoints yet
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default CheckpointTimeline;

