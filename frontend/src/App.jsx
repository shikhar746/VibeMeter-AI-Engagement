import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  // ── Employee chat state ────────────────────────────────────
  const [employeeId, setEmployeeId] = useState("");
  const [isChatActive, setIsChatActive] = useState(false);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // ── HR modal state ─────────────────────────────────────────
  const [showHrModal, setShowHrModal] = useState(false);
  const [hrPassword, setHrPassword] = useState("");
  const [hrToken, setHrToken] = useState("");
  const [hrError, setHrError] = useState("");
  const [isHrLoading, setIsHrLoading] = useState(false);
  const [isHrLoggedIn, setIsHrLoggedIn] = useState(false);
  const [hrDashboardData, setHrDashboardData] = useState([]);
  const [isDashboardLoading, setIsDashboardLoading] = useState(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // ── Employee handlers ──────────────────────────────────────
  const handleTriggerOutreach = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/trigger_outreach`);
      alert(`Success! ${res.data.employees_contacted} employees flagged for outreach.`);
    } catch {
      alert("Error triggering outreach. Is the backend running?");
    }
  };

  const handleStartChat = async () => {
    if (!employeeId.trim()) return alert("Please enter an Employee ID (e.g., EMP0345)");
    setIsLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/start_chat/${employeeId}`);
      setMessages([{ sender: "bot", text: res.data.bot_reply }]);
      setIsChatActive(true);
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to start chat. Check the Employee ID.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading) return;
    const newMessages = [...messages, { sender: "user", text: userInput }];
    setMessages(newMessages);
    setUserInput("");
    setIsLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/chat`, {
        employee_id: employeeId,
        message: userInput,
      });
      setMessages([...newMessages, { sender: "bot", text: res.data.bot_reply }]);
      if (res.data.escalated) {
        setMessages(prev => [...prev, { sender: "system", text: "This conversation has been escalated to HR." }]);
      }
    } catch {
      setMessages(prev => [...prev, { sender: "system", text: "Something went wrong. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  // ── HR handlers ────────────────────────────────────────────
  const handleHrLogin = async (e) => {
    e.preventDefault();
    if (!hrPassword.trim()) return;
    setIsHrLoading(true);
    setHrError("");
    try {
      const res = await axios.post(`${API_BASE_URL}/auth/hr/login`, { password: hrPassword });
      const token = res.data.token;
      setHrToken(token);
      setIsHrLoggedIn(true);
      setHrPassword("");
      fetchHrDashboard(token);
    } catch (error) {
      setHrError(error.response?.data?.detail || "Incorrect password. Please try again.");
    } finally {
      setIsHrLoading(false);
    }
  };

  const fetchHrDashboard = async (token) => {
    const authToken = token || hrToken;
    setIsDashboardLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/dashboard/employees`, {
        headers: { "X-HR-Token": authToken }
      });
      setHrDashboardData(res.data.employees || []);
    } catch {
      setHrError("Failed to load dashboard data.");
    } finally {
      setIsDashboardLoading(false);
    }
  };

  const handleHrLogout = () => {
    setIsHrLoggedIn(false);
    setHrToken("");
    setHrDashboardData([]);
    setHrError("");
    setShowHrModal(false);
  };

  const closeHrModal = () => {
    if (!isHrLoggedIn) {
      setHrPassword("");
      setHrError("");
    }
    setShowHrModal(false);
  };

  // ── Render ─────────────────────────────────────────────────
  return (
    <div className="app-wrapper">
      <header className="app-header">
        <h1 className="app-title">
          <span>The Company</span>
          People Experience Bot
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="hr-login-btn"
            onClick={() => setShowHrModal(true)}
            title="HR Portal"
          >
            {isHrLoggedIn ? "👔 HR Portal" : "🔒 HR Login"}
          </button>
          <div className="app-badge">TIA · v2.0</div>
        </div>
      </header>

      <div className="card">
        {!isChatActive ? (
          <div className="admin-panel">
            <p className="section-label">Admin Controls</p>
            <button className="outreach-btn" onClick={handleTriggerOutreach}>
              <span className="btn-icon">⚡</span>
              Trigger Daily Data Load
            </button>
            <div className="divider" />
            <p className="section-label">Simulate Employee Login</p>
            <p className="login-hint">Enter an Employee ID from your CSV to begin a session</p>
            <div className="input-row">
              <input
                className="emp-input"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleStartChat()}
                placeholder="e.g. EMP0345"
              />
              <button className="start-btn" onClick={handleStartChat} disabled={isLoading}>
                {isLoading ? "Loading…" : "Start Chat →"}
              </button>
            </div>
          </div>
        ) : (
          <div className="chat-panel">
            <div className="chat-header">
              <div className="avatar">🤝</div>
              <div className="chat-meta">
                <div className="chat-name">TIA — Your People Assistant</div>
                <div className="chat-status">
                  <span className="status-dot" />
                  Active · Confidential session
                </div>
              </div>
              <div className="emp-tag">{employeeId}</div>
            </div>

            <div className="messages-area">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.sender}`}>
                  {msg.sender !== 'system' && (
                    <div className="message-sender">
                      {msg.sender === 'user' ? 'You' : 'TIA'}
                    </div>
                  )}
                  <div className="message-bubble">{msg.text}</div>
                </div>
              ))}
              {isLoading && (
                <div className="typing-indicator">
                  <div className="typing-dots">
                    <span /><span /><span />
                  </div>
                  <span className="typing-text">TIA is typing…</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
              <form className="input-form" onSubmit={handleSendMessage}>
                <input
                  className="chat-input"
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  placeholder="Share how you're feeling…"
                  disabled={isLoading}
                />
                <button className="send-btn" type="submit" disabled={isLoading || !userInput.trim()}>
                  ↑
                </button>
              </form>
              <p className="input-hint">This conversation is confidential · Press Enter to send</p>
            </div>
          </div>
        )}
      </div>

      <footer className="app-footer">The Company · People & Purpose · Internal Tool</footer>

      {/* ── HR Modal Overlay ──────────────────────────────────── */}
      {showHrModal && (
        <div className="hr-modal-overlay" onClick={closeHrModal}>
          <div className="hr-modal" onClick={(e) => e.stopPropagation()}>

            {!isHrLoggedIn ? (
              /* Login form */
              <>
                <div className="hr-modal-header">
                  <div className="hr-modal-icon">🔐</div>
                  <div>
                    <h2 className="hr-modal-title">HR Portal</h2>
                    <p className="hr-modal-subtitle">Restricted access · Authorised personnel only</p>
                  </div>
                  <button className="hr-modal-close" onClick={closeHrModal}>✕</button>
                </div>

                <form className="hr-login-form" onSubmit={handleHrLogin}>
                  <label className="hr-field-label">HR Password</label>
                  <input
                    className="hr-password-input"
                    type="password"
                    value={hrPassword}
                    onChange={(e) => setHrPassword(e.target.value)}
                    placeholder="Enter HR password"
                    autoFocus
                    disabled={isHrLoading}
                  />
                  {hrError && <p className="hr-error">{hrError}</p>}
                  <button
                    className="hr-submit-btn"
                    type="submit"
                    disabled={isHrLoading || !hrPassword.trim()}
                  >
                    {isHrLoading ? "Verifying…" : "Access Dashboard →"}
                  </button>
                </form>
              </>
            ) : (
              /* Dashboard */
              <>
                <div className="hr-modal-header">
                  <div className="hr-modal-icon">📊</div>
                  <div>
                    <h2 className="hr-modal-title">Employee Dashboard</h2>
                    <p className="hr-modal-subtitle">{hrDashboardData.length} active conversations</p>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="hr-refresh-btn" onClick={() => fetchHrDashboard()} title="Refresh">↺</button>
                    <button className="hr-modal-close" onClick={handleHrLogout} title="Logout">⏻</button>
                  </div>
                </div>

                {isDashboardLoading ? (
                  <div className="hr-loading">Loading employee data…</div>
                ) : hrDashboardData.length === 0 ? (
                  <div className="hr-empty">No active conversations yet. Employees will appear here once they start chatting.</div>
                ) : (
                  <div className="hr-table-wrap">
                    <table className="hr-table">
                      <thead>
                        <tr>
                          <th>Employee ID</th>
                          <th>Top SHAP Feature</th>
                          <th>Status</th>
                          <th className="issues-col">Issues Raised</th>
                        </tr>
                      </thead>
                      <tbody>
                        {hrDashboardData.map((row) => (
                          <tr key={row.employee_id}>
                            <td className="emp-id-cell">{row.employee_id}</td>
                            <td className="feature-cell">{row.primary_issue?.replace(/_/g, ' ') || '—'}</td>
                            <td>
                              <span className={`status-badge ${row.escalated ? 'escalated' : 'active'}`}>
                                {row.escalated ? '🚨 Escalated' : '💬 Active'}
                              </span>
                            </td>
                            <td className={`issues-cell ${row.escalated ? 'issues-urgent' : ''}`}>
                              {row.vibe_summary || 'Conversation in progress…'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;