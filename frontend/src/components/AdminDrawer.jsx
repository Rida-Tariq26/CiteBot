import React, { useState, useEffect } from 'react';
import {
  X,
  Upload,
  Trash2,
  RefreshCw,
  FileText,
  Sliders,
  BarChart3,
  Code,
  Check,
  AlertCircle
} from 'lucide-react';

const TABS = [
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'branding', label: 'Branding & rules', icon: Sliders },
  { id: 'logs', label: 'Audit & logs', icon: BarChart3 },
  { id: 'widget', label: 'Embed widget', icon: Code }
];

export default function AdminDrawer({
  isOpen,
  onClose,
  config,
  onUpdateConfig,
  documents,
  onUploadDocument,
  onDeleteDocument,
  onReindex,
  adminApiKey
}) {
  const [activeTab, setActiveTab] = useState('documents'); // 'documents' | 'branding' | 'logs' | 'widget'
  const [isUploading, setIsUploading] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);

  // Form State for Branding/Config
  const [formData, setFormData] = useState({
    client_name: config.client_name || '',
    accent_color: config.accent_color || '#2563EB',
    confidence_threshold: config.confidence_threshold ?? 0.45,
    refusal_message: config.refusal_message || '',
    system_tone: config.system_tone || 'precise, helpful, and professional',
    starter_prompts_text: (config.starter_prompts || []).join('\n')
  });

  // Logs state
  const [logsData, setLogsData] = useState({ logs: [], total: 0, refusal_rate: 0, avg_latency_ms: 0 });
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  useEffect(() => {
    if (config) {
      setFormData({
        client_name: config.client_name || '',
        accent_color: config.accent_color || '#2563EB',
        confidence_threshold: config.confidence_threshold ?? 0.45,
        refusal_message: config.refusal_message || '',
        system_tone: config.system_tone || 'precise, helpful, and professional',
        starter_prompts_text: (config.starter_prompts || []).join('\n')
      });
    }
  }, [config]);

  // Fetch logs when tab changes to logs
  useEffect(() => {
    if (isOpen && activeTab === 'logs') {
      fetchLogs();
    }
  }, [isOpen, activeTab]);

  // Escape closes the drawer
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  const fetchLogs = async () => {
    setIsLoadingLogs(true);
    try {
      const res = await fetch('/api/v1/logs', {
        headers: { 'x-admin-key': adminApiKey }
      });
      if (res.ok) {
        const data = await res.json();
        setLogsData(data);
      }
    } catch (e) {
      console.error('Failed to fetch logs:', e);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError('');
    setIsUploading(true);
    try {
      await onUploadDocument(file);
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    const prompts = formData.starter_prompts_text
      .split('\n')
      .map((p) => p.trim())
      .filter(Boolean);

    await onUpdateConfig({
      client_name: formData.client_name,
      accent_color: formData.accent_color,
      confidence_threshold: parseFloat(formData.confidence_threshold),
      refusal_message: formData.refusal_message,
      system_tone: formData.system_tone,
      starter_prompts: prompts
    });
  };

  const handleReindex = async () => {
    if (!window.confirm('Re-index all documents? This will regenerate chunks and embeddings.')) return;
    setIsReindexing(true);
    try {
      await onReindex();
    } finally {
      setIsReindexing(false);
    }
  };

  const embedSnippet = `<script
  src="${window.location.origin}/widget.js"
  data-deployment-id="${config.id || 'default'}"
  data-api-url="${window.location.origin}"
  defer
></script>`;

  const handleCopySnippet = () => {
    navigator.clipboard.writeText(embedSnippet);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  if (!isOpen) return null;

  const statCard = (label, value) => (
    <div className="rounded-2xl border border-hairline bg-white/60 p-3.5 text-center">
      <p className="text-xs text-ink-3">{label}</p>
      <p className="serif mt-0.5 text-2xl font-medium tabular-nums text-ink">{value}</p>
    </div>
  );

  return (
    <div className="fade-in fixed inset-0 z-50 flex justify-end bg-[color-mix(in_srgb,var(--ink)_35%,transparent)] backdrop-blur-[3px]" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="admin-title"
        onClick={(e) => e.stopPropagation()}
        className="glass drawer-in flex h-full w-full max-w-xl flex-col border-l shadow-2xl"
        style={{ background: 'color-mix(in srgb, var(--paper) 90%, white)' }}
      >
        {/* Drawer header */}
        <div className="flex items-center justify-between border-b border-hairline px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg border border-accent-line bg-accent-soft text-accent-text">
              <Sliders className="h-4 w-4" aria-hidden="true" />
            </span>
            <h2 id="admin-title" className="serif text-lg font-medium tracking-tight text-ink">
              CiteBot admin &amp; configuration
            </h2>
          </div>
          <button type="button" onClick={onClose} className="icon-btn" aria-label="Close admin panel">
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {/* Tabs */}
        <div role="tablist" aria-label="Admin sections" className="flex overflow-x-auto border-b border-hairline px-3">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={activeTab === id}
              onClick={() => setActiveTab(id)}
              className="tab"
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              <span>{id === 'documents' ? `${label} (${documents.length})` : label}</span>
            </button>
          ))}
        </div>

        {/* Tab body */}
        <div className="flex-1 overflow-y-auto p-5" role="tabpanel">
          {/* TAB 1: DOCUMENTS */}
          {activeTab === 'documents' && (
            <div className="space-y-6">
              <div>
                <p className="field-label">Upload knowledge documents</p>
                <div className="relative cursor-pointer rounded-2xl border border-dashed border-accent-line p-7 text-center transition focus-within:ring-2 focus-within:ring-accent hover:bg-accent-soft" style={{ background: 'var(--accent-soft)' }}>
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt,.md"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                    aria-label="Upload a PDF, DOCX, Markdown or TXT document"
                    className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                  />
                  <Upload className="mx-auto mb-2 h-7 w-7 text-accent-text" strokeWidth={1.6} aria-hidden="true" />
                  <p className="serif text-base text-ink">
                    {isUploading ? 'Ingesting, chunking & indexing...' : 'Click or drag file to upload'}
                  </p>
                  <p className="mt-1 text-xs text-ink-3">Supports PDF, DOCX, Markdown, and TXT (Max 25MB)</p>
                </div>
                {uploadError && (
                  <p role="alert" className="mt-2 flex items-center text-xs font-medium text-danger">
                    <AlertCircle className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
                    {uploadError}
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between">
                <h3 className="serif text-base font-medium text-ink">Active knowledge files</h3>
                <button
                  type="button"
                  onClick={handleReindex}
                  disabled={isReindexing || documents.length === 0}
                  className="btn-outline"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isReindexing ? 'animate-spin' : ''}`} aria-hidden="true" />
                  <span>{isReindexing ? 'Reindexing...' : 'Reindex all'}</span>
                </button>
              </div>

              <ul className="space-y-2">
                {documents.length === 0 ? (
                  <li className="py-8 text-center text-sm text-ink-3">
                    No documents uploaded yet. Upload policies or manuals above.
                  </li>
                ) : (
                  documents.map((doc) => (
                    <li
                      key={doc.id}
                      className="flex items-center justify-between gap-3 rounded-2xl border border-hairline bg-white/60 p-3 transition hover:bg-white"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-accent-tint text-accent-text">
                          <FileText className="h-4 w-4" aria-hidden="true" />
                        </span>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-ink" title={doc.filename}>
                            {doc.filename}
                          </p>
                          <div className="mt-0.5 flex items-center gap-2 text-xs text-ink-3">
                            <span className="pill capitalize">{doc.status}</span>
                            <span>{doc.chunk_count} chunks</span>
                            <span>{Math.round(doc.file_size_bytes / 1024)} KB</span>
                          </div>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => onDeleteDocument(doc.id)}
                        className="icon-btn hover:!text-danger"
                        title="Delete document"
                        aria-label={`Delete ${doc.filename}`}
                      >
                        <Trash2 className="h-4 w-4" aria-hidden="true" />
                      </button>
                    </li>
                  ))
                )}
              </ul>
            </div>
          )}

          {/* TAB 2: BRANDING & PARAMETERS */}
          {activeTab === 'branding' && (
            <form onSubmit={handleSaveConfig} className="space-y-5">
              <div>
                <label htmlFor="cfg-name" className="field-label">Assistant / client name</label>
                <input
                  id="cfg-name"
                  type="text"
                  value={formData.client_name}
                  onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                  className="field"
                />
              </div>

              <div>
                <label htmlFor="cfg-color" className="field-label">Accent color</label>
                <div className="flex items-center gap-3">
                  <input
                    id="cfg-color"
                    type="color"
                    value={formData.accent_color}
                    onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                    className="h-9 w-9 cursor-pointer rounded-lg border border-hairline bg-transparent p-0.5"
                  />
                  <input
                    type="text"
                    aria-label="Accent color hex value"
                    value={formData.accent_color}
                    onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                    className="field !w-32 tabular-nums"
                  />
                </div>
              </div>

              <div>
                <div className="mb-1 flex items-center justify-between">
                  <label htmlFor="cfg-threshold" className="field-label !mb-0">
                    Confidence threshold ({formData.confidence_threshold})
                  </label>
                  <span className="text-xs text-ink-3">Below this, CiteBot declines</span>
                </div>
                <input
                  id="cfg-threshold"
                  type="range"
                  min="0.10"
                  max="0.80"
                  step="0.05"
                  value={formData.confidence_threshold}
                  onChange={(e) => setFormData({ ...formData, confidence_threshold: e.target.value })}
                  className="w-full"
                  style={{ accentColor: 'var(--accent)' }}
                />
              </div>

              <div>
                <label htmlFor="cfg-refusal" className="field-label">Refusal / insufficient evidence message</label>
                <textarea
                  id="cfg-refusal"
                  rows={3}
                  value={formData.refusal_message}
                  onChange={(e) => setFormData({ ...formData, refusal_message: e.target.value })}
                  className="field"
                />
              </div>

              <div>
                <label htmlFor="cfg-tone" className="field-label">System tone</label>
                <input
                  id="cfg-tone"
                  type="text"
                  value={formData.system_tone}
                  onChange={(e) => setFormData({ ...formData, system_tone: e.target.value })}
                  className="field"
                />
              </div>

              <div>
                <label htmlFor="cfg-starters" className="field-label">Starter questions (one per line)</label>
                <textarea
                  id="cfg-starters"
                  rows={4}
                  value={formData.starter_prompts_text}
                  onChange={(e) => setFormData({ ...formData, starter_prompts_text: e.target.value })}
                  className="field"
                />
              </div>

              <button type="submit" className="btn-primary w-full">
                Save settings
              </button>
            </form>
          )}

          {/* TAB 3: AUDIT & LOGS */}
          {activeTab === 'logs' && (
            <div className="space-y-5" aria-busy={isLoadingLogs}>
              <div className="grid grid-cols-3 gap-2.5">
                {statCard('Total queries', logsData.total)}
                {statCard('Refusal rate', `${Math.round(logsData.refusal_rate * 100)}%`)}
                {statCard('Avg latency', `${logsData.avg_latency_ms} ms`)}
              </div>

              <div className="space-y-2">
                <h3 className="serif text-base font-medium text-ink">Recent query audit trail</h3>
                {logsData.logs.length === 0 ? (
                  <p className="py-6 text-center text-sm text-ink-3">No queries logged yet.</p>
                ) : (
                  logsData.logs.map((log) => (
                    <div key={log.id} className="space-y-1.5 rounded-2xl border border-hairline bg-white/60 p-3.5 text-xs">
                      <div className="flex items-center justify-between gap-3">
                        <span className="max-w-[280px] truncate text-sm font-medium text-ink">
                          "{log.query_text}"
                        </span>
                        <span className={`pill shrink-0 ${log.is_refusal ? 'pill-quiet' : ''}`}>
                          {log.is_refusal ? 'Declined' : `${log.citation_count} cited`}
                        </span>
                      </div>
                      <p className="serif line-clamp-1 italic text-ink-2">{log.response_summary}</p>
                      <div className="flex items-center justify-between pt-0.5 text-ink-3">
                        <span>Score: {log.confidence_score ? Math.round(log.confidence_score * 100) + '%' : 'N/A'}</span>
                        <span>{new Date(log.created_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 4: EMBED WIDGET */}
          {activeTab === 'widget' && (
            <div className="space-y-5">
              <div>
                <h3 className="serif mb-1 text-base font-medium text-ink">Drop-in website widget</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-2">
                  Add this script tag immediately before the closing <code className="rounded bg-hairline px-1 py-0.5 text-xs">&lt;/body&gt;</code> tag on any client website.
                </p>
                <div className="relative">
                  <pre className="overflow-x-auto rounded-2xl p-4 pr-24 text-xs leading-relaxed" style={{ background: 'var(--ink)', color: 'var(--paper)' }}>
                    {embedSnippet}
                  </pre>
                  <button
                    type="button"
                    onClick={handleCopySnippet}
                    className="absolute right-2.5 top-2.5 flex cursor-pointer items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium"
                    style={{ background: 'rgba(255,255,255,0.14)', color: 'var(--paper)' }}
                  >
                    {copySuccess ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Code className="h-3.5 w-3.5" aria-hidden="true" />}
                    <span>{copySuccess ? 'Copied!' : 'Copy'}</span>
                  </button>
                </div>
              </div>

              <div className="rounded-2xl border border-accent-line p-4 text-sm" style={{ background: 'var(--accent-soft)' }}>
                <p className="serif mb-1.5 font-medium text-ink">Widget features</p>
                <ul className="list-inside list-disc space-y-1 text-xs leading-relaxed text-ink-2">
                  <li>Zero build steps: standalone vanilla JavaScript bundle</li>
                  <li>Opens an expandable chat popup with source verification chips</li>
                  <li>Adheres to the same confidence gating and zero-hallucination rules</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
