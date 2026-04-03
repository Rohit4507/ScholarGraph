'use client';

export default function ChatSidebar({ 
  sessions, 
  currentSessionId, 
  agentCapabilities,
  supportedSubjects,
  onSessionSelect, 
  onNewSession, 
  onDeleteSession,
  onClose 
}) {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString([], { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatMessagePreview = (message) => {
    return message.length > 50 ? message.substring(0, 50) + '...' : message;
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <h3 style={{ 
          margin: 0, 
          fontSize: '16px', 
          fontWeight: 600,
          color: 'var(--text-primary)'
        }}>
          Chat Sessions
        </h3>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '18px',
            cursor: 'pointer',
            padding: '4px'
          }}
        >
          ✕
        </button>
      </div>

      {/* New Session Button */}
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)' }}>
        <button
          onClick={onNewSession}
          style={{
            width: '100%',
            padding: '10px',
            border: '1px solid var(--accent-primary)',
            borderRadius: '8px',
            background: 'var(--accent-primary)',
            color: 'var(--bg-primary)',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
        >
          <span>+</span>
          New Chat Session
        </button>
      </div>

      {/* Sessions List */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto',
        padding: '8px'
      }}>
        {sessions.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '20px',
            color: 'var(--text-muted)',
            fontSize: '14px'
          }}>
            No sessions yet. Start a new chat!
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              onClick={() => onSessionSelect(session.session_id)}
              style={{
                padding: '12px',
                borderRadius: '8px',
                cursor: 'pointer',
                background: session.session_id === currentSessionId 
                  ? 'var(--bg-card)' 
                  : 'transparent',
                border: session.session_id === currentSessionId 
                  ? '1px solid var(--accent-primary)' 
                  : '1px solid transparent',
                marginBottom: '8px',
                transition: 'all 0.2s ease'
              }}
              onMouseOver={(e) => {
                if (session.session_id !== currentSessionId) {
                  e.target.style.background = 'var(--bg-secondary)';
                }
              }}
              onMouseOut={(e) => {
                if (session.session_id !== currentSessionId) {
                  e.target.style.background = 'transparent';
                }
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '4px'
              }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {session.session_name}
                </div>
                
                {session.session_id !== currentSessionId && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.session_id);
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-muted)',
                      fontSize: '12px',
                      cursor: 'pointer',
                      padding: '2px 4px',
                      borderRadius: '4px'
                    }}
                    onMouseOver={(e) => {
                      e.target.style.background = 'rgba(220, 38, 38, 0.1)';
                      e.target.style.color = '#dc2626';
                    }}
                    onMouseOut={(e) => {
                      e.target.style.background = 'none';
                      e.target.style.color = 'var(--text-muted)';
                    }}
                  >
                    🗑️
                  </button>
                )}
              </div>
              
              {session.subject && (
                <div style={{
                  fontSize: '12px',
                  color: 'var(--accent-primary)',
                  marginBottom: '4px',
                  fontWeight: 500
                }}>
                  {session.subject}
                </div>
              )}
              
              <div style={{
                fontSize: '12px',
                color: 'var(--text-muted)',
                marginBottom: '4px'
              }}>
                {session.message_count} messages
              </div>
              
              <div style={{
                fontSize: '11px',
                color: 'var(--text-muted)'
              }}>
                {formatTime(session.last_message_at)}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Agent Capabilities */}
      {agentCapabilities && (
        <div style={{
          borderTop: '1px solid var(--border-color)',
          padding: '16px'
        }}>
          <h4 style={{
            margin: '0 0 12px 0',
            fontSize: '14px',
            fontWeight: 600,
            color: 'var(--text-primary)'
          }}>
            Available Agents
          </h4>
          
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {Object.entries(agentCapabilities).map(([agent, capabilities], index) => (
              <div key={agent} style={{ marginBottom: '8px' }}>
                <div style={{
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  marginBottom: '4px',
                  textTransform: 'capitalize'
                }}>
                  {agent.replace('_', ' ')}
                </div>
                <div style={{ marginLeft: '8px' }}>
                  {capabilities.slice(0, 2).map((cap, capIndex) => (
                    <div key={capIndex} style={{ marginBottom: '2px' }}>
                      • {cap}
                    </div>
                  ))}
                  {capabilities.length > 2 && (
                    <div style={{ color: 'var(--text-muted)' }}>
                      +{capabilities.length - 2} more
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Supported Subjects */}
      {supportedSubjects && supportedSubjects.length > 0 && (
        <div style={{
          borderTop: '1px solid var(--border-color)',
          padding: '16px'
        }}>
          <h4 style={{
            margin: '0 0 12px 0',
            fontSize: '14px',
            fontWeight: 600,
            color: 'var(--text-primary)'
          }}>
            Supported Subjects
          </h4>
          
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '6px'
          }}>
            {supportedSubjects.slice(0, 8).map((subject) => (
              <div
                key={subject}
                style={{
                  padding: '4px 8px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '12px',
                  fontSize: '11px',
                  color: 'var(--text-secondary)'
                }}
              >
                {subject}
              </div>
            ))}
            {supportedSubjects.length > 8 && (
              <div style={{
                padding: '4px 8px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                fontSize: '11px',
                color: 'var(--text-muted)'
              }}>
                +{supportedSubjects.length - 8} more
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
