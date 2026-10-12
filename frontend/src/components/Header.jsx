import React from 'react';
import { Layers, Settings, PlusCircle, BookOpen } from 'lucide-react';

export default function Header({
  clientName,
  logoUrl,
  documentCount,
  onNewChat,
  onOpenAdmin,
  isSourcePanelOpen,
  onToggleSourcePanel
}) {
  return (
    <header className="glass relative z-30 flex h-16 shrink-0 select-none items-center justify-between gap-3 border-b px-4 md:px-8">
      {/* Brand & client name */}
      <div className="flex min-w-0 items-center gap-3">
        <div className="brand-mark">
          {logoUrl ? (
            <img src={logoUrl} alt="" className="h-full w-full object-contain" />
          ) : (
            <BookOpen className="h-4 w-4" strokeWidth={2.4} aria-hidden="true" />
          )}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="serif truncate text-[1.1rem] font-medium leading-tight tracking-tight text-ink">
              {clientName || 'CiteBot Assistant'}
            </h1>
            <span className="hidden rounded-full border border-accent-line bg-accent-soft px-2 py-0.5 text-[0.6875rem] font-semibold text-accent-text sm:inline">
              Verified RAG
            </span>
          </div>
          <p className="flex items-center gap-1.5 text-xs text-ink-3">
            <Layers className="h-3 w-3" aria-hidden="true" />
            {documentCount} {documentCount === 1 ? 'active document' : 'active documents'}
          </p>
        </div>
      </div>

      {/* Actions */}
      <nav className="flex shrink-0 items-center gap-1" aria-label="Actions">
        <button type="button" onClick={onNewChat} className="btn" title="Start fresh conversation">
          <PlusCircle className="h-3.5 w-3.5" aria-hidden="true" />
          <span className="hidden sm:inline">New chat</span>
        </button>
        <button
          type="button"
          onClick={onToggleSourcePanel}
          aria-pressed={isSourcePanelOpen}
          className="btn"
          title="Toggle source evidence panel"
        >
          <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
          <span className="hidden sm:inline">Sources</span>
        </button>
        <button type="button" onClick={onOpenAdmin} className="btn" title="Admin panel and document management">
          <Settings className="h-3.5 w-3.5" aria-hidden="true" />
          <span className="hidden sm:inline">Admin</span>
        </button>
      </nav>
    </header>
  );
}
