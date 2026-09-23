import { Gift, Tag, Clock, CheckCircle2, PinOff } from 'lucide-react';

export interface PinnedOfferCardData {
  product_id?: string;
  product_name?: string;
  offer_name?: string;
  offer_type?: string;
  headline_value?: string;
  content_benefit_1?: string;
  content_benefit_2?: string;
  content_benefit_3?: string;
  days_remaining?: number | null;
  terms_summary?: string;
  /** Plain-English pin reason  -  used as a fallback body when there's no
   * richer marketing-offer content available (e.g. the Offer tab, which has
   * no offer-flyer copy of its own, only Agent D's pin reasoning text). */
  reason?: string;
}

/**
 * Shared "Director's pinned offer" card  -  used by both the Recommender and
 * Offer tabs so a pin looks identical wherever it surfaces. `onUnpin` clears
 * the pin (DELETE /api/banking/agent_d/pin/{customer_id}) so the caller can
 * refetch and show each agent's natural, unpinned pick in its place.
 */
export default function PinnedOfferCard({
  card,
  onUnpin,
  unpinning = false,
}: {
  card: PinnedOfferCardData;
  onUnpin?: () => void;
  unpinning?: boolean;
}) {
  const benefits = [card.content_benefit_1, card.content_benefit_2, card.content_benefit_3].filter(Boolean);
  return (
    <div className="relative mb-4 rounded-2xl overflow-hidden border border-indigo-200 shadow-md">
      {onUnpin && (
        <button
          type="button"
          onClick={onUnpin}
          disabled={unpinning}
          title="Unpin this recommendation"
          className="absolute top-2.5 right-2.5 z-10 inline-flex items-center gap-1 px-2 py-1 rounded-full bg-white/15 hover:bg-white/25 text-white text-[10px] font-semibold disabled:opacity-50 transition-colors"
        >
          <PinOff className="w-3 h-3" />
          {unpinning ? 'Unpinning…' : 'Unpin'}
        </button>
      )}
      {/* Gradient header */}
      <div className="bg-gradient-to-r from-indigo-700 via-violet-700 to-purple-700 px-5 py-4">
        <div className="flex items-start gap-3 justify-between pr-16">
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-200 mb-1 flex items-center gap-1.5">
              <Gift className="w-3 h-3" />
              Director's pinned offer · {card.product_name}
            </p>
            {card.offer_name && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/20 text-white text-xs font-semibold">
                <Tag className="w-3 h-3" />
                {card.offer_name}
              </span>
            )}
          </div>
          {card.days_remaining != null && card.days_remaining < 30 && (
            <span className="shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-400/90 text-amber-950 text-[11px] font-bold">
              <Clock className="w-3 h-3" />
              {card.days_remaining}d left
            </span>
          )}
        </div>
        {card.headline_value && (
          <p className="text-xl font-extrabold text-white mt-2.5 leading-tight">{card.headline_value}</p>
        )}
      </div>
      {/* Benefits, or a plain-English fallback reason when there's no richer offer content */}
      {(benefits.length > 0 || card.reason) && (
        <div className="bg-white px-5 py-3.5 space-y-2">
          {benefits.map((b, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-slate-700">
              <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
              <span>{b}</span>
            </div>
          ))}
          {benefits.length === 0 && card.reason && (
            <p className="text-sm text-slate-700 whitespace-pre-line">{card.reason}</p>
          )}
          {card.terms_summary && (
            <p className="text-[11px] text-slate-400 leading-relaxed border-t border-slate-100 pt-2.5 mt-2">
              {card.terms_summary}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
