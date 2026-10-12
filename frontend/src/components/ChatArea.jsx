import React, { useState, useRef, useEffect } from 'react';
import { Send, FileSearch, ArrowUpRight, ShieldCheck, GitCompare } from 'lucide-react';
import CitationChip from './CitationChip';

export default function ChatArea({
  messages,
  isLoading,
  streamingContent,
  onSendMessage,
  starterPrompts,
  clientName,
  onSelectCitation,
  activeCitationNum,
  documentCount
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent, isLoading]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  /**
   * Helper to parse inline citation markers e.g. [1], [2] into interactive CitationChips
   */
  const renderMessageContent = (content, citations) => {
    if (!content) return null;

    const parts = [];
    const regex = /\[(\d+)\]/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(content)) !== null) {
      const matchIndex = match.index;
      const citeNum = parseInt(match[1], 10);

      if (matchIndex > lastIndex) {
        parts.push(content.substring(lastIndex, matchIndex));
      }

      const citationObj = citations?.find((c) => c.citation_number === citeNum);
      parts.push(
        <CitationChip
          key={`chip-${matchIndex}-${citeNum}`}
          num={citeNum}
          citation={citationObj}
          isActive={activeCitationNum === citeNum}
          onClick={(num) => onSelectCitation(num, citations)}
        />
      );

      lastIndex = matchIndex + match[0].length;
    }

    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex));
    }

    return parts;
  };

  return (
    <div className="relative flex h-full min-w-0 flex-1 flex-col overflow-hidden">
      {/* Scrollable message feed */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8" role="log" aria-live="polite" aria-label="Conversation">
        <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col gap-7">
          {messages.length === 0 ? (
            /* Welcome / empty state */
            <div className="my-auto flex flex-col items-center py-8 text-center">
              <div className="mb-6 grid h-12 w-12 place-items-center rounded-2xl border border-accent-line bg-accent-soft text-accent-text shadow-soft">
                <ShieldCheck className="h-6 w-6" strokeWidth={1.8} aria-hidden="true" />
              </div>

              <h2 className="serif max-w-xl text-balance text-[2rem] font-normal leading-[1.15] tracking-tight text-ink md:text-[2.6rem]">
                Welcome to {clientName}
              </h2>
              <p className="mt-4 max-w-md text-[0.95rem] leading-relaxed text-ink-2">
                Ask any question about our verified policies and handbooks. Every factual sentence is backed by a clickable citation.
              </p>

              {documentCount === 0 ? (
                <div className="note-card mt-10 max-w-md p-4 text-left text-sm leading-relaxed text-ink-2">
                  No documents are loaded yet. Open the <strong className="text-ink">Admin panel</strong> in the top-right to upload your company's documents.
                </div>
              ) : (
                <div className="mt-10 w-full text-left">
                  <p className="small-label mb-3">Suggested questions</p>
                  <ul className="grid grid-cols-1 gap-2.5">
                    {starterPrompts?.map((prompt, idx) => (
                      <li key={idx}>
                        <button
                          type="button"
                          onClick={() => onSendMessage(prompt)}
                          className="shadow-soft group flex w-full cursor-pointer items-center justify-between gap-4 rounded-2xl border border-hairline bg-white/70 px-5 py-4 text-left transition hover:border-accent-line hover:bg-white"
                        >
                          <span className="serif text-[1.02rem] leading-snug text-ink">{prompt}</span>
                          <ArrowUpRight
                            className="h-4 w-4 shrink-0 text-ink-3 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-accent-text"
                            aria-hidden="true"
                          />
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`fade-in flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div className="mb-1.5 flex items-center gap-2 px-1">
                  <span className="text-xs font-semibold text-ink-3">
                    {msg.role === 'user' ? 'You' : 'CiteBot'}
                  </span>
                  {msg.role === 'assistant' && msg.confidence_score && (
                    <span className="rounded-full border border-hairline px-2 py-px text-[0.6875rem] tabular-nums text-ink-3">
                      {Math.round(msg.confidence_score * 100)}% confidence
                    </span>
                  )}
                </div>

                {msg.is_refusal ? (
                  /* Calm, informative decline state */
                  <div className="note-card flex max-w-xl items-start gap-3.5 p-4 md:p-5">
                    <FileSearch className="mt-0.5 h-5 w-5 shrink-0 text-accent-text" strokeWidth={1.8} aria-hidden="true" />
                    <div className="space-y-1">
                      <p className="serif text-[1.02rem] font-medium text-ink">Not found in the documents</p>
                      <p className="text-sm leading-relaxed text-ink-2">{msg.content}</p>
                    </div>
                  </div>
                ) : (
                  <div
                    className={`max-w-[92%] px-4 py-3 text-[0.9375rem] leading-relaxed md:max-w-2xl md:px-5 md:py-3.5 ${
                      msg.role === 'user' ? 'bubble-user' : 'bubble-ai shadow-soft'
                    }`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="space-y-2.5">
                        <div className="whitespace-pre-wrap">
                          {renderMessageContent(msg.content, msg.citations)}
                        </div>

                        {/* Conflict note if multiple conflicting sources */}
                        {msg.content?.toLowerCase().includes('differing') && (
                          <div className="flex items-center gap-1.5 border-t border-hairline pt-2.5 text-xs font-medium text-accent-text">
                            <GitCompare className="h-3.5 w-3.5" aria-hidden="true" />
                            Differing policy positions surfaced from distinct sources
                          </div>
                        )}

                        {/* Citation summary */}
                        {msg.citations?.length > 0 && (
                          <div className="flex items-center justify-between border-t border-hairline pt-2.5 text-xs text-ink-3">
                            <span>
                              {msg.citations.length} cited {msg.citations.length === 1 ? 'passage' : 'passages'}
                            </span>
                            <button
                              type="button"
                              onClick={() => onSelectCitation(msg.citations[0].citation_number, msg.citations)}
                              className="cursor-pointer font-semibold text-accent-text underline-offset-4 hover:underline"
                            >
                              Inspect evidence
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {msg.role === 'user' && <div className="whitespace-pre-wrap">{msg.content}</div>}
                  </div>
                )}
              </div>
            ))
          )}

          {/* Searching / streaming indicator */}
          {isLoading && (
            <div className="fade-in flex flex-col items-start" aria-busy="true">
              <span className="mb-1.5 px-1 text-xs font-semibold text-ink-3">CiteBot</span>
              {streamingContent ? (
                <div className="bubble-ai shadow-soft max-w-[92%] px-4 py-3 text-[0.9375rem] leading-relaxed md:max-w-2xl md:px-5 md:py-3.5">
                  <div className="whitespace-pre-wrap">
                    {streamingContent}
                    <span className="caret" aria-hidden="true" />
                  </div>
                </div>
              ) : (
                <div className="bubble-ai flex items-center gap-3 px-4 py-3">
                  <span className="flex items-center gap-1" aria-hidden="true">
                    <span className="search-dot" />
                    <span className="search-dot" style={{ animationDelay: '160ms' }} />
                    <span className="search-dot" style={{ animationDelay: '320ms' }} />
                  </span>
                  <span className="shimmer-text text-sm">Searching documents &amp; verifying evidence...</span>
                </div>
              )}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Frosted input bar */}
      <div className="glass shrink-0 border-t px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 md:px-8">
        <form onSubmit={handleSubmit} className="relative mx-auto flex max-w-3xl items-center">
          <label htmlFor="citebot-input" className="sr-only">
            Ask a question about the uploaded documents
          </label>
          <input
            id="citebot-input"
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading || documentCount === 0}
            placeholder={
              documentCount === 0
                ? 'Upload documents in Admin panel to start querying...'
                : 'Ask a question about the uploaded documents...'
            }
            className="field shadow-soft !rounded-2xl !py-3.5 !pl-5 !pr-14 !text-[0.9375rem] placeholder:text-ink-3 disabled:cursor-not-allowed disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading || documentCount === 0}
            className="btn-primary absolute right-2 !h-9 !w-9 !rounded-xl !p-0"
            title="Send query"
            aria-label="Send query"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
          </button>
        </form>
        <div className="mx-auto mt-2 flex max-w-3xl items-center justify-between px-1 text-xs text-ink-3">
          <span>
            Press <kbd className="font-sans font-semibold text-ink-2">Enter</kbd> to send
          </span>
          <span className="hidden sm:inline">Zero hallucinations • 100% cited or declined</span>
        </div>
      </div>
    </div>
  );
}
