'use client';

export default function MessageBubble({ message, isTyping = false }) {
  const isUser = message.role === 'user';
  const isError = message.agent_type === 'error';
  
  const getAgentIcon = (agentType) => {
    const iconMap = {
      'document_analysis': '📄',
      'prediction': '🎯',
      'quiz_generation': '📝',
      'knowledge_graph': '🕸️',
      'study_strategy': '📚',
      'performance_analysis': '📊',
      'personal_assistant': '🤝',
      'general_qa': '🧠',
      'thinking': '⚡',
      'error': '❌'
    };
    return iconMap[agentType] || '🤖';
  };

  const getAgentColor = (agentType) => {
    const colorMap = {
      'document_analysis': '#3b82f6', // blue
      'prediction': '#ef4444',      // red
      'quiz_generation': '#8b5cf6', // purple
      'knowledge_graph': '#10b981', // green
      'study_strategy': '#f59e0b', // orange
      'performance_analysis': '#06b6d4', // cyan
      'personal_assistant': '#ec4899', // pink
      'general_qa': '#6366f1',     // indigo
      'thinking': '#94a3b8',       // gray
      'error': '#dc2626'           // red
    };
    return colorMap[agentType] || 'var(--accent-primary)';
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        alignItems: 'flex-start',
        gap: '8px',
        maxWidth: '85%'
      }}
    >
      {!isUser && (
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          background: getAgentColor(message.agent_type),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          flexShrink: 0,
          marginTop: '4px'
        }}>
          {getAgentIcon(message.agent_type)}
        </div>
      )}
      
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        alignItems: isUser ? 'flex-end' : 'flex-start'
      }}>
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '16px',
            background: isUser 
              ? 'var(--accent-primary)' 
              : isError 
                ? 'rgba(220, 38, 38, 0.1)'
                : 'var(--bg-card)',
            color: isUser 
              ? 'var(--bg-primary)' 
              : isError
                ? '#dc2626'
                : 'var(--text-primary)',
            fontSize: '14px',
            lineHeight: '1.5',
            wordBreak: 'break-word',
            border: isError ? '1px solid rgba(220, 38, 38, 0.2)' : 'none',
            maxWidth: '600px'
          }}
        >
          {isTyping && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              <div style={{
                width: '4px',
                height: '4px',
                borderRadius: '50%',
                background: getAgentColor(message.agent_type),
                animation: 'bounce 1.4s infinite ease-in-out both'
              }} />
              <div style={{
                width: '4px',
                height: '4px',
                borderRadius: '50%',
                background: getAgentColor(message.agent_type),
                animation: 'bounce 1.4s infinite ease-in-out both',
                animationDelay: '0.16s'
              }} />
              <div style={{
                width: '4px',
                height: '4px',
                borderRadius: '50%',
                background: getAgentColor(message.agent_type),
                animation: 'bounce 1.4s infinite ease-in-out both',
                animationDelay: '0.32s'
              }} />
            </div>
          )}
          
          {!isTyping && message.content}
        </div>
        
        {!isTyping && message.timestamp && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '11px',
            color: 'var(--text-muted)',
            padding: '0 4px'
          }}>
            <span>{formatTime(message.timestamp)}</span>
            
            {!isUser && message.agent_type && message.agent_type !== 'error' && (
              <>
                <span>•</span>
                <span style={{
                  textTransform: 'capitalize',
                  color: getAgentColor(message.agent_type)
                }}>
                  {message.agent_type.replace('_', ' ')}
                </span>
              </>
            )}
            
            {message.processing_time_ms && (
              <>
                <span>•</span>
                <span>{message.processing_time_ms}ms</span>
              </>
            )}
            
            {message.route_confidence && (
              <>
                <span>•</span>
                <span>{Math.round(message.route_confidence * 100)}% confidence</span>
              </>
            )}
          </div>
        )}
      </div>
      
      {isUser && (
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          background: 'var(--bg-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          flexShrink: 0,
          marginTop: '4px'
        }}>
          👤
        </div>
      )}
      
      <style jsx>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
