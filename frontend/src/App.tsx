import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Flame, Cpu, Database, Activity } from 'lucide-react';
import GraphViewer from './components/GraphViewer';
import AgentBrain from './components/AgentBrain';
import CheckpointTimeline from './components/CheckpointTimeline';
import DemoControls from './components/DemoControls';
import { graphApi, agentApi, memvergeApi, AgentStatus, Checkpoint, GraphData } from './services/api';

function App() {
  // State
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentTask, setCurrentTask] = useState<string | null>(null);
  const [isCrashed, setIsCrashed] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);

  // Fetch graph data
  const fetchGraph = useCallback(async () => {
    try {
      const response = await graphApi.getVisualization('demo_user');
      if (response.data.success && response.data.graph) {
        setGraphData(response.data.graph);
      }
    } catch (error) {
      console.error('Failed to fetch graph:', error);
    }
  }, []);

  // Refresh graph when memory cards are created
  const handleCardCreated = useCallback(() => {
    // Refresh graph to show new nodes
    fetchGraph();
  }, [fetchGraph]);

  // Fetch checkpoints
  const fetchCheckpoints = useCallback(async () => {
    try {
      const response = await memvergeApi.listCheckpoints();
      setCheckpoints(response.data.checkpoints || []);
    } catch (error) {
      console.error('Failed to fetch checkpoints:', error);
    }
  }, []);

  // Poll agent status
  useEffect(() => {
    if (!sessionId) return;

    const interval = setInterval(async () => {
      try {
        const response = await agentApi.getStatus(sessionId);
        setAgentStatus(response.data);
        
        if (response.data.status === 'completed' || response.data.status === 'crashed') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Failed to fetch agent status:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionId]);

  // Initial data fetch
  useEffect(() => {
    fetchGraph();
    fetchCheckpoints();
    
    // Poll checkpoints every 5 seconds
    const interval = setInterval(fetchCheckpoints, 5000);
    return () => clearInterval(interval);
  }, [fetchGraph, fetchCheckpoints]);

  // Handlers
  const handleStartTask = async (task: string) => {
    try {
      setIsCrashed(false);
      setCurrentTask(task);
      const response = await agentApi.startTask(task, 'demo_user');
      setSessionId(response.data.session_id);
      setAgentStatus({
        session_id: response.data.session_id,
        status: 'running',
        current_step: 0,
        total_steps: 0,
        steps_completed: [],
        conflict_detected: null,
        final_response: null,
      });
    } catch (error) {
      console.error('Failed to start task:', error);
    }
  };

  const handleCrash = async () => {
    try {
      await memvergeApi.simulateCrash();
      setIsCrashed(true);
      if (agentStatus) {
        setAgentStatus({ ...agentStatus, status: 'crashed' });
      }
    } catch (error) {
      console.error('Failed to simulate crash:', error);
    }
  };

  const handleRestore = async (checkpointId?: string) => {
    try {
      setIsRestoring(true);
      await memvergeApi.restore(checkpointId);
      setIsCrashed(false);
      if (agentStatus) {
        setAgentStatus({ ...agentStatus, status: 'running' });
      }
      await fetchCheckpoints();
    } catch (error) {
      console.error('Failed to restore:', error);
    } finally {
      setIsRestoring(false);
    }
  };

  // Transform agent status to steps format
  const agentSteps = React.useMemo(() => {
    if (!agentStatus || !agentStatus.steps_completed) return [];
    
    return agentStatus.steps_completed.map((step, idx) => ({
      step_number: idx + 1,
      description: typeof step === 'object' && step.description 
        ? step.description 
        : `Step ${idx + 1}`,
      status: idx < agentStatus.current_step 
        ? 'completed' as const
        : idx === agentStatus.current_step
        ? 'in_progress' as const
        : 'pending' as const,
      result: typeof step === 'object' ? step.result : step,
    }));
  }, [agentStatus]);

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <motion.header
        className="flex items-center justify-between mb-6"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ 
              rotate: [0, 10, -10, 0],
              scale: [1, 1.1, 1]
            }}
            transition={{ 
              duration: 2,
              repeat: Infinity,
              repeatType: 'reverse'
            }}
            className="text-4xl"
          >
            🔥
          </motion.div>
          <div>
            <h1 className="text-2xl font-bold glow-text">Phoenix Protocol</h1>
            <p className="text-sm text-white/50">Immortal Agent with Graph Memory</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Status indicators */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5">
            <Database size={14} className="text-green-400" />
            <span className="text-xs text-white/70">Neo4j</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5">
            <Cpu size={14} className="text-blue-400" />
            <span className="text-xs text-white/70">MemVerge</span>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
            isCrashed 
              ? 'bg-red-500/20 text-red-400' 
              : agentStatus?.status === 'running'
                ? 'bg-green-500/20 text-green-400'
                : 'bg-white/5 text-white/70'
          }`}>
            <Activity size={14} />
            <span className="text-xs">
              {isCrashed ? 'CRASHED' : agentStatus?.status?.toUpperCase() || 'IDLE'}
            </span>
          </div>
        </div>
      </motion.header>
      
      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6 h-[calc(100vh-120px)]">
        {/* Left Column: Graph */}
        <div className="col-span-5 h-full">
          <GraphViewer
            nodes={graphData.nodes}
            edges={graphData.edges}
            onCardCreated={handleCardCreated}
          />
        </div>
        
        {/* Right Column: Agent + Controls */}
        <div className="col-span-7 flex flex-col gap-6">
          {/* Agent Brain */}
          <div className="flex-1">
            <AgentBrain
              currentTask={currentTask}
              steps={agentSteps}
              currentStep={agentStatus?.current_step || 0}
              totalSteps={agentStatus?.total_steps || 0}
              status={isCrashed ? 'crashed' : agentStatus?.status || 'idle'}
              conflict={agentStatus?.conflict_detected || null}
              finalResponse={agentStatus?.final_response || null}
            />
          </div>
          
          {/* Bottom Row: Timeline + Controls */}
          <div className="grid grid-cols-2 gap-6">
            <CheckpointTimeline
              checkpoints={checkpoints}
              onRestore={handleRestore}
              isRestoring={isRestoring}
            />
            <DemoControls
              onStartTask={handleStartTask}
              onCrash={handleCrash}
              onRestore={() => handleRestore()}
              isRunning={agentStatus?.status === 'running'}
              isCrashed={isCrashed}
            />
          </div>
        </div>
      </div>

    </div>
  );
}

export default App;

