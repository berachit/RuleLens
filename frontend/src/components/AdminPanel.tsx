import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  uploadDocument,
  listAdminDocuments,
  deleteAdminDocument,
  fetchAdminStats,
} from '../services/api';
import {
  UploadCloud,
  Trash2,
  RefreshCw,
  FileText,
  File,
  ShieldCheck,
  CheckCircle2,
  Loader2,
  ArrowLeft,
  KeyRound,
  BookOpen,
  Moon,
  Sun,
  Layers,
  Database,
  Hash,
} from 'lucide-react';

interface AdminDoc {
  id: string;
  name: string;
  title: string;
  file_type: string;
  file_size_bytes: number | null;
  upload_status: 'pending' | 'indexed' | 'failed';
  chunk_count: number;
  page_count?: number;
  created_at: string | null;
}

interface UploadState {
  file: File;
  progress: number;
  status: 'uploading' | 'done' | 'error';
  message: string;
}

interface AdminPanelProps {
  isDark?: boolean;
  onToggleTheme?: () => void;
}

function formatBytes(b: number | null): string {
  if (b == null || b === 0) return '—';
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(2)} MB`;
}

// ─── Minimalist Auth Gate ─────────────────────────────────────────────────────

function AdminAuthGate({
  onAuth,
  isDark,
  onToggleTheme,
}: {
  onAuth: (key: string) => void;
  isDark?: boolean;
  onToggleTheme?: () => void;
}) {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [checking, setChecking] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim()) return;
    setChecking(true);
    setError('');
    try {
      await fetchAdminStats(key.trim());
      onAuth(key.trim());
    } catch {
      setError('Invalid admin key.');
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground transition-colors">
      <div className="w-full border-b border-border px-6 h-14 flex items-center justify-between bg-background/80 backdrop-blur-md">
        <a href="/" className="flex items-baseline gap-1">
          <span className="font-display text-2xl text-foreground font-normal tracking-tight">
            RuleLens
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-accent inline-block" />
        </a>
        <div className="flex items-center gap-3">
          {onToggleTheme && (
            <button
              onClick={onToggleTheme}
              aria-label="Toggle theme"
              className="p-1.5 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border"
            >
              {isDark ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5" />}
            </button>
          )}
          <a
            href="/"
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors font-mono"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Assistant
          </a>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-sm p-6 sm:p-8 rounded-2xl border border-border bg-surface shadow-sm space-y-5">
          <div className="space-y-1">
            <h1 className="font-display text-2xl font-normal text-foreground">
              Admin Access
            </h1>
            <p className="text-muted-foreground text-xs font-light">
              Enter key to manage vector database documents.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="relative">
              <KeyRound className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="Admin key..."
                className="w-full pl-9 pr-3 py-2 rounded-xl border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 font-mono"
                autoFocus
              />
            </div>

            {error && (
              <p className="text-xs text-rose-500 font-mono">{error}</p>
            )}

            <button
              type="submit"
              disabled={checking || !key.trim()}
              className="w-full py-2 rounded-full bg-foreground text-background text-xs font-medium hover:bg-foreground/90 transition-all disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {checking ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
              {checking ? 'Checking...' : 'Unlock'}
            </button>
          </form>

          <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
            <span className="text-muted-foreground font-mono">Demo:</span>
            <button
              type="button"
              onClick={() => {
                setKey('rulelens-admin');
                setError('');
              }}
              className="font-mono text-accent hover:underline text-[11px]"
            >
              rulelens-admin →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

interface AdminStats {
  total_documents: number;
  indexed_documents: number;
  failed_documents: number;
  total_pages?: number;
  total_chunks_in_db: number;
  in_memory_chunks: number;
  vector_dimension?: number;
  storage: string;
}

// ─── Streamlined AdminPanel ───────────────────────────────────────────────────

export const AdminPanel: React.FC<AdminPanelProps> = ({ isDark = false, onToggleTheme }) => {
  const [adminKey, setAdminKey] = useState<string | null>(() => sessionStorage.getItem('rl-admin-key'));
  const [docs, setDocs] = useState<AdminDoc[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploads, setUploads] = useState<UploadState[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [actionState, setActionState] = useState<Record<string, 'deleting'>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async (key: string) => {
    setLoading(true);
    try {
      const [docsData, statsData] = await Promise.all([
        listAdminDocuments(key),
        fetchAdminStats(key).catch(() => null),
      ]);
      setDocs(docsData.documents || []);
      if (statsData) setStats(statsData);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (adminKey) refresh(adminKey);
  }, [adminKey, refresh]);

  const handleAuth = (key: string) => {
    sessionStorage.setItem('rl-admin-key', key);
    setAdminKey(key);
  };

  const handleLogout = () => {
    sessionStorage.removeItem('rl-admin-key');
    setAdminKey(null);
  };

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    if (!adminKey) return;
    const fileArr = Array.from(files);
    for (const file of fileArr) {
      const uploadEntry: UploadState = { file, progress: 0, status: 'uploading', message: '' };
      setUploads((prev) => [...prev, uploadEntry]);

      try {
        await uploadDocument(file, adminKey, (pct) => {
          setUploads((prev) =>
            prev.map((u) => (u.file === file ? { ...u, progress: pct } : u))
          );
        });
        setUploads((prev) =>
          prev.map((u) =>
            u.file === file
              ? { ...u, status: 'done', progress: 100, message: 'Indexed' }
              : u
          )
        );
      } catch (err: any) {
        setUploads((prev) =>
          prev.map((u) =>
            u.file === file ? { ...u, status: 'error', message: err.message || 'Failed' } : u
          )
        );
      }
    }
    await refresh(adminKey);
  }, [adminKey, refresh]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
  };

  const handleDelete = async (doc: AdminDoc) => {
    if (!adminKey || !confirm(`Delete "${doc.name}" from database?`)) return;
    setActionState((s) => ({ ...s, [doc.id]: 'deleting' }));
    try {
      await deleteAdminDocument(doc.id, adminKey);
      await refresh(adminKey);
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setActionState((s) => { const n = { ...s }; delete n[doc.id]; return n; });
    }
  };

  if (!adminKey) {
    return <AdminAuthGate onAuth={handleAuth} isDark={isDark} onToggleTheme={onToggleTheme} />;
  }

  const totalDocs = stats?.total_documents ?? docs.length;
  const totalChunks = stats?.total_chunks_in_db ?? docs.reduce((acc, d) => acc + (d.chunk_count || 0), 0);
  const totalPages = stats?.total_pages ?? docs.reduce((acc, d) => acc + (d.page_count || 1), 0);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans transition-colors">
      {/* Header */}
      <header className="sticky top-0 z-30 w-full border-b border-border bg-background/80 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-baseline gap-1">
              <span className="font-display text-2xl text-foreground font-normal tracking-tight">
                RuleLens
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-accent inline-block" />
            </a>
            <span className="text-xs uppercase tracking-wider text-muted-foreground font-mono border-l border-border pl-3">
              Admin
            </span>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-mono text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {totalDocs} docs · {totalChunks} chunks
            </span>

            <button
              onClick={() => refresh(adminKey)}
              disabled={loading}
              title="Refresh"
              className="p-1.5 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-accent' : ''}`} />
            </button>

            {onToggleTheme && (
              <button
                onClick={onToggleTheme}
                aria-label="Toggle theme"
                className="p-1.5 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border"
              >
                {isDark ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5" />}
              </button>
            )}

            <button
              onClick={handleLogout}
              className="text-xs text-muted-foreground hover:text-foreground font-mono px-2.5 py-1 rounded-full border border-border hover:bg-muted transition-colors"
            >
              Lock
            </button>

            <a
              href="/"
              className="flex items-center gap-1 px-3 py-1 rounded-full bg-foreground text-background hover:bg-foreground/90 transition-all text-xs font-medium"
            >
              <ArrowLeft className="w-3 h-3" />
              <span>Assistant</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">

        {/* Compact Title + Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border">
          <div>
            <h1 className="font-display text-2xl sm:text-3xl font-normal text-foreground tracking-tight">
              Regulations Corpus
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5 font-light">
              Stored directly in PostgreSQL vector database. No files stored on disk.
            </p>
          </div>

          <button
            onClick={() => fileInputRef.current?.click()}
            className="self-start sm:self-auto px-4 py-2 rounded-full bg-foreground text-background hover:bg-foreground/90 text-xs font-medium transition-all flex items-center gap-1.5 shadow-sm"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>
        </div>

        {/* Essential Metrics: No. of Docs, Chunks, Pages, Vector Store */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-xl border border-border bg-surface p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-muted-foreground mb-1">
              <span className="text-[11px] font-mono uppercase tracking-wider">No. of Docs</span>
              <FileText className="w-3.5 h-3.5 text-accent" />
            </div>
            <div className="font-mono text-2xl font-semibold text-foreground tracking-tight">
              {totalDocs}
            </div>
            <span className="text-[11px] text-muted-foreground font-sans mt-0.5">
              Active in database
            </span>
          </div>

          <div className="rounded-xl border border-border bg-surface p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-muted-foreground mb-1">
              <span className="text-[11px] font-mono uppercase tracking-wider">Total Chunks</span>
              <Hash className="w-3.5 h-3.5 text-accent" />
            </div>
            <div className="font-mono text-2xl font-semibold text-foreground tracking-tight">
              {totalChunks}
            </div>
            <span className="text-[11px] text-muted-foreground font-sans mt-0.5">
              384-d dense vectors
            </span>
          </div>

          <div className="rounded-xl border border-border bg-surface p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-muted-foreground mb-1">
              <span className="text-[11px] font-mono uppercase tracking-wider">Total Pages</span>
              <Layers className="w-3.5 h-3.5 text-accent" />
            </div>
            <div className="font-mono text-2xl font-semibold text-foreground tracking-tight">
              {totalPages}
            </div>
            <span className="text-[11px] text-muted-foreground font-sans mt-0.5">
              Extracted in memory
            </span>
          </div>

          <div className="rounded-xl border border-border bg-surface p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-muted-foreground mb-1">
              <span className="text-[11px] font-mono uppercase tracking-wider">Vector Store</span>
              <Database className="w-3.5 h-3.5 text-emerald-500" />
            </div>
            <div className="font-mono text-base font-semibold text-foreground tracking-tight flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              pgvector
            </div>
            <span className="text-[11px] text-muted-foreground font-sans mt-0.5">
              Port 5434 · PostgreSQL
            </span>
          </div>
        </div>

        {/* Compact Dropzone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`
            border border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-150 flex flex-col items-center justify-center gap-1.5
            ${isDragOver
              ? 'border-accent bg-accent/5'
              : 'border-border bg-surface/50 hover:border-accent/40'
            }
          `}
        >
          <UploadCloud className="w-5 h-5 text-muted-foreground" />
          <p className="text-xs text-foreground font-medium">
            {isDragOver ? 'Drop files to upload' : 'Drag & drop .md, .pdf, or .txt files, or click to browse'}
          </p>
          <span className="text-[11px] text-muted-foreground font-mono">
            Auto-chunked and embedded in vector database (max 20 MB)
          </span>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".md,.pdf,.txt"
            className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />
        </div>

        {/* Upload Status Mini-List */}
        {uploads.length > 0 && (
          <div className="space-y-1.5">
            {uploads.map((u, i) => (
              <div
                key={i}
                className="flex items-center justify-between gap-3 px-3.5 py-2 rounded-lg border border-border bg-surface text-xs"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <FileText className="w-3.5 h-3.5 text-accent shrink-0" />
                  <span className="truncate text-foreground font-medium">{u.file.name}</span>
                  <span className="text-[11px] text-muted-foreground font-mono">({formatBytes(u.file.size)})</span>
                </div>

                <div className="shrink-0">
                  {u.status === 'uploading' && (
                    <span className="inline-flex items-center gap-1 font-mono text-muted-foreground text-[11px]">
                      <Loader2 className="w-3 h-3 animate-spin text-accent" /> {u.progress}%
                    </span>
                  )}
                  {u.status === 'done' && (
                    <span className="inline-flex items-center gap-1 font-mono text-emerald-600 dark:text-emerald-400 text-[11px]">
                      <CheckCircle2 className="w-3 h-3" /> Indexed
                    </span>
                  )}
                  {u.status === 'error' && (
                    <span className="font-mono text-rose-500 text-[11px]">
                      {u.message}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Compact Document Table */}
        <div className="space-y-2">
          {loading && docs.length === 0 ? (
            <div className="p-8 text-center text-xs font-mono text-muted-foreground flex items-center justify-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-accent" />
              Loading documents...
            </div>
          ) : docs.length === 0 ? (
            <div className="p-8 text-center rounded-xl border border-dashed border-border space-y-1">
              <BookOpen className="w-5 h-5 mx-auto text-muted-foreground" />
              <p className="text-xs text-foreground font-medium">No documents in database</p>
              <p className="text-[11px] text-muted-foreground">Upload a file above to add regulations.</p>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-surface overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/40 border-b border-border font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="py-2.5 px-4 font-normal">Document</th>
                    <th className="py-2.5 px-3 font-normal hidden sm:table-cell">Type</th>
                    <th className="py-2.5 px-3 font-normal hidden md:table-cell">Size</th>
                    <th className="py-2.5 px-3 font-normal text-right hidden sm:table-cell">Pages</th>
                    <th className="py-2.5 px-3 font-normal text-right">Chunks</th>
                    <th className="py-2.5 px-3 font-normal">Status</th>
                    <th className="py-2.5 px-3 font-normal text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {docs.map((doc) => {
                    const action = actionState[doc.id];
                    return (
                      <tr key={doc.id} className="hover:bg-muted/20 transition-colors">
                        <td className="py-2.5 px-4">
                          <div className="flex items-center gap-2.5 min-w-0">
                            {doc.file_type === 'pdf' ? (
                              <File className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                            ) : (
                              <FileText className="w-3.5 h-3.5 text-accent shrink-0" />
                            )}
                            <span className="font-medium text-foreground truncate max-w-[200px] sm:max-w-xs" title={doc.name}>
                              {doc.name}
                            </span>
                          </div>
                        </td>

                        <td className="py-2.5 px-3 hidden sm:table-cell font-mono text-[11px] text-muted-foreground uppercase">
                          {doc.file_type}
                        </td>

                        <td className="py-2.5 px-3 hidden md:table-cell font-mono text-[11px] text-muted-foreground">
                          {formatBytes(doc.file_size_bytes)}
                        </td>

                        <td className="py-2.5 px-3 text-right font-mono text-muted-foreground hidden sm:table-cell">
                          {doc.page_count ?? 1}
                        </td>

                        <td className="py-2.5 px-3 text-right font-mono text-foreground font-semibold">
                          {doc.chunk_count}
                        </td>

                        <td className="py-2.5 px-3">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            <span className="w-1 h-1 rounded-full bg-emerald-500" />
                            Ready
                          </span>
                        </td>

                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleDelete(doc)}
                            disabled={!!action}
                            title="Delete"
                            className="p-1 text-muted-foreground hover:text-rose-500 transition-colors disabled:opacity-40"
                          >
                            {action === 'deleting' ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Trash2 className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminPanel;
