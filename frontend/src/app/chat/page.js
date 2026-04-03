'use client';

import { useState, useEffect, useRef } from 'react';
import ChatInterface from '../../components/chat/ChatInterface';
import LiveDashboard from '../../components/dashboard/LiveDashboard';
import { apiUrl } from '../../lib/api';

export default function ChatPage() {
  const [dashboardData, setDashboardData] = useState(null);
  const [currentSubject, setCurrentSubject] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize session
    const initializeSession = async () => {
      try {
        // Generate or retrieve session ID
        const storedSession = localStorage.getItem('chat_session_id');
        if (storedSession) {
          setSessionId(storedSession);
        } else {
          // Create new session
          const response = await fetch(apiUrl('/api/chat/sessions'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_name: 'New Chat Session' })
          });
          if (response.ok) {
            const data = await response.json();
            setSessionId(data.session_id);
            localStorage.setItem('chat_session_id', data.session_id);
          }
        }

        // Load initial dashboard data
        await fetchDashboardData();
      } catch (error) {
        console.error('Failed to initialize session:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeSession();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(apiUrl('/api/dashboard/stats'));
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };

  const handleDashboardUpdate = (updateData) => {
    // Update dashboard based on chat response
    setDashboardData(prevData => ({
      ...prevData,
      ...updateData
    }));

    // Refresh specific widget if needed
    if (updateData?.widget === 'predictions' && currentSubject) {
      fetchPredictions(currentSubject);
    } else if (updateData?.widget === 'knowledge_graph') {
      fetchGraphData(currentSubject);
    } else if (updateData?.widget === 'quiz_stats') {
      fetchQuizStats();
    }
  };

  const fetchPredictions = async (subject) => {
    try {
      const response = await fetch(apiUrl(`/api/predict/${encodeURIComponent(subject)}`));
      if (response.ok) {
        const data = await response.json();
        setDashboardData(prev => ({
          ...prev,
          predictions: data
        }));
      }
    } catch (error) {
      console.error('Failed to fetch predictions:', error);
    }
  };

  const fetchGraphData = async (subject) => {
    try {
      const response = await fetch(apiUrl(`/api/graph/${encodeURIComponent(subject)}`));
      if (response.ok) {
        const data = await response.json();
        setDashboardData(prev => ({
          ...prev,
          graphData: data
        }));
      }
    } catch (error) {
      console.error('Failed to fetch graph data:', error);
    }
  };

  const fetchQuizStats = async () => {
    try {
      // This would fetch recent quiz statistics
      const response = await fetch(apiUrl('/api/quiz/attempts'));
      if (response.ok) {
        const data = await response.json();
        setDashboardData(prev => ({
          ...prev,
          quizStats: data
        }));
      }
    } catch (error) {
      console.error('Failed to fetch quiz stats:', error);
    }
  };

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-primary)',
        color: 'var(--text-secondary)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
          <p>Loading ScholarGraph AI...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      background: 'var(--bg-primary)',
      overflow: 'hidden'
    }}>
      {/* Left Panel - Chat Interface */}
      <div style={{ 
        flex: '1', 
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%'
      }}>
        <ChatInterface
          sessionId={sessionId}
          onDashboardUpdate={handleDashboardUpdate}
          onSubjectChange={setCurrentSubject}
        />
      </div>

      {/* Right Panel - Live Dashboard */}
      <div style={{ 
        flex: '1', 
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden'
      }}>
        <LiveDashboard
          data={dashboardData}
          currentSubject={currentSubject}
          onUpdate={fetchDashboardData}
        />
      </div>
    </div>
  );
}
