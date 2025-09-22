/**
 * TypeScript types for chat interface
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'agent';
  content: string;
  timestamp: Date;
  metadata: {
    agent_id?: string;
    task_id?: string;
    confidence?: number;
    sources?: string[];
    tools_used?: string[];
    processing_time?: number;
    [key: string]: any;
  };
  citations: Citation[];
}

export interface Citation {
  id: string;
  source: string;
  title: string;
  url?: string;
  excerpt: string;
  confidence: number;
  relevance: number;
  timestamp?: Date;
  metadata?: {
    author?: string;
    publishDate?: Date;
    sourceType: 'web' | 'document' | 'database' | 'api';
    credibilityScore?: number;
    [key: string]: any;
  };
}

export interface AgentStatus {
  id: string;
  role: string;
  active: boolean;
  current_tasks: number;
  capabilities: string[];
  last_activity?: Date;
}

export interface TaskProgress {
  task_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  agent_id: string;
  description: string;
  started_at?: Date;
  completed_at?: Date;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
  [key: string]: any;
}