import React, { useState } from 'react';
import { Send, Skull, Flame } from 'lucide-react';

interface DemoControlsProps {
  onStartTask: (task: string) => void;
  onCrash: () => void;
  onRestore: () => void;
  isRunning: boolean;
  isCrashed: boolean;
}

const DEMO_TASKS = ["Book dinner", "Order protein", "Analyze txns", "Find restaurant"];

const DemoControls: React.FC<DemoControlsProps> = ({ onStartTask, onCrash, onRestore, isRunning, isCrashed }) => {
  const [customTask, setCustomTask] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customTask.trim()) { onStartTask(customTask); setCustomTask(''); }
  };

  return (
    <div className="glass-panel p-3 h-full w-full flex flex-col overflow-hidden">
      <div className="flex items-center justify-between mb-2 flex-shrink-0">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <span className="text-lg">⚡</span> Controls
        </h2>
        <div className="flex gap-2">
          <button onClick={onCrash} disabled={!isRunning || isCrashed} className="flex items-center gap-1 px-2 py-1 rounded bg-red-500/20 border border-red-500/30 text-red-400 text-xs disabled:opacity-30">
            <Skull size={14} />Crash
          </button>
          <button onClick={onRestore} disabled={!isCrashed} className="flex items-center gap-1 px-2 py-1 rounded bg-phoenix-500/20 border border-phoenix-500/30 text-phoenix-400 text-xs disabled:opacity-30">
            <Flame size={14} />Restore
          </button>
        </div>
      </div>
      
      <div className="flex flex-wrap gap-1.5 mb-2 flex-shrink-0">
        {DEMO_TASKS.map((task, idx) => (
          <button key={idx} onClick={() => onStartTask(task)} disabled={isRunning} className="px-2 py-1 text-xs bg-white/5 hover:bg-white/10 border border-white/10 rounded disabled:opacity-30">{task}</button>
        ))}
      </div>
      
      <form onSubmit={handleSubmit} className="flex gap-2 flex-shrink-0">
        <input type="text" value={customTask} onChange={(e) => setCustomTask(e.target.value)} placeholder="Custom task..." disabled={isRunning} className="flex-1 bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs placeholder:text-white/30 disabled:opacity-50 min-w-0" />
        <button type="submit" disabled={isRunning || !customTask.trim()} className="px-2 py-1.5 bg-phoenix-500 rounded disabled:opacity-30"><Send size={14} /></button>
      </form>
    </div>
  );
};

export default DemoControls;
