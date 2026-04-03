'use client';

import { useState, useRef } from 'react';
import Navbar from '../../components/Navbar';
import { apiUrl, formatApiErrorDetail } from '../../lib/api';

export default function UploadPage() {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [subject, setSubject] = useState('');
  const [docType, setDocType] = useState('');
  const [semester, setSemester] = useState('');
  const [year, setYear] = useState('');
  const fileRef = useRef(null);

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject', subject);
    formData.append('doc_type', docType);
    formData.append('semester', semester);
    formData.append('year', year);

    try {
      const res = await fetch(apiUrl('/api/upload/'), { method: 'POST', body: formData });
      const data = await res.json();
      if (!res.ok) {
        const detail = formatApiErrorDetail(data.detail);
        setResult({ status: 'error', detail });
        return;
      }
      setResult(data);
    } catch (err) {
      const detail = err?.message || 'Upload failed. Make sure the backend is running (http://localhost:8000).';
      setResult({ status: 'error', detail });
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
        <div className="page-header">
          <h1>📄 Upload Documents</h1>
          <p>Upload syllabus, past year papers, or lecture notes for AI analysis</p>
        </div>

        {/* Form Fields */}
        <div className="grid-3" style={{ marginBottom: '24px' }}>
          <div>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
              Subject
            </label>
            <input
              className="input"
              placeholder="e.g. Machine Learning"
              value={subject}
              onChange={e => setSubject(e.target.value)}
            />
          </div>
          <div>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
              Document Type
            </label>
            <select
              className="input"
              value={docType}
              onChange={e => setDocType(e.target.value)}
              style={{ cursor: 'pointer' }}
            >
              <option value="">Auto-detect</option>
              <option value="syllabus">Syllabus</option>
              <option value="pyq">Past Year Questions (PYQ)</option>
              <option value="lecture_notes">Lecture Notes</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
              Year (for PYQ)
            </label>
            <input
              className="input"
              type="number"
              placeholder="e.g. 2024"
              value={year}
              onChange={e => setYear(e.target.value)}
            />
          </div>
        </div>

        {/* Upload Zone */}
        <div
          className={`upload-zone ${dragOver ? 'dragover' : ''}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => {
            e.preventDefault();
            setDragOver(false);
            handleUpload(e.dataTransfer.files[0]);
          }}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.png,.jpg,.docx"
            style={{ display: 'none' }}
            onChange={e => handleUpload(e.target.files[0])}
          />
          {uploading ? (
            <>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
              <p style={{ fontSize: '18px', fontWeight: 600, color: 'var(--accent-primary)' }}>
                Processing document...
              </p>
              <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '8px' }}>
                Extracting text, classifying, chunking, embedding, and storing
              </p>
            </>
          ) : (
            <>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📂</div>
              <p style={{ fontSize: '18px', fontWeight: 600 }}>
                Drag & drop your PDF here
              </p>
              <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '8px' }}>
                or click to browse • Supports PDF, PNG, JPG, DOCX
              </p>
            </>
          )}
        </div>

        {/* Results */}
        {result && (
          <div className="glass-card animate-fadeInUp" style={{ marginTop: '24px' }}>
            {result.status === 'success' ? (
              <>
                <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px', color: 'var(--low-priority)' }}>
                  ✅ Document Processed Successfully
                </h3>
                <div className="grid-3" style={{ marginBottom: '20px' }}>
                  <div className="stat-card">
                    <div className="stat-value" style={{ fontSize: '24px' }}>{result.pages}</div>
                    <div className="stat-label">Pages</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value" style={{ fontSize: '24px' }}>{result.chunks_created}</div>
                    <div className="stat-label">Chunks Created</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value" style={{ fontSize: '24px' }}>{result.vectors_stored}</div>
                    <div className="stat-label">Vectors Stored</div>
                  </div>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <strong style={{ fontSize: '14px' }}>Document Type:</strong>{' '}
                  <span className={`badge badge-${result.doc_type === 'pyq' ? 'high' : result.doc_type === 'syllabus' ? 'medium' : 'low'}`}>
                    {result.doc_type}
                  </span>
                </div>

                {result.topics_extracted?.length > 0 && (
                  <div>
                    <strong style={{ fontSize: '14px' }}>Extracted Topics:</strong>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
                      {result.topics_extracted.map((t, i) => (
                        <span key={i} style={{
                          padding: '4px 12px',
                          background: 'rgba(99,102,241,0.1)',
                          border: '1px solid rgba(99,102,241,0.2)',
                          borderRadius: '16px',
                          fontSize: '12px',
                          color: 'var(--accent-primary)',
                        }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div style={{ color: 'var(--high-priority)' }}>
                <h3 style={{ marginBottom: '8px' }}>❌ Processing Failed</h3>
                <p style={{ fontSize: '14px' }}>{formatApiErrorDetail(result.detail)}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
