import { SystemHealth, ChatMessage } from '../types';

// Resolve API base URL from Vite environment variable (e.g. VITE_API_URL=http://localhost:8000)
// Falls back to '/api' for Vite dev proxy or relative paths
const getApiBaseUrl = (): string => {
  const envUrl = (
    import.meta.env.VITE_API_URL ||
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_BASE ||
    ''
  ).trim();

  if (!envUrl) {
    return '/api';
  }

  // Normalize localhost to 127.0.0.1 to prevent Windows IPv6 [::1] collisions with other containers
  const normalized = envUrl.replace(/:\/\/localhost(:|\/|$)/, '://127.0.0.1$1');
  const trimmed = normalized.replace(/\/+$/, '');
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
};

export const API_BASE = getApiBaseUrl();

export async function fetchHealth(): Promise<SystemHealth> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      return {
        status: 'unhealthy',
        database: { connected: false, latency_ms: 0, error: `HTTP ${res.status}` },
      };
    }
    return await res.json();
  } catch (err: any) {
    return {
      status: 'unhealthy',
      database: { connected: false, latency_ms: 0, error: err?.message || 'Connection failed' },
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

export async function fetchDocumentContent(docName: string): Promise<{
  document_name: string;
  file_type: string;
  content: string;
  pages?: { page: number; text: string }[];
}> {
  const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(docName)}/content`);
  if (!res.ok) {
    throw new Error(`Failed to load document content: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchSourceChunk(chunkId: string): Promise<{
  chunk_id: string;
  document_id: string;
  document_name: string;
  document_title: string;
  page_number: number;
  section?: string;
  text: string;
}> {
  const res = await fetch(`${API_BASE}/sources/${encodeURIComponent(chunkId)}`);
  if (!res.ok) {
    throw new Error(`Failed to load source chunk: HTTP ${res.status}`);
  }
  return res.json();
}

// ─── Admin API ────────────────────────────────────────────────────────────────

function adminHeaders(adminKey: string): HeadersInit {
  return { 'X-Admin-Key': adminKey };
}

export async function fetchAdminStats(adminKey: string) {
  const res = await fetch(`${API_BASE}/admin/stats`, { headers: adminHeaders(adminKey) });
  if (!res.ok) throw new Error(`Failed to fetch stats: HTTP ${res.status}`);
  return res.json();
}

export async function listAdminDocuments(adminKey: string) {
  const res = await fetch(`${API_BASE}/admin/documents`, { headers: adminHeaders(adminKey) });
  if (!res.ok) throw new Error(`Failed to list documents: HTTP ${res.status}`);
  return res.json();
}

export async function uploadDocument(
  file: File,
  adminKey: string,
  onProgress?: (pct: number) => void,
): Promise<any> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/admin/documents`);
    xhr.setRequestHeader('X-Admin-Key', adminKey);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || `Upload failed: HTTP ${xhr.status}`));
        } catch {
          reject(new Error(`Upload failed: HTTP ${xhr.status}`));
        }
      }
    };
    xhr.onerror = () => reject(new Error('Network error during upload.'));
    xhr.send(formData);
  });
}

export async function deleteAdminDocument(docId: string, adminKey: string) {
  const res = await fetch(`${API_BASE}/admin/documents/${docId}`, {
    method: 'DELETE',
    headers: adminHeaders(adminKey),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Delete failed: HTTP ${res.status}`);
  }
  return res.json();
}
