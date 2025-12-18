import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Zap, RotateCcw, Send, Skull, Flame } from 'lucide-react';

interface DemoControlsProps {
  onStartTask: (task: string) => void;
  onCrash: () => void;
  onRestore: () => void;
  isRunning: boolean;
  isCrashed: boolean;
}

const DEMO_TASKS = [
  "Book me a dinner reservation for tonight",
  "Order protein powder that fits my budget",
  "Analyze my last 50 transactions and create a report",
  "Find a restaurant that matches my dietary preferences",
];

const DemoControls: React.FC<DemoControlsProps> = ({
  onStartTask,
  onCrash,
  onRestore,
  isRunning,
  isCrashed,
}) => {
  const [customTask, setCustomTask] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customTask.trim()) {
      onStartTask(customTask);
      setCustomTask('');
    }
  };

  return (
    <motion.div
      className="glass-panel p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
    >
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-6">
        <span className="text-2xl">⚡</span>
        Demo Controls
      </h2>
      
      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onCrash}
          disabled={!isRunning || isCrashed}
          className="flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 font-medium disabled:opacity-30 disabled:cursor-not-allowed hover:bg-red-500/30 transition-colors"
        >
          <Skull size={18} />
          Crash Agent
        </motion.button>
        
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onRestore}
          disabled={!isCrashed}
          className="flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-phoenix-500/20 border border-phoenix-500/30 text-phoenix-400 font-medium disabled:opacity-30 disabled:cursor-not-allowed hover:bg-phoenix-500/30 transition-colors"
        >
          <Flame size={18} />
          Restore (Phoenix!)
        </motion.button>
      </div>
      
      {/* Quick Task Buttons */}
      <div className="mb-6">
        <div className="text-xs text-white/50 uppercase tracking-wider mb-3">
          Quick Demo Tasks
        </div>
        <div className="flex flex-wrap gap-2">
          {DEMO_TASKS.map((task, idx) => (
            <button
              key={idx}
              onClick={() => onStartTask(task)}
              disabled={isRunning}
              className="px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {task.slice(0, 30)}...
            </button>
          ))}
        </div>
      </div>
      
      {/* Custom Task Input */}
      <form onSubmit={handleSubmit}>
        <div className="text-xs text-white/50 uppercase tracking-wider mb-3">
          Custom Task
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={customTask}
            onChange={(e) => setCustomTask(e.target.value)}
            placeholder="Enter a task for the agent..."
            disabled={isRunning}
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm placeholder:text-white/30 focus:outline-none focus:border-phoenix-500/50 disabled:opacity-50"
          />
          <motion.button
            type="submit"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={isRunning || !customTask.trim()}
            className="px-4 py-3 bg-phoenix-500 hover:bg-phoenix-600 rounded-xl font-medium disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={18} />
          </motion.button>
        </div>
      </form>
    </motion.div>
  );
};

export default DemoControls;

