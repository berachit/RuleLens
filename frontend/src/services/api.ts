import { SystemHealth, ChatMessage } from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<SystemHealth> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      return {
        status: 'unhealthy',
        database: { connected: false, latency_ms: 0, error: `HTTP ${res.status}` },
        redis: { enabled: true, connected: false, latency_ms: 0, error: `HTTP ${res.status}` },
      };
    }
    return await res.json();
  } catch (err: any) {
    return {
      status: 'unhealthy',
      database: { connected: false, latency_ms: 0, error: err?.message || 'Connection failed' },
      redis: { enabled: true, connected: false, latency_ms: 0, error: err?.message || 'Connection failed' },
    };
  }
}

export async function sendQuery(query: string, conversationId?: string): Promise<Partial<ChatMessage>> {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, conversation_id: conversationId }),
    });
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
    const data = await res.json();
    return {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: data.answer,
      status: data.status,
      sources: data.sources,
      conflict_details: data.conflict_details,
      suggested_questions: data.suggested_questions || [],
      timestamp: new Date().toISOString(),
    };
  } catch (err: any) {
    throw err;
  }
}
