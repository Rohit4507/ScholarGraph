'use client';

import { useState, useEffect } from 'react';
import KnowledgeGraph from '../KnowledgeGraph';

export default function LiveDashboard({ data, currentSubject, onUpdate }) {
  const [activeWidget, setActiveWidget] = useState('overview');
  const [graphData, setGraphData] = useState(null);

  useEffect(() => {
    if (currentSubject) {
      fetchGraphData(currentSubject);
    }
  }, [currentSubject]);

  const fetchGraphData = async (subject) => {
    try {
      const response = await fetch(`/api/graph/${encodeURIComponent(subject)}`);
      if (response.ok) {
        const data = await response.json();
        setGraphData(data);
      }
    } catch (error) {
      console.error('Failed to fetch graph data:', error);
    }
  };

  const renderWidget = () => {
    switch (activeWidget) {
      case 'overview':
        return <OverviewWidget data={data} />;
      case 'predictions':
        return <PredictionsWidget data={data?.predictions} subject={currentSubject} />;
      case 'knowledge_graph':
        return <KnowledgeGraphWidget data={graphData} subject={currentSubject} />;
      case 'quiz_stats':
        return <QuizStatsWidget data={data?.quizStats} />;
      case 'performance':
        return <PerformanceWidget data={data?.performance} />;
      default:
        return <OverviewWidget data={data} />;
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-color)',
        background: 'var(--bg-secondary)'
      }}>
        <h2 style={{ 
          margin: 0, 
          fontSize: '18px', 
          fontWeight: 600,
          color: 'var(--text-primary)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          📊 Live Dashboard
          {currentSubject && (
            <span style={{
              fontSize: '14px',
              color: 'var(--accent-primary)',
              fontWeight: 500
            }}>
              {currentSubject}
            </span>
          )}
        </h2>
      </div>

      {/* Widget Navigation */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap'
      }}>
        {[
          { id: 'overview', label: 'Overview', icon: '📈' },
          { id: 'predictions', label: 'Predictions', icon: '🎯' },
          { id: 'knowledge_graph', label: 'Knowledge Graph', icon: '🕸️' },
          { id: 'quiz_stats', label: 'Quiz Stats', icon: '📝' },
          { id: 'performance', label: 'Performance', icon: '📊' }
        ].map((widget) => (
          <button
            key={widget.id}
            onClick={() => setActiveWidget(widget.id)}
            style={{
              padding: '8px 16px',
              border: activeWidget === widget.id 
                ? '1px solid var(--accent-primary)' 
                : '1px solid var(--border-color)',
              borderRadius: '20px',
              background: activeWidget === widget.id 
                ? 'var(--accent-primary)' 
                : 'var(--bg-card)',
              color: activeWidget === widget.id 
                ? 'var(--bg-primary)' 
                : 'var(--text-secondary)',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
          >
            <span>{widget.icon}</span>
            {widget.label}
          </button>
        ))}
      </div>

      {/* Widget Content */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px'
      }}>
        {renderWidget()}
      </div>
    </div>
  );
}

function OverviewWidget({ data }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Stats Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '16px'
      }}>
        <StatCard
          title="Documents"
          value={data?.documents_processed || 0}
          icon="📄"
          color="#3b82f6"
        />
        <StatCard
          title="Topics"
          value={data?.total_topics || 0}
          icon="🎯"
          color="#ef4444"
        />
        <StatCard
          title="Quizzes"
          value={data?.quiz_stats?.total_attempts || 0}
          icon="📝"
          color="#8b5cf6"
        />
        <StatCard
          title="Avg Score"
          value={`${data?.quiz_stats?.avg_score?.toFixed(1) || 0}%`}
          icon="📊"
          color="#10b981"
        />
      </div>

      {/* Priority Distribution */}
      {data?.priority_distribution && (
        <div style={{
          background: 'var(--bg-card)',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid var(--border-color)'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: 'var(--text-primary)' }}>
            Topic Priority Distribution
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { label: 'High Priority', value: data.priority_distribution.high, color: '#ef4444' },
              { label: 'Medium Priority', value: data.priority_distribution.medium, color: '#f59e0b' },
              { label: 'Low Priority', value: data.priority_distribution.low, color: '#10b981' }
            ].map((priority) => (
              <div key={priority.label} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: priority.color
                }} />
                <span style={{ 
                  flex: 1, 
                  fontSize: '14px', 
                  color: 'var(--text-secondary)' 
                }}>
                  {priority.label}
                </span>
                <span style={{ 
                  fontSize: '14px', 
                  fontWeight: 600,
                  color: 'var(--text-primary)' 
                }}>
                  {priority.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div style={{
        background: 'var(--bg-card)',
        padding: '20px',
        borderRadius: '12px',
        border: '1px solid var(--border-color)'
      }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: 'var(--text-primary)' }}>
          Recent Activity
        </h3>
        <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
          <p>📄 Document uploaded: Machine Learning syllabus</p>
          <p>🎯 Predictions generated for 12 topics</p>
          <p>📝 Quiz completed: 85% score</p>
          <p>🕸️ Knowledge graph updated</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      padding: '16px',
      borderRadius: '12px',
      border: '1px solid var(--border-color)',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '24px', marginBottom: '8px' }}>{icon}</div>
      <div style={{
        fontSize: '24px',
        fontWeight: 700,
        color: color,
        marginBottom: '4px'
      }}>
        {value}
      </div>
      <div style={{
        fontSize: '12px',
        color: 'var(--text-muted)',
        textTransform: 'uppercase'
      }}>
        {title}
      </div>
    </div>
  );
}

function PredictionsWidget({ data, subject }) {
  if (!data?.predictions?.length) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '40px',
        color: 'var(--text-muted)'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎯</div>
        <h3 style={{ fontSize: '16px', marginBottom: '8px' }}>
          No predictions available
        </h3>
        <p style={{ fontSize: '14px' }}>
          Upload documents and ask for predictions to see topic probabilities
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 style={{ margin: '0 0 20px 0', fontSize: '16px', color: 'var(--text-primary)' }}>
        Topic Predictions for {subject}
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {data.predictions.slice(0, 10).map((prediction, index) => (
          <div
            key={index}
            style={{
              background: 'var(--bg-card)',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)'
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <span style={{
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--text-primary)'
              }}>
                {prediction.topic}
              </span>
              <span style={{
                fontSize: '14px',
                fontWeight: 700,
                color: prediction.probability_score >= 70 ? '#ef4444' :
                       prediction.probability_score >= 40 ? '#f59e0b' : '#10b981'
              }}>
                {prediction.probability_score}%
              </span>
            </div>
            <div style={{
              height: '4px',
              background: 'var(--border-color)',
              borderRadius: '2px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${prediction.probability_score}%`,
                height: '100%',
                background: prediction.probability_score >= 70 ? '#ef4444' :
                          prediction.probability_score >= 40 ? '#f59e0b' : '#10b981',
                borderRadius: '2px',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <div style={{
              fontSize: '12px',
              color: 'var(--text-muted)',
              marginTop: '4px'
            }}>
              Priority: {prediction.priority}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function KnowledgeGraphWidget({ data, subject }) {
  if (!data?.nodes?.length) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '40px',
        color: 'var(--text-muted)'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🕸️</div>
        <h3 style={{ fontSize: '16px', marginBottom: '8px' }}>
          No knowledge graph available
        </h3>
        <p style={{ fontSize: '14px' }}>
          Upload documents and ask for knowledge graph visualization
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 style={{ margin: '0 0 20px 0', fontSize: '16px', color: 'var(--text-primary)' }}>
        Knowledge Graph for {subject}
      </h3>
      <div style={{
        background: 'var(--bg-card)',
        padding: '20px',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        height: '400px'
      }}>
        <KnowledgeGraph data={data} />
      </div>
    </div>
  );
}

function QuizStatsWidget({ data }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>📝</div>
      <h3 style={{ fontSize: '16px', marginBottom: '8px' }}>
        Quiz Statistics
      </h3>
      <p style={{ fontSize: '14px' }}>
        Take quizzes to see your performance statistics here
      </p>
    </div>
  );
}

function PerformanceWidget({ data }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
      <h3 style={{ fontSize: '16px', marginBottom: '8px' }}>
        Performance Analytics
      </h3>
      <p style={{ fontSize: '14px' }}>
        Complete quizzes and activities to see performance trends
      </p>
    </div>
  );
}
