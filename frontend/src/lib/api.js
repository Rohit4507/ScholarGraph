/**
 * Base URL for backend API. Use this for all fetch() calls so upload and other
 * features work when the backend runs on a different port (e.g. 8000).
 * Next.js rewrites /api/* to the backend only for server-side; client-side
 * fetch needs to hit the backend directly or the same origin with rewrite.
 */
export const API_BASE =
  typeof process.env.NEXT_PUBLIC_API_URL !== 'undefined' &&
  process.env.NEXT_PUBLIC_API_URL !== ''
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '')
    : 'http://localhost:8000';

export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${p}`;
}

/** Turn API error detail (string, array of {msg}, or object) into a string for display. */
export function formatApiErrorDetail(detail) {
  if (detail == null) return 'Unknown error';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(d => (d?.msg != null ? d.msg : JSON.stringify(d))).join('. ');
  return JSON.stringify(detail);
}
