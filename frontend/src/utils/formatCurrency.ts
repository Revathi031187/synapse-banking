/**
 * Compact USD for dashboards (e.g. $4.1M, $58.4K) — avoids long locale strings in cards.
 */
export function formatCompactUsd(value: number | null | undefined): string {
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);
  if (abs >= 1_000_000) {
    const m = abs / 1_000_000;
    const dec = m >= 100 ? 0 : 1;
    return `${sign}$${m.toFixed(dec)}M`;
  }
  if (abs >= 1_000) {
    const k = abs / 1_000;
    const dec = k >= 100 ? 0 : 1;
    return `${sign}$${k.toFixed(dec)}K`;
  }
  return `${sign}$${Math.round(abs).toLocaleString('en-US')}`;
}
