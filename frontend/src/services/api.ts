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

// Profile Types
export interface ProfileQuestion {
  id: string;
  question_text: string;
  question_type: 'text' | 'multiple_choice' | 'scale' | 'boolean';
  options?: string[];
  required: boolean;
  order: number;
  created_at: string;
}

export interface ProfileAnswer {
  question_id: string;
  answer_text: string;
  answer_data?: any;
  answered_at: string;
  updated_at?: string;
}

export interface SubProfile {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  categories: string[];
  questions: ProfileQuestion[];
  answers: ProfileAnswer[];
  created_at: string;
  updated_at?: string;
}

export interface UserProfile {
  user_id: string;
  main_questions: ProfileQuestion[];
  main_answers: ProfileAnswer[];
  sub_profiles: SubProfile[];
  created_at: string;
  updated_at?: string;
}

export interface ConversationExtractionResponse {
  success: boolean;
  extracted_items: Array<{
    type: string;
    text: string;
    category: string;
    sub_category?: string;
    confidence: number;
    properties?: any;
  }>;
  categorized: {
    Shopping?: any[];
    Eating?: any[];
    Health?: any[];
    Work?: {
      Finance?: any[];
      Coding?: any[];
      Projects?: any[];
      Meetings?: any[];
    };
  };
  message: string;
}

// Profile API
export const profileApi = {
  get: (userId: string) => 
    api.get<{ success: boolean; profile: UserProfile }>(`/api/profile/${userId}`),
  
  create: (userId: string) => 
    api.post<{ success: boolean; profile: UserProfile; message: string }>('/api/profile/create', { user_id: userId }),
  
  updateAnswer: (userId: string, questionId: string, answerText: string, answerData?: any) =>
    api.post<{ success: boolean; answer: ProfileAnswer; message: string }>(`/api/profile/${userId}/answer`, { 
      question_id: questionId, 
      answer_text: answerText,
      answer_data: answerData
    }),
  
  createSubProfile: (userId: string, name: string, description: string, categories: string[]) =>
    api.post<{ success: boolean; sub_profile: SubProfile; message: string }>(`/api/profile/${userId}/sub-profile`, { 
      name, 
      description,
      categories 
    }),
  
  addQuestion: (userId: string, questionText: string, questionType: 'text' | 'multiple_choice' | 'scale' | 'boolean', subProfileId?: string, options?: string[], required?: boolean, order?: number) =>
    api.post<{ success: boolean; question: ProfileQuestion; message: string }>(`/api/profile/${userId}/question`, {
      sub_profile_id: subProfileId,
      question_text: questionText,
      question_type: questionType,
      options: options || [],
      required: required !== undefined ? required : true,
      order: order || 0
    }),
  
  extractConversation: (userId: string, conversationText: string, messages: any[], conversationId?: string) =>
    api.post<ConversationExtractionResponse>(`/api/profile/${userId}/extract`, {
      conversation_id: conversationId || `conv_${Date.now()}`,
      conversation_text: conversationText,
      messages,
      user_id: userId
    }),
};

