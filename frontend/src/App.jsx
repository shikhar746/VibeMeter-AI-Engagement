import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [employeeId, setEmployeeId] = useState("");
  const [isChatActive, setIsChatActive] = useState(false);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

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

  return (
    <div className="app-wrapper">
      <header className="app-header">
        <h1 className="app-title">
          <span>Deloitte</span>
          People Experience Bot
        </h1>
        <div className="app-badge">TIA · v2.0</div>
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

      <footer className="app-footer">Deloitte · People & Purpose · Internal Tool</footer>
    </div>
  );
}

export default App;