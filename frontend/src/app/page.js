'use client';

import Link from 'next/link';

export default function HomePage() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Hero Section */}
      <section style={{
        padding: '120px 24px 80px',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Background glow */}
        <div style={{
          position: 'absolute',
          top: '-200px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <div style={{ position: 'relative', zIndex: 1, maxWidth: '800px', margin: '0 auto' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 16px',
            background: 'rgba(99,102,241,0.1)',
            border: '1px solid rgba(99,102,241,0.2)',
            borderRadius: '20px',
            fontSize: '13px',
            color: 'var(--accent-primary)',
            fontWeight: 600,
            marginBottom: '24px',
          }}>
            🚀 Powered by GenAI + Multi-Agent System
          </div>

          <h1 style={{
            fontSize: '64px',
            fontWeight: 900,
            lineHeight: 1.1,
            marginBottom: '24px',
            background: 'var(--gradient-hero)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            ScholarGraph AI
          </h1>

          <p style={{
            fontSize: '22px',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            marginBottom: '12px',
            fontWeight: 300,
          }}>
            From Information Overload to <strong style={{ color: 'var(--text-primary)' }}>Exam Intelligence</strong>
          </p>

          <p style={{
            fontSize: '16px',
            color: 'var(--text-muted)',
            maxWidth: '600px',
            margin: '0 auto 40px',
            lineHeight: 1.7,
          }}>
            Upload your syllabus, past year papers, and lecture notes. Our AI predicts which topics 
            will appear on your exam with quantitative Probability Scores.
          </p>

          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
            <Link href="/chat" className="btn-primary" style={{ fontSize: '17px', padding: '16px 36px' }}>
              💬 Chat with AI
            </Link>
            <Link href="/dashboard" className="btn-secondary" style={{ fontSize: '17px', padding: '16px 36px' }}>
              📊 Dashboard
            </Link>
            <Link href="/upload" className="btn-secondary" style={{ fontSize: '17px', padding: '16px 36px' }}>
              📄 Upload Documents
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section style={{ padding: '0 24px 80px', maxWidth: '1200px', margin: '0 auto' }}>
        <div className="grid-3">
          {[
            {
              icon: '🎯',
              title: 'Probability Scores',
              desc: 'Quantitative prediction of which topics will appear on your exam, scored 0-100 with HIGH/MEDIUM/LOW priority.',
              color: '#ef4444',
            },
            {
              icon: '🕸️',
              title: 'Knowledge Graphs',
              desc: 'Interactive D3.js force-directed graphs showing topic relationships, prerequisites, and exam patterns.',
              color: '#8b5cf6',
            },
            {
              icon: '🤖',
              title: '8-Agent AI System',
              desc: 'LangGraph-powered multi-agent workflow: classifies, extracts, maps, analyzes, predicts, plans, quizzes, tracks.',
              color: '#3b82f6',
            },
            {
              icon: '📚',
              title: 'Hierarchical RAG',
              desc: '3-layer retrieval across syllabus, past papers, and lecture notes for comprehensive analysis.',
              color: '#10b981',
            },
            {
              icon: '🧠',
              title: 'Adaptive Quizzes',
              desc: 'LLM-generated MCQs that adapt difficulty based on your performance and mastery level.',
              color: '#f59e0b',
            },
            {
              icon: '📈',
              title: 'Performance Tracking',
              desc: 'Identify knowledge gaps, track mastery progress, and get personalized study recommendations.',
              color: '#ec4899',
            },
          ].map((f, i) => (
            <div key={i} className="glass-card animate-fadeInUp" style={{ animationDelay: `${i * 0.1}s` }}>
              <div style={{
                fontSize: '40px',
                marginBottom: '16px',
                width: '64px',
                height: '64px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '16px',
                background: `${f.color}15`,
                border: `1px solid ${f.color}30`,
              }}>
                {f.icon}
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '8px' }}>{f.title}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.6 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Probability Score Demo */}
      <section style={{ padding: '0 24px 80px', maxWidth: '900px', margin: '0 auto' }}>
        <div className="glass-card" style={{ padding: '40px' }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: 800,
            marginBottom: '8px',
            textAlign: 'center',
            background: 'var(--gradient-hero)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            Topic Probability Score Engine
          </h2>
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '32px', fontSize: '14px' }}>
            Score = (0.40 × Frequency) + (0.35 × Semantic Similarity) + (0.25 × Recency Weight)
          </p>

          {[
            { topic: 'Neural Networks & Backpropagation', score: 92, years: '2020, 2021, 2022, 2024', priority: 'HIGH' },
            { topic: 'Convolutional Neural Networks', score: 78, years: '2020, 2022, 2024', priority: 'HIGH' },
            { topic: 'Support Vector Machines', score: 55, years: '2019, 2021', priority: 'MEDIUM' },
            { topic: 'Bayesian Networks', score: 32, years: '2018', priority: 'LOW' },
          ].map((t, i) => (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              padding: '16px 0',
              borderBottom: i < 3 ? '1px solid var(--border-color)' : 'none',
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '15px' }}>{t.topic}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '4px' }}>
                  Tested in: {t.years}
                </div>
              </div>
              <div style={{ textAlign: 'right', minWidth: '80px' }}>
                <div style={{ 
                  fontSize: '24px', 
                  fontWeight: 800, 
                  color: t.priority === 'HIGH' ? 'var(--high-priority)' : t.priority === 'MEDIUM' ? 'var(--medium-priority)' : 'var(--low-priority)'
                }}>
                  {t.score}%
                </div>
                <span className={`badge badge-${t.priority.toLowerCase()}`}>{t.priority}</span>
              </div>
              <div style={{ width: '120px' }}>
                <div className="score-bar-container">
                  <div
                    className={`score-bar-fill score-bar-${t.priority.toLowerCase()}`}
                    style={{ width: `${t.score}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '40px 24px',
        borderTop: '1px solid var(--border-color)',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '13px',
      }}>
        <p>
          <strong style={{ color: 'var(--text-secondary)' }}>ScholarGraph AI</strong> — Team Enxapse
        </p>
        <p>Built with FastAPI, LangGraph, Pinecone, Next.js, and D3.js</p>
      </footer>
    </div>
  );
}
