'use client';

import { useState } from 'react';
import Navbar from '../../components/Navbar';
import { apiUrl } from '../../lib/api';

export default function QuizPage() {
  const [subject, setSubject] = useState('');
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentQ, setCurrentQ] = useState(0);

  const generateQuiz = async () => {
    if (!subject.trim()) return;
    setLoading(true);
    setResults(null);
    setAnswers({});
    setCurrentQ(0);

    try {
      const res = await fetch(apiUrl('/api/quiz/generate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject, topic, difficulty, count: 5 }),
      });
      const data = await res.json();
      setQuiz(data);
    } catch {
      setQuiz({
        subject,
        total_questions: 3,
        questions: [
          {
            question: `What is the primary purpose of ${topic || subject}?`,
            options: { A: 'Data storage', B: 'Pattern recognition and learning from data', C: 'Network security', D: 'Hardware optimization' },
            correct_answer: 'B', difficulty, topic: topic || subject,
            explanation: `${topic || subject} is fundamentally about pattern recognition and learning.`,
          },
          {
            question: `Which algorithm is commonly used in ${topic || subject}?`,
            options: { A: 'Bubble Sort', B: 'Gradient Descent', C: 'Binary Search', D: 'Dijkstra\'s Algorithm' },
            correct_answer: 'B', difficulty, topic: topic || subject,
            explanation: 'Gradient Descent is widely used for optimization in ML models.',
          },
          {
            question: `What is overfitting in the context of ${topic || subject}?`,
            options: { A: 'Model performs well on all data', B: 'Model is too simple', C: 'Model memorizes training data but fails on new data', D: 'Model runs too slowly' },
            correct_answer: 'C', difficulty, topic: topic || subject,
            explanation: 'Overfitting occurs when a model learns noise instead of patterns.',
          },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const selectAnswer = (qIndex, option) => {
    if (results) return;
    setAnswers({ ...answers, [qIndex]: option });
  };

  const submitQuiz = async () => {
    if (!quiz) return;
    const correct = quiz.questions.reduce((count, q, i) =>
      count + (answers[i]?.toUpperCase() === q.correct_answer.toUpperCase() ? 1 : 0), 0
    );
    const total = quiz.questions.length;
    const score = Math.round(correct / total * 100);

    setResults({
      score,
      correct,
      total,
      grade: score >= 90 ? 'A+' : score >= 80 ? 'A' : score >= 70 ? 'B' : score >= 60 ? 'C' : score >= 50 ? 'D' : 'F',
    });
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
        <div className="page-header">
          <h1>🧠 Adaptive Quiz</h1>
          <p>Test your knowledge with AI-generated questions</p>
        </div>

        {!quiz ? (
          <div className="glass-card">
            <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '20px' }}>Generate Quiz</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <input className="input" placeholder="Subject (e.g. Machine Learning)" value={subject}
                onChange={e => setSubject(e.target.value)} />
              <input className="input" placeholder="Topic (optional)" value={topic}
                onChange={e => setTopic(e.target.value)} />
              <div style={{ display: 'flex', gap: '8px' }}>
                {['easy', 'medium', 'hard'].map(d => (
                  <button key={d} onClick={() => setDifficulty(d)}
                    style={{
                      flex: 1, padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid',
                      borderColor: difficulty === d ? 'var(--accent-primary)' : 'var(--border-color)',
                      background: difficulty === d ? 'rgba(99,102,241,0.1)' : 'var(--bg-secondary)',
                      color: difficulty === d ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      cursor: 'pointer', fontWeight: 600, textTransform: 'capitalize', fontSize: '14px',
                    }}>
                    {d === 'easy' ? '🟢' : d === 'medium' ? '🟡' : '🔴'} {d}
                  </button>
                ))}
              </div>
              <button className="btn-primary" onClick={generateQuiz} disabled={loading}
                style={{ width: '100%', justifyContent: 'center', fontSize: '16px', padding: '16px' }}>
                {loading ? '⏳ Generating...' : '🧠 Start Quiz'}
              </button>
            </div>
          </div>
        ) : (
          <div className="animate-fadeInUp">
            {/* Progress */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
              <div style={{ flex: 1 }}>
                <div className="score-bar-container" style={{ height: '6px' }}>
                  <div style={{
                    width: `${results ? 100 : (Object.keys(answers).length / quiz.questions.length * 100)}%`,
                    height: '100%', background: 'var(--gradient-hero)', borderRadius: '4px', transition: 'width 0.3s ease',
                  }} />
                </div>
              </div>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                {Object.keys(answers).length}/{quiz.questions.length} answered
              </span>
            </div>

            {/* Results Banner */}
            {results && (
              <div className="glass-card animate-fadeInUp" style={{
                marginBottom: '24px', textAlign: 'center', padding: '32px',
                background: results.score >= 70 ? 'rgba(16,185,129,0.05)' : 'rgba(239,68,68,0.05)',
                border: `1px solid ${results.score >= 70 ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
              }}>
                <div style={{ fontSize: '64px', fontWeight: 900, color: results.score >= 70 ? 'var(--low-priority)' : 'var(--high-priority)' }}>
                  {results.score}%
                </div>
                <div style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px' }}>Grade: {results.grade}</div>
                <div style={{ color: 'var(--text-secondary)' }}>{results.correct}/{results.total} correct answers</div>
              </div>
            )}

            {/* Questions */}
            {quiz.questions.map((q, qi) => (
              <div key={qi} className="glass-card" style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                  <span style={{
                    background: 'var(--accent-primary)', color: 'white', width: '28px', height: '28px',
                    borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '13px', fontWeight: 700, flexShrink: 0,
                  }}>{qi + 1}</span>
                  <p style={{ fontSize: '15px', fontWeight: 600, lineHeight: 1.5 }}>{q.question}</p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(q.options).map(([key, value]) => {
                    let cls = 'quiz-option';
                    if (answers[qi] === key) cls += ' selected';
                    if (results) {
                      if (key === q.correct_answer) cls += ' correct';
                      else if (answers[qi] === key && key !== q.correct_answer) cls += ' incorrect';
                    }
                    return (
                      <div key={key} className={cls} onClick={() => selectAnswer(qi, key)}>
                        <span style={{
                          width: '28px', height: '28px', borderRadius: '50%', display: 'flex',
                          alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700,
                          background: answers[qi] === key ? 'var(--accent-primary)' : 'var(--bg-card)',
                          color: answers[qi] === key ? 'white' : 'var(--text-secondary)', flexShrink: 0,
                        }}>{key}</span>
                        <span style={{ fontSize: '14px' }}>{value}</span>
                      </div>
                    );
                  })}
                </div>

                {results && (
                  <div style={{
                    marginTop: '12px', padding: '12px', borderRadius: 'var(--radius-sm)',
                    background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)',
                    fontSize: '13px', color: 'var(--text-secondary)',
                  }}>
                    💡 {q.explanation}
                  </div>
                )}
              </div>
            ))}

            {/* Actions */}
            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              {!results ? (
                <button className="btn-primary" onClick={submitQuiz}
                  disabled={Object.keys(answers).length < quiz.questions.length}
                  style={{ flex: 1, justifyContent: 'center', fontSize: '16px', padding: '16px' }}>
                  ✅ Submit Answers
                </button>
              ) : (
                <button className="btn-primary" onClick={() => { setQuiz(null); setResults(null); setAnswers({}); }}
                  style={{ flex: 1, justifyContent: 'center', fontSize: '16px', padding: '16px' }}>
                  🔄 New Quiz
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
