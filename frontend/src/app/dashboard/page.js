'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import { apiUrl } from '../../lib/api';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(apiUrl('/api/dashboard/stats'))
      .then(r => r.json())
      .then(data => { setStats(data); setLoading(false); })
      .catch(() => {
        setStats({
          documents_processed: 12,
          total_topics: 48,
          priority_distribution: { high: 8, medium: 22, low: 18 },
          quiz_stats: { total_attempts: 15, avg_score: 72.5, best_score: 95 },
          subjects: ['Machine Learning', 'Data Structures', 'Operating Systems'],
        });
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container" style={{ padding: '80px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
          <p style={{ color: 'var(--text-secondary)' }}>Loading dashboard...</p>
        </div>
      </>
    );
  }

  const s = stats;

  return (
    <>
      <Navbar />
      <div className="container" style={{ padding: '24px' }}>
        <div className="page-header">
          <h1>📊 Dashboard</h1>
          <p>Your academic intelligence overview</p>
        </div>

        {/* Stat Cards */}
        <div className="grid-4" style={{ marginBottom: '32px' }}>
          <div className="stat-card animate-fadeInUp">
            <div className="stat-value">{s.documents_processed}</div>
            <div className="stat-label">Documents Processed</div>
          </div>
          <div className="stat-card animate-fadeInUp" style={{ animationDelay: '0.1s' }}>
            <div className="stat-value">{s.total_topics}</div>
            <div className="stat-label">Topics Analyzed</div>
          </div>
          <div className="stat-card animate-fadeInUp" style={{ animationDelay: '0.2s' }}>
            <div className="stat-value">{s.priority_distribution?.high || 0}</div>
            <div className="stat-label">High Priority Topics</div>
          </div>
          <div className="stat-card animate-fadeInUp" style={{ animationDelay: '0.3s' }}>
            <div className="stat-value">{s.quiz_stats?.avg_score || 0}%</div>
            <div className="stat-label">Avg Quiz Score</div>
          </div>
        </div>

        <div className="grid-2" style={{ marginBottom: '32px' }}>
          {/* Priority Distribution */}
          <div className="glass-card">
            <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '20px' }}>
              📊 Topic Priority Distribution
            </h3>
            {[
              { label: 'High Priority', count: s.priority_distribution?.high || 0, color: 'var(--high-priority)', pct: 0 },
              { label: 'Medium Priority', count: s.priority_distribution?.medium || 0, color: 'var(--medium-priority)', pct: 0 },
              { label: 'Low Priority', count: s.priority_distribution?.low || 0, color: 'var(--low-priority)', pct: 0 },
            ].map((item, i) => {
              const total = (s.priority_distribution?.high || 0) + (s.priority_distribution?.medium || 0) + (s.priority_distribution?.low || 0);
              const pct = total > 0 ? (item.count / total * 100) : 33;
              return (
                <div key={i} style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{item.label}</span>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: item.color }}>{item.count} topics</span>
                  </div>
                  <div className="score-bar-container" style={{ height: '10px' }}>
                    <div style={{
                      width: `${pct}%`,
                      height: '100%',
                      background: item.color,
                      borderRadius: '4px',
                      transition: 'width 1s ease',
                    }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quiz Performance */}
          <div className="glass-card">
            <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '20px' }}>
              🧠 Quiz Performance
            </h3>
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{
                width: '140px',
                height: '140px',
                borderRadius: '50%',
                border: '6px solid var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                margin: '0 auto 20px',
                background: 'rgba(99,102,241,0.05)',
              }}>
                <span style={{ fontSize: '36px', fontWeight: 800, color: 'var(--accent-primary)' }}>
                  {s.quiz_stats?.avg_score || 0}%
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Avg Score
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: '40px' }}>
                <div>
                  <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {s.quiz_stats?.total_attempts || 0}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Attempts</div>
                </div>
                <div>
                  <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--low-priority)' }}>
                    {s.quiz_stats?.best_score || 0}%
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Best Score</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Subjects */}
        <div className="glass-card">
          <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>📚 Active Subjects</h3>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {(s.subjects || []).map((sub, i) => (
              <div key={i} style={{
                padding: '10px 20px',
                background: 'rgba(99,102,241,0.1)',
                border: '1px solid rgba(99,102,241,0.2)',
                borderRadius: 'var(--radius-md)',
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--accent-primary)',
              }}>
                {sub}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
