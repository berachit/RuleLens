import React from 'react';
import { SourceCitation } from '../types';
import { X, FileText, Bookmark, Shield, ExternalLink } from 'lucide-react';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface SourceViewerProps {
  citation: SourceCitation | null;
  onClose: () => void;
}

export const SourceViewer: React.FC<SourceViewerProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  // Format text: Re-insert newlines for tables if pipe symbols are on a single line
  const rawSnippet = (citation.text_snippet || '').replace(/^#{1,4}\s+[^\n]*\n?/gm, '');
  let formattedSnippet = rawSnippet;
  if (formattedSnippet.includes('|') && !formattedSnippet.includes('\n|')) {
    formattedSnippet = formattedSnippet.replace(/\|\s*\|\s*/g, '|\n| ');
  }

  const handleOpenNewTab = () => {
    const params = new URLSearchParams({
      doc: citation.document,
      page: String(citation.page),
      chunk_id: citation.chunk_id,
      section: citation.section || '',
    });
    window.open(`/?${params.toString()}`, '_blank');
  };

  return (
    <aside className="w-full lg:w-96 lg:border-l border-border bg-surface flex flex-col h-full overflow-y-auto animate-in fade-in slide-in-from-right duration-200 shadow-lg">
      {/* Viewer Header */}
      <div className="p-4 border-b border-border flex items-center justify-between sticky top-0 bg-surface/95 backdrop-blur-sm z-10">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-accent" />
          <h2 className="text-sm font-semibold tracking-tight text-foreground">
            Original Rule Document
          </h2>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleOpenNewTab}
            className="p-1.5 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Close source viewer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metadata Card */}
      <div className="p-5 space-y-5">
        <div className="p-4 rounded-2xl bg-muted/40 border border-border space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
              Document
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-background border border-border font-mono font-medium">
              Page {citation.page}
            </span>
          </div>
          <div className="font-semibold text-sm text-foreground">
            {citation.document}
          </div>
          {citation.section && (
            <div className="text-xs text-muted-foreground flex items-center gap-1.5 pt-1 border-t border-border/40 mt-1">
              <Bookmark className="w-3.5 h-3.5 text-accent shrink-0" />
              <span className="font-medium text-foreground/80">{citation.section}</span>
            </div>
          )}
        </div>

        {/* Clean Passage Excerpt */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider font-mono">
              Official Text
            </span>
            <span className="text-[10px] font-mono text-muted-foreground bg-muted/60 px-2 py-0.5 rounded border border-border/50">
              {citation.chunk_id}
            </span>
          </div>

          <div className="p-5 rounded-2xl border border-border bg-background/60 shadow-xs leading-relaxed text-foreground text-sm font-sans space-y-3 overflow-x-auto">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-2.5 last:mb-0 leading-relaxed">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1.5 my-2">{children}</ol>,
                ul: ({ children }) => <ul className="list-disc pl-5 space-y-1.5 my-2">{children}</ul>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                table: ({ children }) => (
                  <div className="my-3 overflow-x-auto rounded-xl border border-border shadow-xs bg-surface">
                    <table className="w-full text-left text-xs border-collapse">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-muted/80 border-b border-border text-foreground font-semibold font-mono text-[10px] uppercase tracking-wider">{children}</thead>,
                th: ({ children }) => <th className="px-3 py-2 font-semibold text-foreground border-b border-border">{children}</th>,
                td: ({ children }) => <td className="px-3 py-2 border-b border-border/50 text-foreground/90 font-normal">{children}</td>,
              }}
            >
              {formattedSnippet}
            </ReactMarkdown>
          </div>
        </div>

        {/* Verification Badge */}
        <div className="p-3 rounded-xl border border-border bg-surface text-xs text-muted-foreground space-y-1">
          <div className="flex items-center gap-1.5 text-foreground font-medium text-[11px]">
            <Shield className="w-3.5 h-3.5 text-accent" />
            <span>Document Reference</span>
          </div>
          <p className="text-[11px] text-muted-foreground leading-relaxed font-mono">
            {citation.document} (Page {citation.page})
          </p>
        </div>
      </div>
    </aside>
  );
};
