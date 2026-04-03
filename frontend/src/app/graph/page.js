'use client';

import { useState } from 'react';
import Navbar from '../../components/Navbar';
import KnowledgeGraph from '../../components/KnowledgeGraph';
import { apiUrl } from '../../lib/api';

const SAMPLE_GRAPH = {
  nodes: [
    { id: 'neural_networks', name: 'Neural Networks', probability_score: 92, priority: 'HIGH PRIORITY', difficulty: 'hard', mastery_score: 65, group: 1, type: 'topic' },
    { id: 'backpropagation', name: 'Backpropagation', probability_score: 88, priority: 'HIGH PRIORITY', difficulty: 'hard', mastery_score: 55, group: 1, type: 'concept' },
    { id: 'cnn', name: 'CNN', probability_score: 78, priority: 'HIGH PRIORITY', difficulty: 'hard', mastery_score: 45, group: 1, type: 'topic' },
    { id: 'rnn_lstm', name: 'RNN & LSTM', probability_score: 65, priority: 'MEDIUM PRIORITY', difficulty: 'hard', mastery_score: 30, group: 2, type: 'topic' },
    { id: 'svm', name: 'SVM', probability_score: 55, priority: 'MEDIUM PRIORITY', difficulty: 'medium', mastery_score: 70, group: 2, type: 'topic' },
    { id: 'decision_trees', name: 'Decision Trees', probability_score: 48, priority: 'MEDIUM PRIORITY', difficulty: 'easy', mastery_score: 80, group: 2, type: 'topic' },
    { id: 'gradient_descent', name: 'Gradient Descent', probability_score: 85, priority: 'HIGH PRIORITY', difficulty: 'medium', mastery_score: 60, group: 1, type: 'concept' },
    { id: 'regularization', name: 'Regularization', probability_score: 62, priority: 'MEDIUM PRIORITY', difficulty: 'medium', mastery_score: 50, group: 2, type: 'concept' },
    { id: 'bayesian', name: 'Bayesian Networks', probability_score: 28, priority: 'LOW PRIORITY', difficulty: 'hard', mastery_score: 20, group: 3, type: 'topic' },
    { id: 'random_forests', name: 'Random Forests', probability_score: 42, priority: 'MEDIUM PRIORITY', difficulty: 'medium', mastery_score: 75, group: 2, type: 'topic' },
    { id: 'linear_algebra', name: 'Linear Algebra', probability_score: 35, priority: 'LOW PRIORITY', difficulty: 'medium', mastery_score: 85, group: 3, type: 'concept' },
    { id: 'activation_functions', name: 'Activation Functions', probability_score: 72, priority: 'HIGH PRIORITY', difficulty: 'easy', mastery_score: 90, group: 1, type: 'concept' },
  ],
  links: [
    { source: 'neural_networks', target: 'backpropagation', type: 'dependency', weight: 0.9 },
    { source: 'neural_networks', target: 'cnn', type: 'prerequisite', weight: 0.85 },
    { source: 'neural_networks', target: 'rnn_lstm', type: 'prerequisite', weight: 0.8 },
    { source: 'gradient_descent', target: 'backpropagation', type: 'dependency', weight: 0.95 },
    { source: 'neural_networks', target: 'activation_functions', type: 'dependency', weight: 0.88 },
    { source: 'linear_algebra', target: 'neural_networks', type: 'prerequisite', weight: 0.7 },
    { source: 'linear_algebra', target: 'svm', type: 'prerequisite', weight: 0.6 },
    { source: 'decision_trees', target: 'random_forests', type: 'dependency', weight: 0.92 },
    { source: 'regularization', target: 'neural_networks', type: 'correlation', weight: 0.65 },
    { source: 'regularization', target: 'svm', type: 'correlation', weight: 0.55 },
    { source: 'svm', target: 'bayesian', type: 'correlation', weight: 0.4 },
    { source: 'gradient_descent', target: 'regularization', type: 'correlation', weight: 0.6 },
  ],
};

export default function GraphPage() {
  const [subject, setSubject] = useState('');
  const [graphData, setGraphData] = useState(SAMPLE_GRAPH);
  const [loading, setLoading] = useState(false);

  const fetchGraph = async () => {
    if (!subject.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(apiUrl(`/api/graph/${encodeURIComponent(subject)}`));
      const data = await res.json();
      if (data.nodes?.length > 0) setGraphData(data);
    } catch {
      /* Keep sample data */
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ padding: '24px' }}>
        <div className="page-header">
          <h1>🕸️ Knowledge Graph</h1>
          <p>Interactive topic relationship visualization</p>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
          <input
            className="input"
            placeholder="Enter subject to load graph"
            value={subject}
            onChange={e => setSubject(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetchGraph()}
            style={{ flex: 1 }}
          />
          <button className="btn-primary" onClick={fetchGraph} disabled={loading}>
            {loading ? '⏳ Loading...' : '🕸️ Load Graph'}
          </button>
        </div>

        <KnowledgeGraph data={graphData} width={1200} height={650} />

        <div className="glass-card" style={{ marginTop: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>📊 Graph Statistics</h3>
          <div className="grid-4">
            <div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--accent-primary)' }}>{graphData?.nodes?.length || 0}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Nodes</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--accent-primary)' }}>{graphData?.links?.length || 0}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Edges</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--high-priority)' }}>
                {graphData?.nodes?.filter(n => n.group === 1).length || 0}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>High Priority</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--low-priority)' }}>
                {graphData?.nodes?.filter(n => n.group === 3).length || 0}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Low Priority</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
