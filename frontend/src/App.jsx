import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatArea from './components/ChatArea';
import SourcePanel from './components/SourcePanel';
import AdminDrawer from './components/AdminDrawer';

const ADMIN_API_KEY = 'citebot-admin-secret-key-change-me';

// Picks a readable text colour (dark or light) for content placed on the accent colour.
const inkFor = (hex) => {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || '');
  if (!m) return '#ffffff';
  const n = parseInt(m[1], 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.179 ? '#17140f' : '#ffffff';
};

export default function App() {
  const [config, setConfig] = useState({
    id: 'default',
    client_name: 'Acme Knowledge Base',
    accent_color: '#2563EB',
    confidence_threshold: 0.45,
    refusal_message: "I couldn't find this information in the uploaded documents. Please try rephrasing or refer directly to your organization's documentation.",
    system_tone: 'precise, helpful, and professional',
    starter_prompts: [
      "What is the home office equipment stipend amount and what does it cover?",
      "How many weeks of paid parental leave are offered, and who qualifies?",
      "What are the expense approval thresholds for staff vs contractors?"
    ],
    active_document_count: 0
  });

  const [documents, setDocuments] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [currentCitations, setCurrentCitations] = useState([]);
  const [activeCitationNum, setActiveCitationNum] = useState(null);
  const [isSourcePanelOpen, setIsSourcePanelOpen] = useState(true);
  const [isAdminOpen, setIsAdminOpen] = useState(false);

  // Load public config & document list on startup
  useEffect(() => {
    loadConfig();
    loadDocuments();
  }, []);

  // Update CSS dynamic accent color
  useEffect(() => {
    if (config.accent_color) {
      const root = document.documentElement.style;
      root.setProperty('--accent', config.accent_color);
      root.setProperty('--accent-ink', inkFor(config.accent_color));
      root.setProperty('--brand-600', config.accent_color);
    }
  }, [config.accent_color]);

  const loadConfig = async () => {
    try {
      const res = await fetch('/api/v1/config');
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (e) {
      console.error('Failed to load config:', e);
    }
  };

  const loadDocuments = async () => {
    try {
      const res = await fetch('/api/v1/documents');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (e) {
      console.error('Failed to load documents:', e);
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
    setCurrentCitations([]);
    setActiveCitationNum(null);
    setStreamingContent('');
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setStreamingContent('');
    setActiveCitationNum(null);

    try {
      // Use SSE streaming endpoint
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
          deployment_id: config.id
        })
      });

      if (!response.ok) {
        throw new Error(`Chat error: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedText = '';
      let receivedCitations = [];
      let activeConvId = conversationId;
      let isRefusal = false;
      let confScore = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          const [eventPart, dataPart] = line.split('\n');
          const eventType = eventPart ? eventPart.replace('event: ', '').trim() : '';
          const eventData = dataPart ? JSON.parse(dataPart.replace('data: ', '').trim()) : {};

          if (eventType === 'session') {
            activeConvId = eventData.conversation_id;
            setConversationId(activeConvId);
          } else if (eventType === 'delta') {
            accumulatedText += eventData.delta;
            setStreamingContent(accumulatedText);
          } else if (eventType === 'citations') {
            receivedCitations = eventData.citations || [];
            isRefusal = eventData.is_refusal || false;
            confScore = eventData.confidence_score;
          }
        }
      }

      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: accumulatedText,
        citations: receivedCitations,
        is_refusal: isRefusal,
        confidence_score: confScore
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setCurrentCitations(receivedCitations);
      if (receivedCitations.length > 0) {
        setIsSourcePanelOpen(true);
        setActiveCitationNum(receivedCitations[0].citation_number);
      }
    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: "An error occurred while communicating with the knowledge service. Please try again.",
        is_refusal: true,
        citations: []
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setStreamingContent('');
    }
  };

  const handleSelectCitation = (num, citations) => {
    if (citations) setCurrentCitations(citations);
    setActiveCitationNum(num);
    setIsSourcePanelOpen(true);
  };

  const handleUploadDocument = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('deployment_id', config.id);

    const res = await fetch('/api/v1/documents', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    await loadDocuments();
    await loadConfig();
  };

  const handleDeleteDocument = async (docId) => {
    if (!window.confirm('Delete this document and all its indexed chunks?')) return;
    const res = await fetch(`/api/v1/documents/${docId}?deployment_id=${config.id}`, {
      method: 'DELETE',
      headers: { 'x-admin-key': ADMIN_API_KEY }
    });
    if (res.ok) {
      await loadDocuments();
      await loadConfig();
    }
  };

  const handleReindex = async () => {
    const res = await fetch(`/api/v1/documents/reindex?deployment_id=${config.id}`, {
      method: 'POST',
      headers: { 'x-admin-key': ADMIN_API_KEY }
    });
    if (res.ok) {
      await loadDocuments();
    }
  };

  const handleUpdateConfig = async (newConfig) => {
    const res = await fetch(`/api/v1/config?deployment_id=${config.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'x-admin-key': ADMIN_API_KEY
      },
      body: JSON.stringify(newConfig)
    });
    if (res.ok) {
      const updated = await res.json();
      setConfig(updated);
      alert('Configuration updated successfully!');
    }
  };

  return (
    <div className="app-shell">
      {/* Top Navbar */}
      <Header
        clientName={config.client_name}
        logoUrl={config.logo_url}
        documentCount={documents.length}
        onNewChat={handleNewChat}
        onOpenAdmin={() => setIsAdminOpen(true)}
        isSourcePanelOpen={isSourcePanelOpen}
        onToggleSourcePanel={() => setIsSourcePanelOpen(!isSourcePanelOpen)}
      />

      {/* Main Workspace (Two-pane layout) */}
      <div className="flex-1 flex overflow-hidden relative">
        <ChatArea
          messages={messages}
          isLoading={isLoading}
          streamingContent={streamingContent}
          onSendMessage={handleSendMessage}
          starterPrompts={config.starter_prompts}
          clientName={config.client_name}
          onSelectCitation={handleSelectCitation}
          activeCitationNum={activeCitationNum}
          documentCount={documents.length}
        />

        <SourcePanel
          citations={currentCitations}
          activeCitationNum={activeCitationNum}
          onSelectCitation={(num) => setActiveCitationNum(num)}
          isOpen={isSourcePanelOpen}
          onClose={() => setIsSourcePanelOpen(false)}
        />
      </div>

      {/* Admin Slide-Over Drawer */}
      <AdminDrawer
        isOpen={isAdminOpen}
        onClose={() => setIsAdminOpen(false)}
        config={config}
        onUpdateConfig={handleUpdateConfig}
        documents={documents}
        onUploadDocument={handleUploadDocument}
        onDeleteDocument={handleDeleteDocument}
        onReindex={handleReindex}
        adminApiKey={ADMIN_API_KEY}
      />
    </div>
  );
}
