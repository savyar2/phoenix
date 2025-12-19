import React, { useEffect, useState, useCallback } from 'react';
import { Database, Activity, Cpu, User } from 'lucide-react';
import GraphViewer from './components/GraphViewer';
import AgentBrain from './components/AgentBrain';
import CheckpointTimeline from './components/CheckpointTimeline';
import DemoControls from './components/DemoControls';
import ProfileManager from './components/ProfileManager';
import { graphApi, agentApi, memvergeApi, AgentStatus, Checkpoint, GraphData } from './services/api';

function App() {
  const [view, setView] = useState<'dashboard' | 'profile'>('dashboard');
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentTask, setCurrentTask] = useState<string | null>(null);
  const [isCrashed, setIsCrashed] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);

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

  const handleCardCreated = useCallback(() => { fetchGraph(); }, [fetchGraph]);

  const fetchCheckpoints = useCallback(async () => {
    try {
      const response = await memvergeApi.listCheckpoints();
      setCheckpoints(response.data.checkpoints || []);
    } catch (error) {
      console.error('Failed to fetch checkpoints:', error);
    }
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    const interval = setInterval(async () => {
      try {
        const response = await agentApi.getStatus(sessionId);
        setAgentStatus(response.data);
        if (response.data.status === 'completed' || response.data.status === 'crashed') clearInterval(interval);
      } catch (error) {
        console.error('Failed to fetch agent status:', error);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  useEffect(() => {
    fetchGraph();
    fetchCheckpoints();
    const interval = setInterval(fetchCheckpoints, 10000);
    return () => clearInterval(interval);
  }, [fetchGraph, fetchCheckpoints]);

  const handleStartTask = async (task: string) => {
    try {
      setIsCrashed(false);
      setCurrentTask(task);
      const response = await agentApi.startTask(task, 'demo_user');
      setSessionId(response.data.session_id);
      setAgentStatus({ session_id: response.data.session_id, status: 'running', current_step: 0, total_steps: 0, steps_completed: [], conflict_detected: null, final_response: null });
    } catch (error) {
      console.error('Failed to start task:', error);
    }
  };

  const handleCrash = async () => {
    try {
      await memvergeApi.simulateCrash();
      setIsCrashed(true);
      if (agentStatus) setAgentStatus({ ...agentStatus, status: 'crashed' });
    } catch (error) {
      console.error('Failed to simulate crash:', error);
    }
  };

  const handleRestore = async (checkpointId?: string) => {
    try {
      setIsRestoring(true);
      await memvergeApi.restore(checkpointId);
      setIsCrashed(false);
      if (agentStatus) setAgentStatus({ ...agentStatus, status: 'running' });
      await fetchCheckpoints();
    } catch (error) {
      console.error('Failed to restore:', error);
    } finally {
      setIsRestoring(false);
    }
  };

  const agentSteps = React.useMemo(() => {
    if (!agentStatus || !agentStatus.steps_completed) return [];
    return agentStatus.steps_completed.map((step, idx) => ({
      step_number: idx + 1,
      description: typeof step === 'object' && step.description ? step.description : `Step ${idx + 1}`,
      status: idx < agentStatus.current_step ? 'completed' as const : idx === agentStatus.current_step ? 'in_progress' as const : 'pending' as const,
      result: typeof step === 'object' ? step.result : step,
    }));
  }, [agentStatus]);

  return (
    <div style={{ position: 'fixed', inset: 0, display: 'flex', flexDirection: 'column', padding: 12, gap: 12, background: '#050508' }}>
      {/* Header */}
      <header style={{ height: 48, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="flex items-center gap-3">
          <span className="text-3xl">🔥</span>
          <div>
            <h1 className="text-xl font-bold glow-text leading-tight">Phoenix Protocol</h1>
            <p className="text-xs text-white/50 leading-tight">Immortal Agent with Graph Memory</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setView(view === 'dashboard' ? 'profile' : 'dashboard')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs ${
              view === 'profile' ? 'bg-blue-500/20 text-blue-400' : 'bg-white/5 text-white/70 hover:bg-white/10'
            }`}
          >
            <User size={14} />
            <span>{view === 'profile' ? 'Profile' : 'Dashboard'}</span>
          </button>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 text-xs">
            <Database size={14} className="text-green-400" /><span className="text-white/70">Neo4j</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 text-xs">
            <Cpu size={14} className="text-blue-400" /><span className="text-white/70">MemVerge</span>
          </div>
          <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs ${isCrashed ? 'bg-red-500/20 text-red-400' : agentStatus?.status === 'running' ? 'bg-green-500/20 text-green-400' : 'bg-white/5 text-white/70'}`}>
            <Activity size={14} /><span>{isCrashed ? 'CRASHED' : agentStatus?.status?.toUpperCase() || 'IDLE'}</span>
          </div>
        </div>
      </header>
      
      {/* Main content */}
      {view === 'profile' ? (
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
          <ProfileManager />
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', gap: 12, minHeight: 0 }}>
          {/* Left: Graph */}
          <div style={{ width: '50%', height: '100%' }}>
            <GraphViewer nodes={graphData.nodes} edges={graphData.edges} onCardCreated={handleCardCreated} />
          </div>
          
          {/* Right column */}
          <div style={{ width: '50%', height: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {/* Agent Brain - smaller now */}
            <div style={{ flex: '0 0 55%', minHeight: 0 }}>
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
            
            {/* Bottom: Checkpoints + Controls - larger now */}
            <div style={{ flex: 1, display: 'flex', gap: 12, minHeight: 0 }}>
              <div style={{ flex: 1 }}>
                <CheckpointTimeline checkpoints={checkpoints} onRestore={handleRestore} isRestoring={isRestoring} />
              </div>
              <div style={{ flex: 1 }}>
                <DemoControls onStartTask={handleStartTask} onCrash={handleCrash} onRestore={() => handleRestore()} isRunning={agentStatus?.status === 'running'} isCrashed={isCrashed} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
