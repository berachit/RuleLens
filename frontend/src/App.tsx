import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { HeroComposer } from './components/HeroComposer';
import { ChatInterface } from './components/ChatInterface';
import { SourceViewer } from './components/SourceViewer';
import { FullDocViewer } from './components/FullDocViewer';
import { AdminPanel } from './components/AdminPanel';
import { ChatMessage, SourceCitation, SystemHealth } from './types';
import { fetchHealth, sendQuery } from './services/api';

export const App: React.FC = () => {
  // Theme state: defaults to system preference, remembers user preference in localStorage
  const [isDark, setIsDark] = useState<boolean>(() => {
    const saved = localStorage.getItem('rulelens-theme');
    if (saved) return saved === 'dark';
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  const handleToggleTheme = () => {
    setIsDark((prev) => {
      const next = !prev;
      localStorage.setItem('rulelens-theme', next ? 'dark' : 'light');
      return next;
    });
  };

  // Render admin panel for /admin path
  if (window.location.pathname.startsWith('/admin')) {
    return <AdminPanel isDark={isDark} onToggleTheme={handleToggleTheme} />;
  }

  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<SourceCitation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [standaloneDocCitation, setStandaloneDocCitation] = useState<SourceCitation | null>(null);

  const [isConnectionFailed, setIsConnectionFailed] = useState<boolean>(false);

  // Check if opened with query parameters for direct standalone document view
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const doc = params.get('doc');
    const chunkId = params.get('chunk_id');
    const page = params.get('page');
    const section = params.get('section');

    if (doc && chunkId) {
      setStandaloneDocCitation({
        document: doc,
        chunk_id: chunkId,
        page: page ? parseInt(page, 10) : 1,
        section: section || undefined,
      });
    }
  }, []);

  // Periodically check system health with a 90-second connecting grace period
  useEffect(() => {
    let failureStartTime: number | null = null;

    const check = async () => {
      const h = await fetchHealth();
      setHealth(h);

      const isWorking = h && (h.status === 'healthy' || h.status === 'standalone' || h.status === 'degraded');
      if (isWorking) {
        failureStartTime = null;
        setIsConnectionFailed(false);
      } else {
        if (!failureStartTime) {
          failureStartTime = Date.now();
        } else if (Date.now() - failureStartTime >= 90000) {
          // After 90 seconds (1.5 min) of persistent failure, mark as offline
          setIsConnectionFailed(true);
        }
      }
    };

    check();
    const interval = setInterval(check, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleNewChat = () => {
    setMessages([]);
    setSelectedCitation(null);
  };

  const handleSendMessage = async (queryText: string) => {
    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: queryText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // Call live backend RAG API
      const response = await sendQuery(queryText);

      const assistantMsg: ChatMessage = {
        id: response.id || `ast-${Date.now()}`,
        role: 'assistant',
        status: response.status,
        content: response.content || 'No response returned by server.',
        sources: response.sources || [],
        conflict_details: response.conflict_details,
        suggested_questions: response.suggested_questions || [],
        timestamp: response.timestamp || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error connecting to backend API: ${err.message}. Ensure backend is running at http://127.0.0.1:8000.`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  if (standaloneDocCitation) {
    return (
      <FullDocViewer
        citation={standaloneDocCitation}
        onBack={() => {
          setStandaloneDocCitation(null);
          window.history.replaceState({}, '', window.location.pathname);
        }}
      />
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground font-sans">
      <Header
        health={health}
        isConnectionFailed={isConnectionFailed}
        onNewChat={handleNewChat}
        hasActiveChat={messages.length > 0}
        isDark={isDark}
        onToggleTheme={handleToggleTheme}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Main Conversation or Hero Area */}
        <main className="flex-1 flex flex-col overflow-y-auto">
          {messages.length === 0 ? (
            <HeroComposer onSubmit={handleSendMessage} isLoading={isLoading} />
          ) : (
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              onSelectCitation={(citation) => setSelectedCitation(citation)}
              isLoading={isLoading}
            />
          )}
        </main>

        {/* Provenance Source Viewer Split-Panel */}
        {selectedCitation && (
          <SourceViewer
            citation={selectedCitation}
            onClose={() => setSelectedCitation(null)}
          />
        )}
      </div>
    </div>
  );
};

export default App;
