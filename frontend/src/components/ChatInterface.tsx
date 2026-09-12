import React, { useState } from 'react';
import { ChatMessage, SourceCitation } from '../types';
import { StatusBadge } from './StatusBadge';
import { ArrowUp, BookOpen, AlertOctagon, HelpCircle, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  onSelectCitation: (citation: SourceCitation) => void;
  isLoading?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  onSelectCitation,
  isLoading,
}) => {
  const [input, setInput] = useState('');
  const [expandedWhyMap, setExpandedWhyMap] = useState<Record<string, boolean>>({});

  const toggleWhy = (msgId: string) => {
    setExpandedWhyMap((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  return (
    <div className="flex-1 flex flex-col h-full max-w-4xl mx-auto w-full px-4 sm:px-6">
      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto py-6 space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className="space-y-4">
            {msg.role === 'user' ? (
              // User Query Bubble
              <div className="flex justify-end">
                <div className="max-w-2xl px-5 py-3 rounded-2xl bg-muted/80 border border-border/80 text-foreground text-sm sm:text-base font-medium shadow-sm">
                  {msg.content}
                </div>
              </div>
            ) : (
              // Assistant Answer Card
              <div className="p-6 sm:p-7 rounded-3xl border border-border bg-surface/95 backdrop-blur-sm shadow-sm space-y-5 text-left transition-all">
                {/* State Badge & Verified Header */}
                <div className="flex items-center justify-between flex-wrap gap-2 border-b border-border/60 pb-3.5">
                  <div className="flex items-center gap-2">
                    {msg.status && <StatusBadge status={msg.status} />}
                  </div>
                  {msg.status === 'NOT_COVERED' ? (
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground bg-muted/50 px-2.5 py-1 rounded-full border border-border/50">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 inline-block"></span>
                      <span>No Rule in Corpus</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground bg-muted/50 px-2.5 py-1 rounded-full border border-border/50">
                      <span className="w-1.5 h-1.5 rounded-full bg-accent inline-block"></span>
                      <span>Source Verified</span>
                    </div>
                  )}
                </div>

                {/* Conflict Notice if CONFLICT */}
                {msg.status === 'CONFLICT' && (
                  <div className="p-4 sm:p-5 rounded-2xl bg-rose-500/10 border border-rose-500/25 text-rose-900 dark:text-rose-200 text-xs sm:text-sm space-y-3">
                    <div className="flex items-center gap-2 font-semibold text-rose-700 dark:text-rose-300">
                      <AlertOctagon className="w-4 h-4 shrink-0" />
                      <span>Conflicting Rules Detected</span>
                    </div>
                    <p className="leading-relaxed text-xs sm:text-sm text-rose-800 dark:text-rose-200/90">
                      The university rules give conflicting instructions on this matter. Here are both provisions:
                    </p>
                    {msg.conflict_details && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                        <div className="p-3.5 bg-surface/90 dark:bg-surface/50 rounded-xl border border-rose-500/20 shadow-xs space-y-1">
                          <span className="font-semibold block text-[11px] text-rose-600 dark:text-rose-400 uppercase font-mono tracking-wider">
                            Provision A
                          </span>
                          <span className="text-foreground text-xs leading-relaxed block">
                            {msg.conflict_details.provision_a}
                          </span>
                        </div>
                        <div className="p-3.5 bg-surface/90 dark:bg-surface/50 rounded-xl border border-rose-500/20 shadow-xs space-y-1">
                          <span className="font-semibold block text-[11px] text-rose-600 dark:text-rose-400 uppercase font-mono tracking-wider">
                            Provision B
                          </span>
                          <span className="text-foreground text-xs leading-relaxed block">
                            {msg.conflict_details.provision_b}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Refusal Notice if NOT_COVERED */}
                {msg.status === 'NOT_COVERED' && (
                  <div className="p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-500/25 text-xs sm:text-sm space-y-1.5 text-amber-900 dark:text-amber-200">
                    <div className="flex items-center gap-2 font-semibold text-amber-800 dark:text-amber-300">
                      <HelpCircle className="w-4 h-4 shrink-0" />
                      <span>Not Found in University Rules</span>
                    </div>
                    <p className="leading-relaxed text-muted-foreground text-xs sm:text-sm">
                      The official university regulations do not cover this topic. RuleLens only shares verified rules and will not guess or assume.
                    </p>
                  </div>
                )}

                {/* Answer Content - Formatted with Markdown */}
                <div className="prose dark:prose-invert max-w-none text-foreground text-sm sm:text-[15px] leading-relaxed font-sans space-y-3">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="mb-2.5 last:mb-0 leading-relaxed">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc pl-5 my-2.5 space-y-1">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal pl-5 my-2.5 space-y-1">{children}</ol>,
                      li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                      strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                      code: ({ children }) => (
                        <code className="px-1.5 py-0.5 rounded-md bg-muted font-mono text-xs text-accent font-medium border border-border">
                          {children}
                        </code>
                      ),
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>

                {/* Grounding Evidence & Citations */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="pt-3.5 border-t border-border/60 space-y-2.5">
                    <div className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-accent" />
                        <span>Sources Used ({msg.sources.length})</span>
                      </div>
                      <span className="text-[10px] text-muted-foreground/70 lowercase">click to inspect source</span>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {msg.sources.map((src, i) => (
                        <button
                          key={i}
                          onClick={() => onSelectCitation(src)}
                          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-muted/80 hover:bg-accent/10 hover:border-accent/40 border border-border transition-all text-foreground group shadow-xs hover:scale-[1.02] active:scale-[0.98]"
                          title="Click to view exact passage"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-accent/60 group-hover:bg-accent transition-colors"></span>
                          <span className="font-medium group-hover:text-accent transition-colors">
                            {src.document}
                          </span>
                          <span className="text-muted-foreground font-mono text-[11px] bg-background/60 px-1.5 py-0.2 rounded border border-border/40">
                            p.{src.page}
                          </span>
                        </button>
                      ))}
                    </div>

                    {/* Expandable 'Why this evidence?' */}
                    <div className="pt-1">
                      <button
                        onClick={() => toggleWhy(msg.id)}
                        className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 font-mono transition-colors"
                      >
                        <span>Why these sources?</span>
                        {expandedWhyMap[msg.id] ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </button>

                      {expandedWhyMap[msg.id] && (
                        <div className="mt-2.5 p-3.5 rounded-2xl bg-muted/30 border border-border text-xs text-muted-foreground space-y-1.5 leading-relaxed font-sans">
                          <p>
                            RuleLens checked each passage against the question and verified the document page before writing this answer.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Contextual Suggested Questions (Auto Question Telling) */}
                {msg.suggested_questions && msg.suggested_questions.length > 0 && (
                  <div className="pt-3 border-t border-border/50 space-y-2">
                    <div className="flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
                      <Sparkles className="w-3.5 h-3.5 text-accent" />
                      <span>Suggested Follow-up Questions</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {msg.suggested_questions.map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => onSendMessage(q)}
                          disabled={isLoading}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs bg-muted/60 hover:bg-accent/10 hover:border-accent/40 border border-border text-foreground/90 hover:text-foreground text-left transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
                        >
                          <span className="text-accent">↳</span>
                          <span>{q}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="p-6 rounded-3xl border border-border bg-surface animate-pulse space-y-3">
            <div className="h-4 w-28 bg-muted rounded-full"></div>
            <div className="h-4 w-full bg-muted rounded"></div>
            <div className="h-4 w-3/4 bg-muted rounded"></div>
          </div>
        )}
      </div>

      {/* Sticky Follow-up Composer */}
      <div className="py-4 border-t border-border bg-background sticky bottom-0">
        <form
          onSubmit={handleSend}
          className="relative bg-surface rounded-2xl border border-border shadow-sm p-2 flex items-center focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/10 transition-all"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a follow-up question regarding the regulations…"
            className="flex-1 bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={`p-2 rounded-full transition-all ${
              input.trim() && !isLoading
                ? 'bg-accent text-white hover:bg-accent-hover shadow-sm'
                : 'bg-muted text-muted-foreground cursor-not-allowed'
            }`}
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
