/**
 * API base URL for banking (and academy) requests.
 *
 * FastAPI registers routes at /api/... on the app root. Do NOT prefix with the
 * Vite SPA base (e.g. /banking-platform/v1)  -  that produces URLs like
 * /banking-platform/v1/api/... which only match the SPA catch-all GET route,
 * so POST returns 405 Method Not Allowed.
 *
 * Use '' in the browser → fetch('/api/...') hits the same host's /api (Databricks
 * single-port, or Vite dev proxy). Set VITE_API_BASE_URL only when the API is on
 * another origin (e.g. http://localhost:8002).
 */
export function getBankingApiBase(): string {
  const env = import.meta.env.VITE_API_BASE_URL;
  if (typeof env === 'string' && env.trim() !== '') {
    return env.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined') {
    return '';
  }
  return 'http://localhost:8002';
}
