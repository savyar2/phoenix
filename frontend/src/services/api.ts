import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8787';

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

export interface MemoryCard {
  id: string;
  type: 'constraint' | 'preference' | 'goal' | 'capability';
  text: string;
  domain: string[];
  priority: 'hard' | 'soft';
  tags: string[];
  persona: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateMemoryCardRequest {
  type: 'constraint' | 'preference' | 'goal' | 'capability';
  text: string;
  domain: string[];
  priority: 'hard' | 'soft';
  tags: string[];
  persona: string;
}

// API Functions
export const graphApi = {
  getVisualization: (userId: string) =>
    api.get<{ success: boolean; graph: GraphData }>(`/api/graph/visualize/${userId}`),
  
  getContext: (userId: string) =>
    api.get(`/api/graph/context/${userId}`),
  
  ingestTuples: (userId: string, tuples: SemanticTuple[]) =>
    api.post('/api/graph/ingest', { user_id: userId, tuples }),
};

export const agentApi = {
  startTask: (task: string, userId: string = 'demo_user') =>
    api.post<{ session_id: string; status: string }>('/api/agent/start', { task, user_id: userId }),
  
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

export const memoryCardsApi = {
  create: (data: CreateMemoryCardRequest) =>
    api.post<{ success: boolean; card: MemoryCard; message: string }>('/api/memory-cards/create', data),
  
  list: (persona?: string, domain?: string) => {
    const params = new URLSearchParams();
    if (persona) params.append('persona', persona);
    if (domain) params.append('domain', domain);
    return api.get<{ success: boolean; cards: MemoryCard[]; count: number }>(
      `/api/memory-cards/list?${params.toString()}`
    );
  },
  
  get: (cardId: string) =>
    api.get<{ success: boolean; card: MemoryCard }>(`/api/memory-cards/${cardId}`),
  
  delete: (cardId: string) =>
    api.delete<{ success: boolean; message: string }>(`/api/memory-cards/${cardId}`),
};

