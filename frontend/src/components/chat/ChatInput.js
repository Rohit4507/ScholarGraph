'use client';

import { useState } from 'react';

export default function ChatInput({ onSendMessage, disabled, supportedSubjects }) {
  const [message, setMessage] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message, selectedSubject);
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Subject Selector */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <select
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          style={{
            padding: '8px 12px',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '14px',
            cursor: 'pointer',
            flex: '0 0 auto',
            minWidth: '150px'
          }}
        >
          <option value="">No Subject (Optional)</option>
          {supportedSubjects.map(subject => (
            <option key={subject} value={subject}>{subject}</option>
          ))}
        </select>
        
        {selectedSubject && (
          <button
            type="button"
            onClick={() => setSelectedSubject('')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '12px',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Message Input */}
      <div style={{
        display: 'flex',
        gap: '12px',
        alignItems: 'flex-end'
      }}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            selectedSubject 
              ? `Ask about ${selectedSubject}...` 
              : "Ask me anything about your studies..."
          }
          disabled={disabled}
          rows={1}
          style={{
            flex: 1,
            padding: '12px 16px',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '14px',
            resize: 'none',
            minHeight: '44px',
            maxHeight: '120px',
            fontFamily: 'inherit',
            opacity: disabled ? 0.6 : 1,
            cursor: disabled ? 'not-allowed' : 'text'
          }}
          onInput={(e) => {
            // Auto-resize textarea
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
          }}
        />
        
        <button
          type="submit"
          disabled={!message.trim() || disabled}
          style={{
            padding: '12px 20px',
            border: 'none',
            borderRadius: '12px',
            background: (!message.trim() || disabled) 
              ? 'var(--border-color)' 
              : 'var(--accent-primary)',
            color: 'var(--bg-primary)',
            fontSize: '14px',
            fontWeight: 600,
            cursor: (!message.trim() || disabled) ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap'
          }}
        >
          {disabled ? 'Sending...' : 'Send'}
        </button>
      </div>

      {/* Quick Suggestions */}
      {!message && !disabled && (
        <div style={{
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap',
          fontSize: '12px',
          color: 'var(--text-muted)'
        }}>
          <span>Try:</span>
          {[
            "Analyze my syllabus",
            "Predict exam topics", 
            "Generate a quiz",
            "Show knowledge graph",
            "How am I doing?"
          ].map((suggestion, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setMessage(suggestion)}
              style={{
                background: 'none',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                padding: '4px 12px',
                color: 'var(--text-secondary)',
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseOver={(e) => {
                e.target.style.background = 'var(--bg-card)';
                e.target.style.color = 'var(--accent-primary)';
              }}
              onMouseOut={(e) => {
                e.target.style.background = 'none';
                e.target.style.color = 'var(--text-secondary)';
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </form>
  );
}
