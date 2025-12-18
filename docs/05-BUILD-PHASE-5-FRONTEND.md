# 🖥️ Phase 5: Frontend Dashboard

**Estimated Time: 4-5 hours**

This phase builds the React dashboard that visualizes the Phoenix Protocol in action.

---

## 5.1 Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          PHOENIX DASHBOARD                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                           HEADER / NAV                                     │  │
│  │   🔥 Phoenix Protocol              [Status: Running]         [Demo Mode]  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌─────────────────────────────┐  ┌────────────────────────────────────────────┐│
│  │     💎 GRAPH VIEWER         │  │              🧠 AGENT BRAIN                ││
│  │     (Neo4j Visualization)   │  │                                            ││
│  │                             │  │  Current Task: "Book dinner reservation"   ││
│  │    ┌───┐      ┌───┐        │  │                                            ││
│  │    │User│─────│Steak│       │  │  ┌────────────────────────────────────┐   ││
│  │    └─┬─┘      └───┘        │  │  │  Step 1: Load context      ✅      │   ││
│  │      │                      │  │  │  Step 2: Check preferences ✅      │   ││
│  │      │ HAS_CONSTRAINT       │  │  │  Step 3: Detect conflicts  🔄      │   ││
│  │      ▼                      │  │  │  Step 4: Resolve           ⏳      │   ││
│  │    ┌────┐                   │  │  │  Step 5: Book restaurant   ⏳      │   ││
│  │    │NoMeat│                 │  │  └────────────────────────────────────┘   ││
│  │    └────┘                   │  │                                            ││
│  │                             │  │  🔴 CONFLICT DETECTED                      ││
│  │  [Zoom] [Reset] [Filter]    │  │  Preference: Steakhouse X                  ││
│  └─────────────────────────────┘  │  Constraint: No Red Meat (3 days ago)      ││
│                                    │  Resolution: CONSTRAINT_WINS               ││
│  ┌─────────────────────────────┐  │                                            ││
│  │     📸 CHECKPOINT TIMELINE  │  └────────────────────────────────────────────┘│
│  │                             │                                                 │
│  │  ──●────●────●────●────●──  │  ┌────────────────────────────────────────────┐│
│  │   10   15   20   25   30    │  │              ⚡ DEMO CONTROLS               ││
│  │         Step Number         │  │                                            ││
│  │                             │  │  [💥 Crash Agent]  [🔄 Restore Latest]     ││
│  │  Latest: Step 25 @ 14:32:00 │  │                                            ││
│  │  [Restore from Step 20]     │  │  [📝 Send Task]  "________________"        ││
│  └─────────────────────────────┘  └────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.2 Project Setup

### Step 1: Create React App

```bash
cd frontend

# Create with Vite
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install

# Install additional packages
npm install @tanstack/react-query axios socket.io-client
npm install react-force-graph-2d d3
npm install framer-motion
npm install lucide-react
npm install tailwindcss postcss autoprefixer
npm install @radix-ui/react-dialog @radix-ui/react-tabs

# Initialize Tailwind
npx tailwindcss init -p
```

### Step 2: Configure Tailwind

Update `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        phoenix: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
        },
        cyber: {
          dark: '#0a0a0f',
          darker: '#050508',
          purple: '#a855f7',
          blue: '#3b82f6',
          green: '#22c55e',
        }
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(249, 115, 22, 0.5)' },
          '50%': { boxShadow: '0 0 40px rgba(249, 115, 22, 0.8)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      }
    },
  },
  plugins: [],
}
```

Update `src/index.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --phoenix-glow: rgba(249, 115, 22, 0.6);
  --graph-node-user: #f97316;
  --graph-node-preference: #22c55e;
  --graph-node-constraint: #ef4444;
  --graph-edge-default: #6b7280;
  --graph-edge-conflict: #ef4444;
}

body {
  @apply bg-cyber-darker text-white font-display;
  background: 
    radial-gradient(ellipse at top, rgba(249, 115, 22, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at bottom, rgba(59, 130, 246, 0.05) 0%, transparent 50%),
    #050508;
}

.glass-panel {
  @apply bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl;
}

.glow-text {
  text-shadow: 0 0 30px var(--phoenix-glow);
}
```

---

## 5.3 API Service

Create `src/services/api.ts`:

```typescript
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface SemanticTuple {
  subject: string;
  subject_type: string;
  predicate: string;
  object: string;
  object_type: string;
  confidence: number;
}

export interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    properties: Record<string, unknown>;
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
  }>;
}

export interface AgentStatus {
  session_id: string;
  status: 'idle' | 'running' | 'paused' | 'crashed' | 'completed';
  current_step: number;
  total_steps: number;
  steps_completed: Array<{
    step_number: number;
    description: string;
    result: unknown;
  }>;
  conflict_detected: Record<string, unknown> | null;
  final_response: string | null;
}

export interface Checkpoint {
  checkpoint_id: string;
  step_number: number;
  total_steps: number;
  task_description: string;
  timestamp: string;
}

// API Functions
export const graphApi = {
  getVisualization: (userId: string) =>
    api.get<{ graph: GraphData }>(`/api/graph/visualize/${userId}`),
  
  getContext: (userId: string) =>
    api.get(`/api/graph/context/${userId}`),
  
  ingestTuples: (userId: string, tuples: SemanticTuple[]) =>
    api.post('/api/graph/ingest', { user_id: userId, tuples }),
};

export const agentApi = {
  startTask: (task: string, userId: string = 'demo_user') =>
    api.post<{ session_id: string }>('/api/agent/start', { task, user_id: userId }),
  
  getStatus: (sessionId: string) =>
    api.get<AgentStatus>(`/api/agent/status/${sessionId}`),
  
  listSessions: () =>
    api.get<{ sessions: AgentStatus[] }>('/api/agent/sessions'),
};

export const memvergeApi = {
  listCheckpoints: () =>
    api.get<{ checkpoints: Checkpoint[] }>('/api/memverge/checkpoints'),
  
  createCheckpoint: (data: {
    container_id: string;
    step_number: number;
    total_steps: number;
    task_description: string;
  }) =>
    api.post('/api/memverge/checkpoint', data),
  
  restore: (checkpointId?: string) =>
    api.post('/api/memverge/restore', { checkpoint_id: checkpointId }),
  
  simulateCrash: () =>
    api.post('/api/memverge/simulate-crash', { container_id: 'phoenix-agent' }),
};
```

---

## 5.4 Graph Viewer Component

Create `src/components/GraphViewer.tsx`:

```tsx
import React, { useRef, useEffect, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { motion } from 'framer-motion';
import { ZoomIn, ZoomOut, Maximize2, Filter } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
}

interface GraphViewerProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedNode?: string;
  onNodeClick?: (node: GraphNode) => void;
}

const NODE_COLORS: Record<string, string> = {
  User: '#f97316',
  Person: '#f97316',
  Preference: '#22c55e',
  Constraint: '#ef4444',
  Goal: '#3b82f6',
  Restaurant: '#a855f7',
  Diet: '#f59e0b',
  Budget: '#06b6d4',
  Action: '#8b5cf6',
  Entity: '#6b7280',
};

const GraphViewer: React.FC<GraphViewerProps> = ({
  nodes,
  edges,
  highlightedNode,
  onNodeClick,
}) => {
  const graphRef = useRef<any>();
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);

  const handleZoomIn = () => {
    graphRef.current?.zoom(1.5, 400);
  };

  const handleZoomOut = () => {
    graphRef.current?.zoom(0.67, 400);
  };

  const handleReset = () => {
    graphRef.current?.zoomToFit(400);
  };

  const nodeColor = useCallback((node: GraphNode) => {
    if (highlightedNode === node.id) {
      return '#fff';
    }
    return NODE_COLORS[node.type] || NODE_COLORS.Entity;
  }, [highlightedNode]);

  const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || node.id;
    const fontSize = 12 / globalScale;
    const nodeSize = highlightedNode === node.id ? 8 : 6;
    
    // Node circle
    ctx.beginPath();
    ctx.arc(node.x!, node.y!, nodeSize, 0, 2 * Math.PI);
    ctx.fillStyle = nodeColor(node);
    ctx.fill();
    
    // Glow effect for highlighted node
    if (highlightedNode === node.id) {
      ctx.shadowColor = '#f97316';
      ctx.shadowBlur = 15;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
    
    // Label
    ctx.font = `${fontSize}px 'Space Grotesk', sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fillText(label, node.x!, node.y! + nodeSize + fontSize);
  }, [highlightedNode, nodeColor]);

  const linkColor = useCallback((link: GraphEdge) => {
    if (link.type === 'CONFLICTS_WITH') {
      return '#ef4444';
    }
    if (link.type === 'HAS_CONSTRAINT' || link.type === 'HAS_GOAL') {
      return '#f59e0b';
    }
    return 'rgba(255, 255, 255, 0.3)';
  }, []);

  return (
    <motion.div
      className="glass-panel p-4 h-full relative"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span className="text-2xl">💎</span>
          Memory Graph
        </h2>
        <div className="flex gap-2">
          <button
            onClick={handleZoomIn}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={handleReset}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
          >
            <Maximize2 size={16} />
          </button>
        </div>
      </div>
      
      <div className="h-[calc(100%-60px)] rounded-xl overflow-hidden bg-black/30">
        <ForceGraph2D
          ref={graphRef}
          graphData={{ nodes, links: edges }}
          nodeLabel="label"
          nodeColor={nodeColor}
          nodeCanvasObject={nodeCanvasObject}
          linkColor={linkColor}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.2}
          onNodeClick={(node) => onNodeClick?.(node as GraphNode)}
          onNodeHover={(node) => setHoveredNode(node as GraphNode)}
          backgroundColor="transparent"
          cooldownTicks={100}
        />
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-6 left-6 flex flex-wrap gap-3 text-xs">
        {Object.entries(NODE_COLORS).slice(0, 5).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-white/60">{type}</span>
          </div>
        ))}
      </div>
      
      {/* Hovered node info */}
      {hoveredNode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-20 right-6 bg-black/80 p-3 rounded-lg text-sm max-w-[200px]"
        >
          <div className="font-semibold">{hoveredNode.label}</div>
          <div className="text-white/60 text-xs mt-1">Type: {hoveredNode.type}</div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default GraphViewer;
```

---

## 5.5 Agent Brain Component

Create `src/components/AgentBrain.tsx`:

```tsx
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
```

---

## 5.6 Checkpoint Timeline Component

Create `src/components/CheckpointTimeline.tsx`:

```tsx
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
```

---

## 5.7 Demo Controls Component

Create `src/components/DemoControls.tsx`:

```tsx
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
```

---

## 5.8 Main App Component

Create `src/App.tsx`:

```tsx
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
  const [isCrashed, setIsCrashed] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);

  // Fetch graph data
  const fetchGraph = useCallback(async () => {
    try {
      const response = await graphApi.getVisualization('demo_user');
      setGraphData(response.data.graph);
    } catch (error) {
      console.error('Failed to fetch graph:', error);
    }
  }, []);

  // Fetch checkpoints
  const fetchCheckpoints = useCallback(async () => {
    try {
      const response = await memvergeApi.listCheckpoints();
      setCheckpoints(response.data.checkpoints);
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
          />
        </div>
        
        {/* Right Column: Agent + Controls */}
        <div className="col-span-7 flex flex-col gap-6">
          {/* Agent Brain */}
          <div className="flex-1">
            <AgentBrain
              currentTask={agentStatus?.session_id ? 'Active Task' : null}
              steps={agentStatus?.steps_completed?.map((s, i) => ({
                step_number: i + 1,
                description: String(s),
                status: 'completed' as const,
              })) || []}
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
```

---

## 5.9 Dockerfile for Frontend

Create `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

---

## 5.10 Phase 5 Verification

### Test 1: Frontend Builds
```bash
cd frontend
npm run build
```

### Test 2: Development Server
```bash
npm run dev
```
Visit `http://localhost:5173`

### Test 3: Full Stack
```bash
cd ..
docker-compose up --build
```

---

## 5.11 Phase 5 Deliverables Checklist

- [ ] React app with Vite and TypeScript
- [ ] Tailwind CSS with custom theme
- [ ] GraphViewer component with force-directed layout
- [ ] AgentBrain component showing execution state
- [ ] CheckpointTimeline with restore capability
- [ ] DemoControls for quick demo actions
- [ ] API service with all endpoints
- [ ] Docker configuration for frontend
- [ ] Responsive layout
- [ ] Smooth animations with Framer Motion

---

## Next: [Demo Script](./06-DEMO-SCRIPT.md)

