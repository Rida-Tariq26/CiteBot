import React, { useEffect, useRef } from 'react';
import { FileText, CheckCircle2, X } from 'lucide-react';

export default function SourcePanel({
  citations,
  activeCitationNum,
  onSelectCitation,
  isOpen,
  onClose
}) {
  const cardRefs = useRef({});

  // Auto-scroll to selected citation card
  useEffect(() => {
    if (activeCitationNum && cardRefs.current[activeCitationNum]) {
      cardRefs.current[activeCitationNum].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  }, [activeCitationNum]);

  // Escape closes the panel / sheet
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const hasCitations = citations.length > 0;

  return (
    <>
      {/* Mobile backdrop (the panel is a bottom sheet below md) */}
      {hasCitations && (
        <div
          className="fade-in fixed inset-0 z-30 bg-[color-mix(in_srgb,var(--ink)_30%,transparent)] backdrop-blur-[2px] md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        aria-label="Source evidence"
        className={`glass sheet-in shadow-soft fixed inset-x-0 bottom-0 z-40 max-h-[80dvh] flex-col rounded-t-[1.75rem] border-t md:static md:z-20 md:h-full md:max-h-none md:w-96 md:rounded-none md:border-l md:border-t-0 lg:w-[26rem] ${
          hasCitations ? 'flex' : 'hidden md:flex'
        }`}
      >
        {/* Grab handle (mobile) */}
        <div className="flex justify-center pt-2.5 md:hidden" aria-hidden="true">
          <span className="h-1 w-10 rounded-full bg-hairline" style={{ background: 'var(--hairline-strong)' }} />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between gap-3 border-b border-hairline px-5 pb-3 pt-3 md:py-4">
          <div className="flex items-baseline gap-2.5">
            <h2 className="serif text-[1.1rem] font-medium tracking-tight text-ink">Source evidence</h2>
            <span className="pill">
              {citations.length} {citations.length === 1 ? 'source' : 'sources'}
            </span>
          </div>
          <button type="button" onClick={onClose} className="icon-btn" title="Close panel" aria-label="Close source panel">
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3.5 overflow-y-auto p-4 md:p-5">
          {citations.length === 0 ? (
            <div className="flex h-full min-h-[14rem] flex-col items-center justify-center p-6 text-center">
              <FileText className="mb-3 h-9 w-9 text-ink-3 opacity-60" strokeWidth={1.2} aria-hidden="true" />
              <p className="serif text-base text-ink">No citations for this turn</p>
              <p className="mt-1 max-w-[230px] text-xs leading-relaxed text-ink-3">
                Ask a question to see exact document excerpts and verification references.
              </p>
            </div>
          ) : (
            citations.map((cite) => {
              const isSelected = activeCitationNum === cite.citation_number;
              const select = () => onSelectCitation(cite.citation_number);
              return (
                <article
                  key={cite.citation_number}
                  ref={(el) => (cardRefs.current[cite.citation_number] = el)}
                  role="button"
                  tabIndex={0}
                  aria-current={isSelected}
                  aria-label={`Source ${cite.citation_number}: ${cite.document_name}`}
                  onClick={select}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      select();
                    }
                  }}
                  className={`source-card ${isSelected ? 'excerpt-active' : ''}`}
                >
                  {/* Document header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 items-start gap-2.5">
                      <span
                        className={`mt-0.5 inline-flex h-5 min-w-5 shrink-0 items-center justify-center rounded-md px-1 text-[0.6875rem] font-bold tabular-nums ${
                          isSelected ? 'bg-accent text-accent-ink' : 'border border-accent-line bg-accent-tint text-accent-text'
                        }`}
                      >
                        {cite.citation_number}
                      </span>
                      <div className="min-w-0">
                        <h3 className="serif truncate text-[0.95rem] font-medium leading-snug text-ink" title={cite.document_name}>
                          {cite.document_name}
                        </h3>
                        {(cite.page_number || cite.section_heading) && (
                          <p className="mt-0.5 text-xs text-ink-3">
                            {cite.page_number && <span>Page {cite.page_number}</span>}
                            {cite.page_number && cite.section_heading && <span aria-hidden="true">, </span>}
                            {cite.section_heading && (
                              <span title={cite.section_heading}>§ {cite.section_heading}</span>
                            )}
                          </p>
                        )}
                      </div>
                    </div>

                    {cite.similarity_score !== null && (
                      <span className="pill pill-quiet shrink-0 tabular-nums">
                        {Math.round(cite.similarity_score * 100)}% match
                      </span>
                    )}
                  </div>

                  {/* Excerpt, with the cited passage marked */}
                  <blockquote className="serif mt-3.5 border-l border-hairline pl-4 text-[0.9rem] leading-[1.75] text-ink-2" style={{ borderColor: 'var(--hairline-strong)' }}>
                    <span aria-hidden="true">“</span>
                    <mark className="marker">{cite.excerpt}</mark>
                    <span aria-hidden="true">”</span>
                  </blockquote>

                  <p className="mt-3 flex items-center gap-1.5 text-xs font-medium text-ink-3">
                    <CheckCircle2 className="h-3.5 w-3.5 text-accent-text" aria-hidden="true" />
                    Verified source passage
                  </p>
                </article>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-hairline px-4 py-3 text-center text-xs text-ink-3">
          Zero general-knowledge hallucinations • 100% cited
        </div>
      </aside>
    </>
  );
}
