import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, Search, Plus, Compass, Loader2, Download, Table, 
  MessageSquare, BookOpen, Layers, Award, Code, CheckCircle, 
  HelpCircle, Settings, Users, ArrowRight, Copy, Terminal,
  ExternalLink, Sparkles, FileSpreadsheet, Trash
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [papers, setPapers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [activeAgentLogs, setActiveAgentLogs] = useState([]);
  const [activePlan, setActivePlan] = useState([]);
  
  // Literature Review state
  const [selectedPapersForReview, setSelectedPapersForReview] = useState([]);
  const [reviewTitle, setReviewTitle] = useState('Literature Review on Deep Learning');
  const [generatedReview, setGeneratedReview] = useState('');
  const [reviewLoading, setReviewLoading] = useState(false);
  
  // Comparison state
  const [selectedPapersForCompare, setSelectedPapersForCompare] = useState([]);
  const [comparisonTable, setComparisonTable] = useState('');
  const [comparisonLoading, setComparisonLoading] = useState(false);

  // Presentation State
  const [presentationTopic, setPresentationTopic] = useState('Research Presentation');
  const [generatedSlides, setGeneratedSlides] = useState('');
  const [slidesLoading, setSlidesLoading] = useState(false);

  // File Upload
  const [uploadFiles, setUploadFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  // Loaders
  const [fetchingPapers, setFetchingPapers] = useState(false);

  const API_BASE = 'http://localhost:8000/api';

  // Load initial data
  useEffect(() => {
    fetchPapers();
    fetchSessions();
  }, []);

  useEffect(() => {
    if (activeSession) {
      fetchMessages(activeSession.id);
    }
  }, [activeSession]);

  const fetchPapers = async () => {
    setFetchingPapers(true);
    try {
      const res = await fetch(`${API_BASE}/papers`);
      if (res.ok) {
        const data = await res.json();
        setPapers(data);
      }
    } catch (err) {
      console.error("Failed to fetch papers:", err);
    } finally {
      setFetchingPapers(false);
    }
  };

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0 && !activeSession) {
          setActiveSession(data[0]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
    }
  };

  const createSession = async () => {
    try {
      const sessionName = prompt("Enter a name for the new session:", `Research Session ${sessions.length + 1}`);
      if (!sessionName) return;
      
      const res = await fetch(`${API_BASE}/sessions?name=${encodeURIComponent(sessionName)}`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(prev => [data, ...prev]);
        setActiveSession(data);
        setMessages([]);
        setActivePlan([]);
        setActiveAgentLogs([]);
      }
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  };

  const fetchMessages = async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
        // Find last orchestrator logs
        const lastAssistantMsg = [...data].reverse().find(m => m.role === 'assistant');
        if (lastAssistantMsg && lastAssistantMsg.step_logs) {
          setActiveAgentLogs(lastAssistantMsg.step_logs);
        } else {
          setActiveAgentLogs([]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch messages:", err);
    }
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const res = await fetch(`${API_BASE}/papers/upload`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const newPapers = await res.json();
        alert(`Successfully uploaded and indexed ${newPapers.length} papers!`);
        fetchPapers();
      } else {
        const errorData = await res.json();
        alert(`Upload failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Upload error:", err);
      alert("An error occurred during file upload.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const sendChatMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || !activeSession) return;

    const userMsg = inputValue;
    setInputValue('');
    setChatLoading(true);

    // Optimistically update chat
    setMessages(prev => [...prev, { role: 'user', content: userMsg, created_at: new Date().toISOString() }]);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSession.id,
          message: userMsg,
          paper_ids: papers.map(p => p.id) // Query all uploaded papers in workspace by default
        })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.answer,
          created_at: new Date().toISOString()
        }]);
        setActivePlan(data.plan || []);
        setActiveAgentLogs(data.logs || []);
      }
    } catch (err) {
      console.error("Chat error:", err);
    } finally {
      setChatLoading(false);
    }
  };

  const generateLiteratureReview = async () => {
    if (selectedPapersForReview.length === 0) {
      alert("Please select at least one paper.");
      return;
    }
    setReviewLoading(true);
    try {
      const res = await fetch(`${API_BASE}/literature-review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSession?.id || "temp",
          title: reviewTitle,
          paper_ids: selectedPapersForReview
        })
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedReview(data.content);
      }
    } catch (err) {
      console.error("Lit review error:", err);
    } finally {
      setReviewLoading(false);
    }
  };

  const comparePapers = async () => {
    if (selectedPapersForCompare.length === 0) {
      alert("Please select at least one paper to compare.");
      return;
    }
    setComparisonLoading(true);
    try {
      const res = await fetch(`${API_BASE}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSession?.id || "temp",
          paper_ids: selectedPapersForCompare
        })
      });
      if (res.ok) {
        const data = await res.json();
        setComparisonTable(data.comparisons);
      }
    } catch (err) {
      console.error("Comparison error:", err);
    } finally {
      setComparisonLoading(false);
    }
  };

  const exportReport = async (title, content, format) => {
    try {
      const res = await fetch(`${API_BASE}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          content,
          format
        })
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/\s+/g, '_')}.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (err) {
      console.error("Export error:", err);
    }
  };

  // Helper to copy text to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  // Simple page layout styling
  const mainStyle = {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    backgroundColor: 'var(--bg-base)',
    overflow: 'hidden'
  };

  return (
    <div style={mainStyle}>
      {/* SIDEBAR */}
      <div style={{
        width: '280px',
        backgroundColor: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0
      }}>
        {/* LOGO */}
        <div style={{
          padding: '24px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          borderBottom: '1px solid var(--border)',
          background: 'linear-gradient(180deg, rgba(99,102,241,0.05) 0%, transparent 100%)'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'var(--primary-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
          }}>
            <Compass size={22} color="#fff" />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: '800', tracking: 'wide' }} className="gradient-text">ResearchPilot AI</h1>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Multi-Agent System</span>
          </div>
        </div>

        {/* NAVIGATION */}
        <nav style={{ padding: '20px 12px', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button 
            onClick={() => setActiveTab('dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              textAlign: 'left',
              color: activeTab === 'dashboard' ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: activeTab === 'dashboard' ? 'var(--bg-glass-active)' : 'transparent',
              border: activeTab === 'dashboard' ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent'
            }}
          >
            <Layers size={18} color={activeTab === 'dashboard' ? '#6366f1' : '#cbd5e1'} />
            Dashboard & Library
          </button>
          
          <button 
            onClick={() => setActiveTab('chat')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              textAlign: 'left',
              color: activeTab === 'chat' ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: activeTab === 'chat' ? 'var(--bg-glass-active)' : 'transparent',
              border: activeTab === 'chat' ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent'
            }}
          >
            <MessageSquare size={18} color={activeTab === 'chat' ? '#6366f1' : '#cbd5e1'} />
            Agent Workspace
          </button>

          <button 
            onClick={() => setActiveTab('literature')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              textAlign: 'left',
              color: activeTab === 'literature' ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: activeTab === 'literature' ? 'var(--bg-glass-active)' : 'transparent',
              border: activeTab === 'literature' ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent'
            }}
          >
            <BookOpen size={18} color={activeTab === 'literature' ? '#6366f1' : '#cbd5e1'} />
            Literature Review
          </button>

          <button 
            onClick={() => setActiveTab('compare')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              textAlign: 'left',
              color: activeTab === 'compare' ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: activeTab === 'compare' ? 'var(--bg-glass-active)' : 'transparent',
              border: activeTab === 'compare' ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent'
            }}
          >
            <Table size={18} color={activeTab === 'compare' ? '#6366f1' : '#cbd5e1'} />
            Paper Comparison
          </button>

          <button 
            onClick={() => setActiveTab('citations')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              textAlign: 'left',
              color: activeTab === 'citations' ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: activeTab === 'citations' ? 'var(--bg-glass-active)' : 'transparent',
              border: activeTab === 'citations' ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent'
            }}
          >
            <Award size={18} color={activeTab === 'citations' ? '#6366f1' : '#cbd5e1'} />
            Citations Manager
          </button>

          <div style={{ marginTop: 'auto', paddingTop: '20px', borderTop: '1px solid var(--border)' }}>
            <div style={{
              padding: '12px',
              borderRadius: '8px',
              background: 'rgba(255,255,255,0.03)',
              fontSize: '12px',
              color: 'var(--text-secondary)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent)', fontWeight: '600', marginBottom: '4px' }}>
                <Terminal size={14} />
                Sandbox Status
              </div>
              <p style={{ color: 'var(--text-muted)' }}>Local Simulation mode active. Running offline with mock LLM outputs.</p>
            </div>
          </div>
        </nav>
      </div>

      {/* MAIN CONTAINER */}
      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* HEADER BAR */}
        <header style={{
          height: '70px',
          borderBottom: '1px solid var(--border)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(13, 18, 32, 0.4)',
          backdropFilter: 'blur(8px)',
          flexShrink: 0
        }}>
          <div>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>ACTIVE WORKSPACE</span>
            <h2 style={{ fontSize: '16px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} color="#06b6d4" />
              Local Capstone Library
            </h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              style={{ display: 'none' }} 
              multiple 
              accept=".pdf"
            />
            
            <button 
              onClick={() => fileInputRef.current.click()}
              style={{
                background: 'var(--primary-gradient)',
                color: '#fff',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.25)'
              }}
              disabled={uploading}
            >
              {uploading ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
              Upload PDF Research
            </button>
          </div>
        </header>

        {/* CONTENT CHANGER */}
        <main style={{ flexGrow: 1, overflowY: 'auto', padding: '24px' }}>
          
          {/* TAB: DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* STATUS WIDGETS */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
                <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '10px', background: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyCenter: 'center', flexShrink: 0 }}>
                    <FileText size={24} color="#6366f1" style={{ margin: 'auto' }} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '20px', fontWeight: '800' }}>{papers.length}</h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Indexed Papers</p>
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '10px', background: 'rgba(6,182,212,0.1)', display: 'flex', alignItems: 'center', justifyCenter: 'center', flexShrink: 0 }}>
                    <Users size={24} color="#06b6d4" style={{ margin: 'auto' }} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '20px', fontWeight: '800' }}>10</h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Specialist AI Agents</p>
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '10px', background: 'rgba(16,185,129,0.1)', display: 'flex', alignItems: 'center', justifyCenter: 'center', flexShrink: 0 }}>
                    <CheckCircle size={24} color="#10b981" style={{ margin: 'auto' }} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '20px', fontWeight: '800' }}>Offline Ready</h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Security Safe Sandbox</p>
                  </div>
                </div>
              </div>

              {/* LIBRARY SECTION */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Document Library</h3>
                
                {fetchingPapers ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
                    <Loader2 className="animate-spin" color="#6366f1" size={32} />
                  </div>
                ) : papers.length === 0 ? (
                  <div style={{
                    padding: '48px',
                    textAlign: 'center',
                    border: '2px dashed var(--border)',
                    borderRadius: '8px',
                    color: 'var(--text-muted)'
                  }}>
                    <FileSpreadsheet size={48} style={{ margin: '0 auto 16px auto', display: 'block' }} />
                    <p style={{ fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '8px' }}>Your Library is Empty</p>
                    <p style={{ fontSize: '13px', marginBottom: '16px' }}>Upload your first research papers (PDF) to begin semantic querying.</p>
                    <button 
                      onClick={() => fileInputRef.current.click()}
                      style={{
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        color: '#a5b4fc',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        fontSize: '13px'
                      }}
                    >
                      Browse PDF Files
                    </button>
                  </div>
                ) : (
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {papers.map(p => (
                      <div key={p.id} style={{
                        padding: '16px',
                        borderRadius: '8px',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        gap: '16px'
                      }}>
                        <div style={{ flexGrow: 1 }}>
                          <h4 style={{ fontWeight: '600', fontSize: '15px', color: 'var(--text-primary)', marginBottom: '4px' }}>{p.title}</h4>
                          <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                            <span><b>Authors:</b> {p.authors}</span>
                            <span><b>Year:</b> {p.year || 'N/A'}</span>
                            <span><b>File:</b> {p.file_name}</span>
                          </div>
                          {p.abstract && (
                            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '8px', background: 'rgba(0,0,0,0.15)', padding: '8px', borderRadius: '6px' }}>
                              <b>Abstract:</b> {p.abstract.substring(0, 300)}...
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB: CHAT / WORKSPACE */}
          {activeTab === 'chat' && (
            <div className="animate-fade-in" style={{ display: 'flex', gap: '24px', height: 'calc(100vh - 140px)' }}>
              
              {/* CHAT INTERFACE */}
              <div className="glass-panel" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                {/* Chat Session Picker */}
                <div style={{
                  padding: '12px 16px',
                  borderBottom: '1px solid var(--border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Session:</span>
                    <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>{activeSession?.name || 'Loading...'}</strong>
                  </div>
                  <button 
                    onClick={createSession}
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--border)',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Plus size={14} /> New Session
                  </button>
                </div>

                {/* Messages List */}
                <div style={{ flexGrow: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {messages.length === 0 ? (
                    <div style={{ margin: 'auto', textAlign: 'center', maxWidth: '400px', color: 'var(--text-muted)' }}>
                      <Compass size={36} style={{ margin: '0 auto 12px auto' }} />
                      <h4 style={{ color: 'var(--text-primary)', marginBottom: '4px' }}>Multi-Agent Workspace</h4>
                      <p style={{ fontSize: '13px' }}>Ask research questions. The multi-agent planner will delegate steps to retrieval, code, presentation, and synthesis agents.</p>
                    </div>
                  ) : (
                    messages.map((m, i) => (
                      <div key={i} style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: m.role === 'user' ? 'flex-end' : 'flex-start',
                        gap: '6px'
                      }}>
                        <div style={{
                          maxWidth: '80%',
                          padding: '12px 16px',
                          borderRadius: '12px',
                          fontSize: '14px',
                          lineHeight: '1.5',
                          background: m.role === 'user' ? 'var(--primary-gradient)' : 'var(--bg-card)',
                          border: m.role === 'user' ? 'none' : '1px solid var(--border)',
                          color: '#fff',
                          whiteSpace: 'pre-wrap'
                        }}>
                          {m.content}
                        </div>
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                          {m.role === 'user' ? 'You' : m.agent_name || 'Assistant'}
                        </span>
                      </div>
                    ))
                  )}
                  {chatLoading && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '13px' }}>
                      <Loader2 size={16} className="animate-spin" color="#6366f1" />
                      <span>Planner Agent is structuring research workflow...</span>
                    </div>
                  )}
                </div>

                {/* Message Input Box */}
                <form onSubmit={sendChatMessage} style={{
                  padding: '16px',
                  borderTop: '1px solid var(--border)',
                  background: 'rgba(0,0,0,0.2)',
                  display: 'flex',
                  gap: '12px'
                }}>
                  <input 
                    type="text" 
                    placeholder="Enter research prompt e.g., 'Compare the attention models and generate code'..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    style={{
                      flexGrow: 1,
                      backgroundColor: 'rgba(0,0,0,0.3)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      padding: '12px 16px',
                      color: 'var(--text-primary)',
                      fontSize: '14px'
                    }}
                    disabled={chatLoading}
                  />
                  <button 
                    type="submit"
                    style={{
                      background: 'var(--primary-gradient)',
                      padding: '0 20px',
                      borderRadius: '8px',
                      fontWeight: '600',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                    disabled={chatLoading}
                  >
                    Send
                  </button>
                </form>
              </div>

              {/* AGENT ACTIVITY TRACKER (CONSOLE) */}
              <div className="glass-panel" style={{
                width: '380px',
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                overflow: 'hidden',
                flexShrink: 0
              }}>
                <div style={{
                  padding: '16px',
                  borderBottom: '1px solid var(--border)',
                  background: 'linear-gradient(90deg, rgba(99,102,241,0.05) 0%, transparent 100%)'
                }}>
                  <h3 style={{ fontSize: '15px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={16} color="#a855f7" />
                    Agent Orchestration Engine
                  </h3>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Planner workflow execution log</span>
                </div>

                <div style={{ flexGrow: 1, padding: '16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {activeAgentLogs.length === 0 ? (
                    <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                      <Terminal size={24} style={{ margin: '0 auto 8px auto', color: 'var(--text-muted)' }} />
                      Waiting for workflow execution...
                    </div>
                  ) : (
                    activeAgentLogs.map((log, i) => (
                      <div key={i} style={{
                        padding: '12px',
                        borderRadius: '8px',
                        background: 'rgba(255,255,255,0.02)',
                        borderLeft: `3px solid ${log.action.includes('Completed') ? 'var(--success)' : 'var(--primary)'}`,
                        fontSize: '13px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <strong style={{ color: 'var(--text-primary)', fontSize: '12px' }}>{log.agent}</strong>
                          <span style={{ 
                            fontSize: '10px', 
                            color: log.action.includes('Completed') ? 'var(--success)' : 'var(--accent)',
                            fontWeight: '600'
                          }}>{log.action}</span>
                        </div>
                        <pre style={{
                          margin: 0,
                          fontSize: '11px',
                          color: 'var(--text-secondary)',
                          whiteSpace: 'pre-wrap',
                          fontFamily: 'monospace',
                          background: 'rgba(0,0,0,0.2)',
                          padding: '6px',
                          borderRadius: '4px',
                          overflowX: 'auto'
                        }}>
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>
          )}

          {/* TAB: LITERATURE REVIEW */}
          {activeTab === 'literature' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Generate Literature Review</h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '20px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px' }}>Literature Review Title</label>
                    <input 
                      type="text" 
                      value={reviewTitle} 
                      onChange={(e) => setReviewTitle(e.target.value)}
                      style={{
                        width: '100%',
                        backgroundColor: 'var(--bg-card)',
                        border: '1px solid var(--border)',
                        borderRadius: '6px',
                        padding: '10px 12px',
                        color: 'var(--text-primary)',
                        fontSize: '14px'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px' }}>Select Papers to Synthesize</label>
                    {papers.length === 0 ? (
                      <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No papers available. Please upload papers first.</p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {papers.map(p => (
                          <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', cursor: 'pointer' }}>
                            <input 
                              type="checkbox" 
                              checked={selectedPapersForReview.includes(p.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedPapersForReview(prev => [...prev, p.id]);
                                } else {
                                  setSelectedPapersForReview(prev => prev.filter(id => id !== p.id));
                                }
                              }}
                            />
                            {p.title} <span style={{ color: 'var(--text-muted)' }}>({p.authors}, {p.year || 'N/A'})</span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>

                  <button 
                    onClick={generateLiteratureReview}
                    style={{
                      background: 'var(--primary-gradient)',
                      color: '#fff',
                      padding: '10px 20px',
                      borderRadius: '6px',
                      fontWeight: '600',
                      alignSelf: 'flex-start',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                    disabled={reviewLoading || papers.length === 0}
                  >
                    {reviewLoading && <Loader2 size={16} className="animate-spin" />}
                    Compile Literature Review
                  </button>
                </div>
              </div>

              {generatedReview && (
                <div className="glass-panel animate-fade-in" style={{ padding: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h4 style={{ fontWeight: '700', fontSize: '16px' }}>Review Preview</h4>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button 
                        onClick={() => exportReport(reviewTitle, generatedReview, 'md')}
                        style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '12px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Download size={14} /> MD
                      </button>
                      <button 
                        onClick={() => exportReport(reviewTitle, generatedReview, 'docx')}
                        style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '12px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Download size={14} /> DOCX
                      </button>
                      <button 
                        onClick={() => exportReport(reviewTitle, generatedReview, 'pdf')}
                        style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '12px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Download size={14} /> PDF
                      </button>
                    </div>
                  </div>
                  <div style={{
                    padding: '20px',
                    borderRadius: '8px',
                    background: 'rgba(0,0,0,0.2)',
                    fontSize: '14px',
                    lineHeight: '1.6',
                    color: 'var(--text-secondary)',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {generatedReview}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: PAPER COMPARISON */}
          {activeTab === 'compare' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Compare Papers</h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '20px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px' }}>Select Papers to Compare</label>
                    {papers.length === 0 ? (
                      <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No papers available.</p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {papers.map(p => (
                          <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', cursor: 'pointer' }}>
                            <input 
                              type="checkbox" 
                              checked={selectedPapersForCompare.includes(p.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedPapersForCompare(prev => [...prev, p.id]);
                                } else {
                                  setSelectedPapersForCompare(prev => prev.filter(id => id !== p.id));
                                }
                              }}
                            />
                            {p.title}
                          </label>
                        ))}
                      </div>
                    )}
                  </div>

                  <button 
                    onClick={comparePapers}
                    style={{
                      background: 'var(--primary-gradient)',
                      color: '#fff',
                      padding: '10px 20px',
                      borderRadius: '6px',
                      fontWeight: '600',
                      alignSelf: 'flex-start',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                    disabled={comparisonLoading || papers.length === 0}
                  >
                    {comparisonLoading && <Loader2 size={16} className="animate-spin" />}
                    Build Comparison Table
                  </button>
                </div>
              </div>

              {comparisonTable && (
                <div className="glass-panel animate-fade-in" style={{ padding: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h4 style={{ fontWeight: '700', fontSize: '16px' }}>Comparison Matrix</h4>
                    <button 
                      onClick={() => exportReport("Comparison Matrix", comparisonTable, 'docx')}
                      style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '12px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <Download size={14} /> Export DOCX
                    </button>
                  </div>
                  <div style={{
                    padding: '20px',
                    borderRadius: '8px',
                    background: 'rgba(0,0,0,0.2)',
                    fontSize: '14px',
                    lineHeight: '1.6',
                    color: 'var(--text-secondary)',
                    whiteSpace: 'pre-wrap',
                    overflowX: 'auto'
                  }}>
                    {comparisonTable}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: CITATIONS */}
          {activeTab === 'citations' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Citation Generator</h3>
                
                {papers.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)' }}>Upload papers to generate formatted citations.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {papers.map(p => (
                      <div key={p.id} style={{
                        padding: '16px',
                        borderRadius: '8px',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border)'
                      }}>
                        <h4 style={{ fontWeight: '600', fontSize: '15px', color: 'var(--text-primary)', marginBottom: '8px' }}>{p.title}</h4>
                        <div style={{ display: 'grid', gap: '10px', fontSize: '13px', background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px' }}>
                          <div>
                            <span style={{ color: 'var(--accent)', fontWeight: '600', display: 'block', marginBottom: '2px' }}>APA Format</span>
                            <span style={{ color: 'var(--text-secondary)' }}>{p.authors}. ({p.year || 'N/A'}). {p.title}.</span>
                          </div>
                          <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px' }}>
                            <span style={{ color: 'var(--accent)', fontWeight: '600', display: 'block', marginBottom: '2px' }}>IEEE Format</span>
                            <span style={{ color: 'var(--text-secondary)' }}>[{p.id.slice(0,3)}] {p.authors}, &ldquo;{p.title},&rdquo; {p.year || 'N/A'}.</span>
                          </div>
                          <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px' }}>
                            <span style={{ color: 'var(--accent)', fontWeight: '600', display: 'block', marginBottom: '2px' }}>BibTeX</span>
                            <pre style={{ margin: '4px 0 0 0', padding: '6px', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-secondary)', overflowX: 'auto' }}>
{`@article{${p.id.slice(0,8)},
  title={${p.title}},
  author={${p.authors}},
  year={${p.year || 'N/A'}}
}`}
                            </pre>
                            <button 
                              onClick={() => copyToClipboard(`@article{${p.id.slice(0,8)},\n  title={${p.title}},\n  author={${p.authors}},\n  year={${p.year || 'N/A'}}\n}`)}
                              style={{
                                marginTop: '6px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px',
                                fontSize: '11px',
                                color: '#a5b4fc',
                                background: 'transparent'
                              }}
                            >
                              <Copy size={12} /> Copy BibTeX
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
