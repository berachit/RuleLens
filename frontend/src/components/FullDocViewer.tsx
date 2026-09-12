import React, { useEffect, useState, useRef } from 'react';
import { SourceCitation } from '../types';
import { FileText, Bookmark, ArrowLeft, Printer, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { fetchDocumentContent, fetchSourceChunk } from '../services/api';

interface FullDocViewerProps {
  citation: SourceCitation;
  onBack?: () => void;
}

export const FullDocViewer: React.FC<FullDocViewerProps> = ({ citation, onBack }) => {
  const [docContent, setDocContent] = useState<string | null>(null);
  const [chunkText, setChunkText] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const highlightRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const loadFullDocAndChunk = async () => {
      setIsLoading(true);
      try {
        // 1. Fetch full document content
        try {
          const docData = await fetchDocumentContent(citation.document);
          setDocContent(docData.content || '');
        } catch {
          setDocContent('');
        }

        // 2. Fetch chunk text
        try {
          const chunkData = await fetchSourceChunk(citation.chunk_id);
          setChunkText(chunkData.text || citation.text_snippet || '');
        } catch {
          setChunkText(citation.text_snippet || '');
        }
      } catch (err) {
        console.error('Failed to load document content:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadFullDocAndChunk();
  }, [citation.document, citation.chunk_id]);

  // Smooth scroll to highlight after render
  useEffect(() => {
    if (!isLoading && highlightRef.current) {
      setTimeout(() => {
        highlightRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 300);
    }
  }, [isLoading, docContent]);

  // Split document into before-chunk, chunk, and after-chunk to render full document with highlighted chunk
  const renderDocumentWithHighlight = () => {
    if (!docContent) {
      return (
        <div className="p-5 rounded-2xl bg-surface border border-border">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{chunkText || ''}</ReactMarkdown>
        </div>
      );
    }

    // Try finding the chunk in the document
    const cleanTarget = (chunkText || citation.text_snippet || '').trim();
    // Use first 60 chars of chunk for robust index matching
    const searchAnchor = cleanTarget.slice(0, 60).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    
    let matchIndex = -1;
    let matchLength = cleanTarget.length;

    if (searchAnchor) {
      const match = docContent.search(new RegExp(searchAnchor, 'i'));
      if (match !== -1) {
        matchIndex = match;
        // Try to match whole section or chunk length
        const sub = docContent.slice(match);
        const nextHeading = sub.slice(1).search(/\n## /);
        if (nextHeading !== -1) {
          matchLength = nextHeading + 1;
        } else {
          matchLength = Math.min(cleanTarget.length + 80, sub.length);
        }
      }
    }

    if (matchIndex === -1) {
      // Fallback: render full document and prominent top highlighted excerpt
      return (
        <div className="space-y-6">
          <div
            ref={highlightRef}
            className="p-6 sm:p-8 rounded-3xl border-2 border-accent bg-accent/5 dark:bg-accent/10 shadow-sm space-y-3"
          >
            <div className="flex items-center gap-2 text-accent font-semibold text-xs font-mono uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              <span>Referenced Passage Chunk ({citation.chunk_id})</span>
            </div>
            <div className="prose dark:prose-invert max-w-none text-foreground text-sm sm:text-base leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{chunkText || ''}</ReactMarkdown>
            </div>
          </div>

          <div className="p-6 sm:p-10 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground pb-2 border-b border-border">
              Full Document Text ({citation.document})
            </h3>
            <div className="prose dark:prose-invert max-w-none text-foreground text-sm sm:text-base leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{docContent}</ReactMarkdown>
            </div>
          </div>
        </div>
      );
    }

    const beforeText = docContent.slice(0, matchIndex);
    const highlightedText = docContent.slice(matchIndex, matchIndex + matchLength);
    const afterText = docContent.slice(matchIndex + matchLength);

    return (
      <div className="p-6 sm:p-10 rounded-3xl border border-border bg-surface shadow-xs space-y-6">
        {/* Before Passage */}
        {beforeText.trim() && (
          <div className="prose dark:prose-invert max-w-none text-foreground/80 text-sm sm:text-base leading-relaxed opacity-75">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => (
                  <div className="my-4 overflow-x-auto rounded-xl border border-border shadow-xs bg-surface">
                    <table className="w-full text-left text-xs sm:text-sm border-collapse">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-muted/80 border-b border-border text-foreground font-semibold font-mono text-[11px] uppercase tracking-wider">{children}</thead>,
                th: ({ children }) => <th className="px-4 py-3 font-semibold text-foreground border-b border-border">{children}</th>,
                td: ({ children }) => <td className="px-4 py-3 border-b border-border/50 text-foreground/90 font-normal">{children}</td>,
              }}
            >
              {beforeText}
            </ReactMarkdown>
          </div>
        )}

        {/* Highlighted Chunk Passage */}
        <div
          ref={highlightRef}
          className="my-6 p-6 sm:p-8 rounded-2xl border-2 border-accent bg-accent/5 dark:bg-accent/10 shadow-md ring-4 ring-accent/10 transition-all space-y-3"
        >
          <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-accent/20">
            <div className="flex items-center gap-2 text-accent font-semibold text-xs font-mono uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              <span>Active Referenced Passage (Page {citation.page})</span>
            </div>
            <span className="text-[11px] font-mono text-accent bg-accent/10 px-2 py-0.5 rounded border border-accent/30">
              {citation.chunk_id}
            </span>
          </div>

          <div className="prose dark:prose-invert max-w-none text-foreground text-sm sm:text-base leading-relaxed font-sans">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => (
                  <div className="my-4 overflow-x-auto rounded-xl border border-accent/30 shadow-xs bg-surface">
                    <table className="w-full text-left text-xs sm:text-sm border-collapse">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-accent/15 border-b border-accent/30 text-foreground font-semibold font-mono text-[11px] uppercase tracking-wider">{children}</thead>,
                th: ({ children }) => <th className="px-4 py-3 font-semibold text-accent dark:text-accent border-b border-accent/30">{children}</th>,
                td: ({ children }) => <td className="px-4 py-3 border-b border-border/50 text-foreground/90 font-normal">{children}</td>,
              }}
            >
              {highlightedText}
            </ReactMarkdown>
          </div>
        </div>

        {/* After Passage */}
        {afterText.trim() && (
          <div className="prose dark:prose-invert max-w-none text-foreground/80 text-sm sm:text-base leading-relaxed opacity-75">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => (
                  <div className="my-4 overflow-x-auto rounded-xl border border-border shadow-xs bg-surface">
                    <table className="w-full text-left text-xs sm:text-sm border-collapse">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-muted/80 border-b border-border text-foreground font-semibold font-mono text-[11px] uppercase tracking-wider">{children}</thead>,
                th: ({ children }) => <th className="px-4 py-3 font-semibold text-foreground border-b border-border">{children}</th>,
                td: ({ children }) => <td className="px-4 py-3 border-b border-border/50 text-foreground/90 font-normal">{children}</td>,
              }}
            >
              {afterText}
            </ReactMarkdown>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      {/* Top Bar */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur-md px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="p-1.5 rounded-full hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              title="Return to search"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-accent" />
            <div>
              <h1 className="font-semibold text-sm sm:text-base leading-tight">
                {citation.document}
              </h1>
              <span className="text-xs text-muted-foreground font-mono">
                Full Document View • Page {citation.page} {citation.section ? `• ${citation.section}` : ''}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border bg-surface text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
            title="Print or Save as PDF"
          >
            <Printer className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Print / Save PDF</span>
          </button>
        </div>
      </header>

      {/* Main Document Reader */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-8 py-8 space-y-6">
        {/* Document Header Metadata Tile */}
        <div className="p-6 rounded-3xl border border-border bg-surface shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 pb-4">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground block">
                Official University Record
              </span>
              <h2 className="text-xl sm:text-2xl font-semibold text-foreground mt-0.5">
                {citation.document}
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-accent/10 border border-accent/30 text-accent font-mono text-xs font-medium">
                Page {citation.page}
              </span>
              <span className="px-2.5 py-1 rounded-full bg-muted font-mono text-xs text-muted-foreground border border-border">
                {citation.chunk_id}
              </span>
            </div>
          </div>

          {citation.section && (
            <div className="flex items-center gap-2 text-xs sm:text-sm text-foreground/80 font-medium">
              <Bookmark className="w-4 h-4 text-accent" />
              <span>Section: {citation.section}</span>
            </div>
          )}
        </div>

        {/* Full Document Body with Highlight */}
        {isLoading ? (
          <div className="p-8 rounded-3xl border border-border bg-surface animate-pulse space-y-4">
            <div className="h-5 w-48 bg-muted rounded"></div>
            <div className="h-4 w-full bg-muted rounded"></div>
            <div className="h-4 w-5/6 bg-muted rounded"></div>
            <div className="h-4 w-3/4 bg-muted rounded"></div>
          </div>
        ) : (
          renderDocumentWithHighlight()
        )}

        {/* Note */}
        <div className="p-4 rounded-2xl bg-muted/40 border border-border text-xs text-muted-foreground flex items-center justify-between">
          <span>Demo University 2026 Regulations</span>
          <span className="font-mono text-[11px]">RuleLens Core</span>
        </div>
      </main>
    </div>
  );
};
