'use client';

import { useState, useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';
import { apiUrl } from '../../lib/api';

export default function ChatInterface({ sessionId, onDashboardUpdate, onSubjectChange }) {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState(null);
  const [showSidebar, setShowSidebar] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [agentCapabilities, setAgentCapabilities] = useState(null);
  const [supportedSubjects, setSupportedSubjects] = useState([]);
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    // Load initial data
    if (sessionId) {
      loadSessionHistory(sessionId);
      loadSessionsList();
      loadAgentCapabilities();
      loadSupportedSubjects();
    }

    return () => {
      // Cleanup any ongoing requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [sessionId]);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStreamingMessage]);

  const loadSessionHistory = async (sid) => {
    try {
      const response = await fetch(apiUrl(`/api/chat/sessions/${sid}?limit=20`));
      if (response.ok) {
        const data = await response.json();
        setMessages(data || []);
      }
    } catch (error) {
      console.error('Failed to load session history:', error);
    }
  };

  const loadSessionsList = async () => {
    try {
      const response = await fetch(apiUrl('/api/chat/sessions?limit=10'));
      if (response.ok) {
        const data = await response.json();
        setSessions(data || []);
      }
    } catch (error) {
      console.error('Failed to load sessions list:', error);
    }
  };

  const loadAgentCapabilities = async () => {
    try {
      const response = await fetch(apiUrl('/api/chat/agents/capabilities'));
      if (response.ok) {
        const data = await response.json();
        setAgentCapabilities(data.capabilities || {});
      }
    } catch (error) {
      console.error('Failed to load agent capabilities:', error);
    }
  };

  const loadSupportedSubjects = async () => {
    try {
      const response = await fetch(apiUrl('/api/chat/subjects'));
      if (response.ok) {
        const data = await response.json();
        setSupportedSubjects(data.subjects || []);
      }
    } catch (error) {
      console.error('Failed to load supported subjects:', error);
    }
  };

  const sendMessage = async (messageText, subject = '') => {
    if (!messageText.trim()) return;

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    // Add user message immediately
    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, userMessage]);

    // Update subject if provided
    if (subject && subject !== onSubjectChange) {
      onSubjectChange(subject);
    }

    setIsTyping(true);
    setCurrentStreamingMessage({
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      agent_type: 'thinking'
    });

    try {
      // Create form data for SSE request
      const formData = new FormData();
      formData.append('message', messageText);
      formData.append('session_id', sessionId);
      if (subject) formData.append('subject', subject);

      // Make SSE request
      const response = await fetch(apiUrl('/api/chat/stream'), {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'token') {
                // Stream token
                setCurrentStreamingMessage(prev => ({
                  ...prev,
                  content: prev.content + data.token,
                  agent_type: data.agent_type
                }));
              } else if (data.type === 'complete') {
                // Response complete
                setCurrentStreamingMessage(null);
                setIsTyping(false);
                
                const assistantMessage = {
                  role: 'assistant',
                  content: data.full_content,
                  timestamp: Date.now(),
                  agent_type: data.agent_type,
                  message_id: data.message_id,
                  processing_time_ms: data.processing_time_ms,
                  route_confidence: data.route_confidence
                };
                setMessages(prev => [...prev, assistantMessage]);

                // Trigger dashboard updates
                if (data.dashboard_updates) {
                  onDashboardUpdate(data.dashboard_updates);
                }

                // Refresh sessions list
                loadSessionsList();
              } else if (data.type === 'error') {
                setCurrentStreamingMessage(null);
                setIsTyping(false);
                
                const errorMessage = {
                  role: 'assistant',
                  content: `Error: ${data.error}`,
                  timestamp: Date.now(),
                  agent_type: 'error'
                };
                setMessages(prev => [...prev, errorMessage]);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted');
      } else {
        console.error('Failed to send message:', error);
        setCurrentStreamingMessage(null);
        setIsTyping(false);
        
        const errorMessage = {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: Date.now(),
          agent_type: 'error'
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    }
  };

  const switchSession = async (newSessionId) => {
    // Cancel current request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Update session
    setSessionId(newSessionId);
    localStorage.setItem('chat_session_id', newSessionId);
    setMessages([]);
    setCurrentStreamingMessage(null);
    setIsTyping(false);
    
    // Load new session history
    await loadSessionHistory(newSessionId);
  };

  const createNewSession = async () => {
    try {
      const response = await fetch(apiUrl('/api/chat/sessions'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_name: `Chat ${new Date().toLocaleTimeString()}` })
      });
      
      if (response.ok) {
        const data = await response.json();
        await switchSession(data.session_id);
        await loadSessionsList();
      }
    } catch (error) {
      console.error('Failed to create new session:', error);
    }
  };

  const deleteSession = async (sessionIdToDelete) => {
    try {
      const response = await fetch(apiUrl(`/api/chat/sessions/${sessionIdToDelete}`), {
        method: 'DELETE'
      });
      
      if (response.ok) {
        await loadSessionsList();
        
        // If we deleted the current session, create a new one
        if (sessionIdToDelete === sessionId) {
          await createNewSession();
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      height: '100%', 
      background: 'var(--bg-primary)'
    }}>
      {/* Chat Sidebar */}
      {showSidebar && (
        <div style={{
          width: '280px',
          borderRight: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          height: '100%'
        }}>
          <ChatSidebar
            sessions={sessions}
            currentSessionId={sessionId}
            agentCapabilities={agentCapabilities}
            supportedSubjects={supportedSubjects}
            onSessionSelect={switchSession}
            onNewSession={createNewSession}
            onDeleteSession={deleteSession}
            onClose={() => setShowSidebar(false)}
          />
        </div>
      )}

      {/* Main Chat Area */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        height: '100%'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-secondary)',
                fontSize: '18px',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              ☰
            </button>
            <div>
              <h2 style={{ 
                margin: 0, 
                fontSize: '18px', 
                fontWeight: 600,
                color: 'var(--text-primary)'
              }}>
                ScholarGraph AI
              </h2>
              <p style={{ 
                margin: 0, 
                fontSize: '12px', 
                color: 'var(--text-muted)'
              }}>
                Academic Intelligence Assistant
              </p>
            </div>
          </div>
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#10b981',
              animation: 'pulse 2s infinite'
            }} />
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Online
            </span>
          </div>
        </div>

        {/* Messages Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {messages.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: '40px 20px',
              color: 'var(--text-muted)'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>👋</div>
              <h3 style={{ fontSize: '18px', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                Welcome to ScholarGraph AI!
              </h3>
              <p style={{ fontSize: '14px', lineHeight: '1.5' }}>
                I'm your academic intelligence assistant. I can help you with:<br/>
                📚 Document analysis and topic extraction<br/>
                🎯 Exam predictions and probability scoring<br/>
                🧠 Knowledge graph visualization<br/>
                📝 Adaptive quiz generation<br/>
                📊 Performance tracking and study plans<br/>
                <br/>
                Try asking: "Help me analyze my machine learning syllabus"
              </p>
            </div>
          )}
          
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
          
          {currentStreamingMessage && (
            <MessageBubble message={currentStreamingMessage} isTyping={true} />
          )}
          
          {isTyping && !currentStreamingMessage && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 16px',
              background: 'var(--bg-card)',
              borderRadius: '12px',
              width: 'fit-content'
            }}>
              <div style={{
                display: 'flex',
                gap: '4px'
              }}>
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: 'var(--accent-primary)',
                  animation: 'bounce 1.4s infinite ease-in-out both'
                }} />
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: 'var(--accent-primary)',
                  animation: 'bounce 1.4s infinite ease-in-out both',
                  animationDelay: '0.16s'
                }} />
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: 'var(--accent-primary)',
                  animation: 'bounce 1.4s infinite ease-in-out both',
                  animationDelay: '0.32s'
                }} />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div style={{
          padding: '20px',
          borderTop: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)'
        }}>
          <ChatInput 
            onSendMessage={sendMessage}
            disabled={isTyping}
            supportedSubjects={supportedSubjects}
          />
        </div>
      </div>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
