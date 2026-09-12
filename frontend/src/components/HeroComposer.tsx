import React, { useState } from 'react';
import { ArrowUp, Sparkles, BookOpen, AlertCircle, Calendar, GraduationCap } from 'lucide-react';

interface HeroComposerProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
}

const SAMPLE_QUERIES = [
  {
    topic: 'Attendance',
    icon: Calendar,
    query: 'What is the minimum attendance required to appear for final examinations?',
    category: 'Conflict check',
  },
  {
    topic: 'Fee Deadlines',
    icon: GraduationCap,
    query: 'What is the deadline for late course drop with full fee refund?',
    category: 'Conflict check',
  },
  {
    topic: 'Wedding Leave',
    icon: AlertCircle,
    query: 'Can a student miss the midterm examination due to an immediate family wedding?',
    category: 'Not in rules',
  },
  {
    topic: 'Grade Appeals',
    icon: BookOpen,
    query: 'What is the exact time limit for lodging a formal academic grade appeal?',
    category: 'Conflict check',
  },
];

export const HeroComposer: React.FC<HeroComposerProps> = ({ onSubmit, isLoading }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSubmit(input.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-12 max-w-3xl mx-auto w-full text-center">
      {/* Editorial Title */}
      <div className="space-y-3 mb-8">
        <h1 className="font-display text-5xl sm:text-6xl md:text-7xl font-normal tracking-tight text-foreground">
          RuleLens.
        </h1>
        <p className="text-muted-foreground text-lg sm:text-xl font-light tracking-wide max-w-md mx-auto">
          See what the rules actually say.
        </p>
      </div>

      {/* ChatGPT-style Dominant Composer */}
      <div className="w-full relative mb-8">
        <form
          onSubmit={handleSubmit}
          className="relative bg-surface rounded-3xl border border-border shadow-sm hover:border-accent/40 focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/10 transition-all p-3 sm:p-4 text-left"
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about attendance, exam policies, refunds, or contradictory regulations…"
            rows={3}
            className="w-full resize-none bg-transparent border-0 text-foreground placeholder:text-muted-foreground/60 focus:outline-none text-base leading-relaxed"
          />

          <div className="flex items-center justify-between pt-2 border-t border-border/50 mt-1">
            <span className="text-xs text-muted-foreground font-mono">
              Press Enter ↵ to search corpus
            </span>

            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={`p-2.5 rounded-full transition-all ${
                input.trim() && !isLoading
                  ? 'bg-accent text-white hover:bg-accent-hover shadow-sm'
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
              }`}
              title="Submit query"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* Suggested Topic Pills */}
      <div className="w-full space-y-3">
        <div className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground uppercase tracking-widest font-mono">
          <Sparkles className="w-3.5 h-3.5 text-accent" />
          <span>Explore Corpus Topics</span>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2">
          {SAMPLE_QUERIES.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                onClick={() => {
                  setInput(item.query);
                  onSubmit(item.query);
                }}
                className="group flex items-center gap-2 px-3.5 py-2 rounded-full border border-border bg-surface hover:bg-muted/60 hover:border-border transition-all text-xs text-foreground/90 font-medium"
              >
                <Icon className="w-3.5 h-3.5 text-muted-foreground group-hover:text-accent transition-colors" />
                <span>{item.topic}</span>
                <span className="text-[10px] text-muted-foreground font-mono group-hover:text-foreground">
                  ({item.category})
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Trust Note */}
      <p className="mt-12 text-xs text-muted-foreground max-w-lg leading-relaxed">
        RuleLens checks the official university rules directly. Questions not found in the documents are answered honestly and contradictions are clearly shown.
      </p>
    </div>
  );
};
