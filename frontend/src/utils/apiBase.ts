/**
 * API base URL for banking (and academy) requests.
 * Uses VITE_API_BASE_URL at build time, or derives from current path when
 * deployed under e.g. /banking-platform/v1 so requests hit the same origin.
 */
export function getBankingApiBase(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined') {
    const path = window.location.pathname;
    // Deployed under /banking-platform/v1/...
    const m = path.match(/^(\/banking-platform\/v1)/);
    if (m) return m[1];
  }
  return 'http://localhost:8002';
}
