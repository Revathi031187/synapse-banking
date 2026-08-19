import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Search, User } from 'lucide-react';

export interface CustomerSearchOption {
  customer_id: string;
  customer_name?: string;
  [key: string]: unknown;
}

interface CustomerSearchSelectProps {
  customers: CustomerSearchOption[];
  value: string;
  onChange: (customerId: string, customer?: CustomerSearchOption) => void;
  loading?: boolean;
  loadingLabel?: string;
  /** Shown when `customers` is empty (not while loading) */
  emptyListLabel?: string;
  placeholder?: string;
  maxResults?: number;
  disabled?: boolean;
  className?: string;
}

function labelFor(c: CustomerSearchOption | undefined, fallbackId: string): string {
  if (!c) return fallbackId;
  return c.customer_name ? `${c.customer_name} (${c.customer_id})` : String(c.customer_id);
}

/** Higher = closer match. -1 = no match at all. */
function matchScore(query: string, text?: string | null): number {
  if (!text) return -1;
  const t = String(text).toLowerCase();
  if (t === query) return 1000;
  if (t.startsWith(query)) return 900 - t.length;
  const idx = t.indexOf(query);
  if (idx >= 0) return 700 - idx;
  // Fuzzy subsequence match: every query char appears in order somewhere in text
  let ti = 0;
  for (let qi = 0; qi < query.length; qi++) {
    const found = t.indexOf(query[qi], ti);
    if (found === -1) return -1;
    ti = found + 1;
  }
  return 300 - (t.length - query.length);
}

/** Text input + dynamic dropdown: closest name/ID matches, or an explicit "no results" state. */
export default function CustomerSearchSelect({
  customers,
  value,
  onChange,
  loading = false,
  loadingLabel = 'Loading customers…',
  emptyListLabel = 'No customers available.',
  placeholder = 'Search by name or customer ID…',
  maxResults = 8,
  disabled = false,
  className = '',
}: CustomerSearchSelectProps) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const lastSyncedValue = useRef<string | null>(null);
  const [dropdownRect, setDropdownRect] = useState<{ top: number; left: number; width: number } | null>(null);

  // Keep the input text in sync with externally-driven selection changes
  // (e.g. a "Get offer" button elsewhere selecting a customer), without
  // clobbering what the user is actively typing.
  useEffect(() => {
    if (value === lastSyncedValue.current) return;
    lastSyncedValue.current = value;
    const match = customers.find((c) => String(c.customer_id) === String(value));
    setQuery(value ? labelFor(match, value) : '');
  }, [value, customers]);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDocMouseDown(e: MouseEvent) {
      const target = e.target as Node;
      if (containerRef.current?.contains(target)) return;
      if (dropdownRef.current?.contains(target)) return;
      setOpen(false);
    }
    document.addEventListener('mousedown', onDocMouseDown);
    return () => document.removeEventListener('mousedown', onDocMouseDown);
  }, []);

  // The dropdown renders in a portal (to escape clipping by any ancestor's
  // overflow-hidden/scroll container), so its position has to be measured
  // from the input's real screen coordinates and kept in sync while open.
  useEffect(() => {
    if (!open) return;
    function updateRect() {
      const rect = containerRef.current?.getBoundingClientRect();
      if (rect) setDropdownRect({ top: rect.bottom + 6, left: rect.left, width: rect.width });
    }
    updateRect();
    window.addEventListener('scroll', updateRect, true);
    window.addEventListener('resize', updateRect);
    return () => {
      window.removeEventListener('scroll', updateRect, true);
      window.removeEventListener('resize', updateRect);
    };
  }, [open]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return customers
      .map((c) => ({
        customer: c,
        score: Math.max(matchScore(q, c.customer_name), matchScore(q, c.customer_id)),
      }))
      .filter((r) => r.score >= 0)
      .sort((a, b) => b.score - a.score || String(a.customer.customer_name ?? '').localeCompare(String(b.customer.customer_name ?? '')))
      .slice(0, maxResults)
      .map((r) => r.customer);
  }, [customers, query, maxResults]);

  const trimmedQuery = query.trim();

  function selectCustomer(c: CustomerSearchOption) {
    lastSyncedValue.current = String(c.customer_id);
    setQuery(labelFor(c, c.customer_id));
    setOpen(false);
    onChange(c.customer_id, c);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      setOpen(true);
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, Math.max(results.length - 1, 0)));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === 'Enter') {
      if (open && results[highlight]) {
        e.preventDefault();
        selectCustomer(results[highlight]);
      }
    } else if (e.key === 'Escape') {
      setOpen(false);
      inputRef.current?.blur();
    }
  }

  useEffect(() => {
    setHighlight(0);
  }, [query]);

  const showEmptyListNotice = !loading && customers.length === 0;

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
          disabled={disabled || loading || showEmptyListNotice}
          placeholder={loading ? loadingLabel : showEmptyListNotice ? emptyListLabel : placeholder}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={(e) => {
            setOpen(true);
            e.target.select();
          }}
          onKeyDown={handleKeyDown}
          className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-slate-50 disabled:text-slate-400"
        />
      </div>

      {open &&
        !disabled &&
        !loading &&
        !showEmptyListNotice &&
        dropdownRect &&
        createPortal(
          <div
            ref={dropdownRef}
            role="listbox"
            onMouseDown={(e) => e.preventDefault()}
            className="fixed max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-lg"
            style={{ top: dropdownRect.top, left: dropdownRect.left, width: dropdownRect.width, zIndex: 9999 }}
          >
            {trimmedQuery === '' ? (
              <div className="px-4 py-3 text-sm text-slate-400">
                No results
                <div className="text-xs text-slate-400 mt-0.5">Start typing a customer name or ID to search.</div>
              </div>
            ) : results.length === 0 ? (
              <div className="px-4 py-3 text-sm text-slate-400">
                No results for &ldquo;{trimmedQuery}&rdquo;
              </div>
            ) : (
              results.map((c, i) => (
                <button
                  key={c.customer_id}
                  type="button"
                  role="option"
                  aria-selected={String(c.customer_id) === String(value)}
                  onClick={() => selectCustomer(c)}
                  onMouseEnter={() => setHighlight(i)}
                  className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-left border-b border-slate-100 last:border-0 transition-colors ${
                    i === highlight ? 'bg-blue-50' : 'bg-white'
                  } ${String(c.customer_id) === String(value) ? 'text-blue-700' : 'text-slate-800'}`}
                >
                  <User className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium truncate">{c.customer_name || c.customer_id}</p>
                    <p className="text-xs text-slate-500 truncate">{c.customer_id}</p>
                  </div>
                </button>
              ))
            )}
          </div>,
          document.body,
        )}
    </div>
  );
}
