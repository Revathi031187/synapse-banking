import React from 'react';

// ── Markdown renderer ─────────────────────────────────────────────────────────
// Shared by SegmentAIPanel and BankingAskGenie (both render the same chatbot
// response shape) — hand-rolled rather than a markdown library so the exact
// visual language (violet accents, compact spacing) stays consistent with the
// rest of the chat UI.

export function renderInline(text: string, key: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|`[^`]+`)/);
  return (
    <React.Fragment key={key}>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**'))
          return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
        if (part.startsWith('__') && part.endsWith('__'))
          return <u key={i} className="underline decoration-slate-400">{part.slice(2, -2)}</u>;
        if (part.startsWith('*') && part.endsWith('*'))
          return <em key={i} className="italic text-slate-700">{part.slice(1, -1)}</em>;
        if (part.startsWith('`') && part.endsWith('`'))
          return <code key={i} className="bg-violet-50 text-violet-700 px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
        return part;
      })}
    </React.Fragment>
  );
}

export function NarrativeMarkdown({ text }: { text: string }) {
  const processed = React.useMemo(() => {
    let t = text;
    t = t.replace(/\\n/g, '\n');
    t = t.replace(/\\ *\n/g, '\n');
    t = t.replace(/\\$/gm, '');
    t = t.replace(/([.!?;:]) ([*-] (?=[A-Z*`\d]))/g, '$1\n$2');
    t = t.replace(/([^\n]) (## )/g, '$1\n$2');
    t = t.replace(/([^\n]) (### )/g, '$1\n$2');
    t = t.replace(/([.!?]) (\*\*Recommendation)/g, '$1\n\n$2');
    return t;
  }, [text]);

  const lines = processed.split('\n');
  const elements: React.ReactNode[] = [];
  let bulletBuffer: React.ReactNode[] = [];
  let numberedBuffer: React.ReactNode[] = [];
  let idx = 0;

  const flushBullets = () => {
    if (bulletBuffer.length > 0) {
      elements.push(
        <ul key={`ul-${idx++}`} className="mt-1.5 mb-1.5 space-y-0.5 pl-1">
          {bulletBuffer}
        </ul>
      );
      bulletBuffer = [];
    }
  };

  const flushNumbered = () => {
    if (numberedBuffer.length > 0) {
      elements.push(
        <ol key={`ol-${idx++}`} className="mt-1.5 mb-1.5 space-y-0.5 pl-5 list-decimal marker:text-violet-500 marker:font-semibold">
          {numberedBuffer}
        </ol>
      );
      numberedBuffer = [];
    }
  };

  lines.forEach((line, i) => {
    const isBullet = line.startsWith('- ') || line.startsWith('• ') || line.startsWith('* ');
    const numberedMatch = /^(\d+)\.\s+(.*)$/.exec(line);
    const isNumbered = !!numberedMatch;

    if (!isBullet) flushBullets();
    if (!isNumbered) flushNumbered();

    if (/^## /.test(line)) {
      elements.push(
        <p key={i} className="font-bold text-sm text-slate-900 mt-3 mb-1">
          {renderInline(line.slice(3), `h2-${i}`)}
        </p>
      );
    } else if (/^### /.test(line)) {
      elements.push(
        <p key={i} className="font-semibold text-sm text-slate-800 mt-2 mb-0.5">
          {renderInline(line.slice(4), `h3-${i}`)}
        </p>
      );
    } else if (isBullet) {
      bulletBuffer.push(
        <li key={i} className="flex items-start gap-1.5">
          <span className="mt-1.5 w-1 h-1 rounded-full bg-violet-400 flex-shrink-0" />
          <span className="text-sm text-slate-700 leading-relaxed">
            {renderInline(line.slice(2), `li-${i}`)}
          </span>
        </li>
      );
    } else if (isNumbered) {
      numberedBuffer.push(
        <li key={i} className="text-sm text-slate-700 leading-relaxed pl-1">
          {renderInline(numberedMatch![2], `li-num-${i}`)}
        </li>
      );
    } else if (line.trim() === '') {
      elements.push(<div key={i} className="h-1.5" />);
    } else {
      elements.push(
        <p key={i} className="text-sm text-slate-700 leading-relaxed">
          {renderInline(line, `p-${i}`)}
        </p>
      );
    }
  });

  flushBullets();
  flushNumbered();
  return <div className="space-y-0.5">{elements}</div>;
}
