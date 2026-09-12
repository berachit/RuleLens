export type RegulationStatus = 'ANSWERED' | 'NOT_COVERED' | 'CONFLICT';

export interface SourceCitation {
  id?: string;
  document: string;
  page: number;
  section?: string;
  chunk_id: string;
  text_snippet?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  status?: RegulationStatus;
  sources?: SourceCitation[];
  conflict_details?: {
    provision_a?: string;
    provision_b?: string;
    explanation?: string;
  };
  suggested_questions?: string[];
  timestamp: string;
}

export interface SystemHealth {
  status: 'healthy' | 'standalone' | 'degraded' | 'unhealthy' | 'checking';
  app?: {
    name: string;
    version: string;
    environment: string;
  };
  corpus?: {
    loaded: boolean;
    chunks_count: number;
  };
  database?: {
    connected: boolean;
    latency_ms: number;
    error?: string | null;
  };
}
