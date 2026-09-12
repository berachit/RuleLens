import React from 'react';
import { SystemHealth } from '../types';
import { RefreshCw, ShieldCheck, Moon, Sun } from 'lucide-react';

interface HeaderProps {
  health: SystemHealth | null;
  isConnectionFailed?: boolean;
  onNewChat: () => void;
  hasActiveChat: boolean;
  isDark: boolean;
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  isConnectionFailed,
  onNewChat,
  hasActiveChat,
  isDark,
  onToggleTheme,
}) => {
  const isHealthy = health?.status === 'healthy';
  const isStandalone = health?.status === 'standalone';
  const isDegraded = health?.status === 'degraded';
  const isOnline = isHealthy || isStandalone;

  // Determine user-friendly status badge and color
  let statusText = 'Connecting...';
  let dotColor = 'bg-amber-400 animate-pulse';

  if (isOnline) {
    statusText = 'Ready';
    dotColor = 'bg-emerald-500 animate-pulse';
  } else if (isDegraded) {
    statusText = 'Connected (Limited)';
    dotColor = 'bg-amber-500';
  } else if (isConnectionFailed) {
    statusText = 'Offline';
    dotColor = 'bg-rose-500';
  }

  return (
    <header className="sticky top-0 z-30 w-full border-b border-border bg-background/80 backdrop-blur-md transition-all">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-4">
          <button
            onClick={onNewChat}
            className="text-left group flex items-baseline gap-1 focus:outline-none"
          >
            <span className="font-display text-2xl sm:text-3xl text-foreground font-normal tracking-tight">
               RuleLens
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-accent inline-block transition-transform group-hover:scale-125"></span>
          </button>
          <span className="hidden sm:inline-block text-xs uppercase tracking-wider text-muted-foreground border-l border-border pl-4 font-mono">
            Demo Univ 2026
          </span>
        </div>

        {/* Status Indicators & Controls */}
        <div className="flex items-center gap-3">
          {/* Health status pill */}
          <div
            className="flex items-center gap-2 px-3 py-1 rounded-full text-xs border border-border bg-surface text-muted-foreground font-mono"
            title={isOnline ? 'System is online and ready' : isConnectionFailed ? 'Unable to reach backend' : 'Attempting to establish connection'}
          >
            <span className={`w-2 h-2 rounded-full ${dotColor}`} />
            <span className="hidden md:inline">{statusText}</span>
          </div>

          {/* New Chat Button */}
          {hasActiveChat && (
            <button
              onClick={onNewChat}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-foreground bg-muted hover:bg-muted/80 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>New Query</span>
            </button>
          )}

          {/* Dark Mode Toggle */}
          <button
            onClick={onToggleTheme}
            aria-label="Toggle dark mode"
            title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            className="p-2 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border bg-surface"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>

          {/* Authority reminder */}
          <div className="hidden lg:flex items-center gap-1.5 text-xs text-muted-foreground pl-2">
            <ShieldCheck className="w-3.5 h-3.5 text-accent" />
            <span>Official University Rules</span>
          </div>
        </div>
      </div>
    </header>
  );
};
