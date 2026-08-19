"""
LLM client for the JPMorgan Chase banking personalization platform.

Uses Together AI (Llama 3.3 70B) by default — no new credentials needed,
the TOGETHER_API_KEY already in .env is sufficient.

If ANTHROPIC_API_KEY is set, switches to Claude Haiku 4.5 automatically.

All public methods return empty strings / empty lists / empty dicts on failure —
never raise. Callers fall back to rule-based logic transparently.
"""

import os
import time
import json
import logging
from pathlib import Path

from utils.token_tracker import log_llm_call

logger = logging.getLogger(__name__)

# ── load .env ─────────────────────────────────────────────────────────────────
_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

# ── backend selection ─────────────────────────────────────────────────────────
_ANTHROPIC_KEY   = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
_TOGETHER_KEY    = (os.getenv("TOGETHER_API_KEY") or "").strip()
_TOGETHER_BASE   = "https://api.together.xyz/v1"

# High-quality Together AI models for segment naming and rationale.
# Llama 3.3 70B gives GPT-4-class quality for concise generation tasks. Confirmed
# working again via direct API test on 2026-07-29 (3/3 successful calls, ~4-10s each)
# after an earlier session saw HTTP 400 "non-serverless model" on every attempt —
# that was transient (a 503 showed up on retry too), not a permanent account
# restriction. Qwen2.5-7B kept as a fast, confirmed-working fallback in case the
# larger models flake out again.
_TOGETHER_MODELS = [
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "Qwen/Qwen2.5-72B-Instruct-Turbo",
    "Qwen/Qwen2.5-7B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3-8B-Instruct-Lite",
]

# Circuit breaker settings
_CB_FAILURE_THRESHOLD = 3
_CB_COOLDOWN_SECONDS  = 60

# ── module-level singleton ────────────────────────────────────────────────────
_claude_client = None

def get_claude_client():
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client


class ClaudeClient:
    """
    Unified LLM client:
    - Primary: Together AI (Llama 3.3 70B) using existing TOGETHER_API_KEY
    - Optional override: Anthropic Claude Haiku if ANTHROPIC_API_KEY is set
    - Circuit breaker: 3 consecutive failures -> 60s cooldown
    """

    def __init__(self):
        self._together_key = _TOGETHER_KEY
        self._anthropic_key = _ANTHROPIC_KEY
        self._consecutive_failures = 0
        self._circuit_open_until: float = 0.0

        # Try to load Anthropic SDK if key is present
        self._anthropic_client = None
        if self._anthropic_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=self._anthropic_key)
                logger.info("ClaudeClient: using Anthropic Claude Haiku (ANTHROPIC_API_KEY set)")
            except ImportError:
                logger.info("ClaudeClient: anthropic package not installed, using Together AI")
            except Exception as e:
                logger.warning("ClaudeClient: Anthropic init failed (%s), using Together AI", e)

        if not self._anthropic_client:
            if self._together_key:
                logger.info("ClaudeClient: using Together AI (Llama 3.3 70B) via TOGETHER_API_KEY")
            else:
                logger.warning("ClaudeClient: no API key found — LLM features will use rule-based fallbacks")

    # ── public ────────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        if time.time() < self._circuit_open_until:
            return False
        return bool(self._anthropic_client or self._together_key)

    def generate_text(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 50,
        temperature: float = 0.75,
        model: str = "",
        agent_name: str = "unknown",
        call_type: str = "general",
        first_line_only: bool = False,
    ) -> str:
        """
        Call the LLM and return the response text.
        Set first_line_only=True for single-word/single-line outputs (segment names).
        Returns "" on circuit-open, missing keys, or any error.
        """
        if not self.is_available():
            return ""

        t0 = time.monotonic()
        provider = "anthropic" if self._anthropic_client else "together"
        try:
            if self._anthropic_client:
                result, usage = self._call_anthropic(prompt, system, max_tokens, temperature, model)
            else:
                result, usage = self._call_together(prompt, system, max_tokens, temperature)

            if first_line_only:
                result = (result or "").strip().split("\n")[0].strip()
            else:
                result = (result or "").strip()

            duration_ms = int((time.monotonic() - t0) * 1000)
            self._consecutive_failures = 0
            log_llm_call(
                provider=provider,
                agent=agent_name,
                call_type=call_type,
                duration_ms=duration_ms,
                success=True,
                model=usage.get("model", model or ""),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                fallback_used=False,
            )
            return result

        except Exception as e:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._consecutive_failures += 1
            logger.warning(
                "LLM call failed (%d/%d): %s",
                self._consecutive_failures, _CB_FAILURE_THRESHOLD, e
            )
            if self._consecutive_failures >= _CB_FAILURE_THRESHOLD:
                self._circuit_open_until = time.time() + _CB_COOLDOWN_SECONDS
                logger.warning("Circuit breaker OPEN for %ds", _CB_COOLDOWN_SECONDS)
            log_llm_call(
                provider=provider,
                agent=agent_name,
                call_type=call_type,
                duration_ms=duration_ms,
                success=False,
                fallback_used=True,
                note=str(e)[:200],
            )
            return ""

    # ── high-level helpers ────────────────────────────────────────────────────

    def generate_segment_name(self, characteristics: dict, primary_trait: str, percentile: float, used_names: list = None) -> str:
        """Generate a 2–3 word banking segment name based on financial profile."""
        avg_deposits = characteristics.get("avg_deposits", 0)
        avg_income   = characteristics.get("avg_income", 0)
        avg_digital  = characteristics.get("avg_digital_engagement", 0.5)
        avg_products = characteristics.get("avg_products", 2.0)
        avg_txn      = characteristics.get("avg_transactions_per_customer", 20)

        taken = ", ".join(used_names) if used_names else "none yet"

        trait_hint = {
            "deposits":     f"highest balances (${avg_deposits:,.0f} avg deposits)",
            "digital":      f"most digital ({avg_digital*100:.0f}% online engagement)",
            "products":     f"most products ({avg_products:.1f} avg products held)",
            "transactions": f"most active ({avg_txn:.0f} monthly transactions)",
            "cross_sell":   f"most open to new products",
        }.get(primary_trait, primary_trait)

        prompt = (
            f"Name a retail banking customer persona. Describe WHO the customer IS, not just a metric.\n\n"
            f"Defining trait: {trait_hint} — {percentile:.0f}th percentile among all segments\n"
            f"Income: ${avg_income:,.0f}/yr  |  Products: {avg_products:.1f}  |  Digital: {avg_digital*100:.0f}%  |  Txns/mo: {avg_txn:.0f}\n\n"
            f"Already used names (must be DIFFERENT): {taken}\n\n"
            f"Good examples: 'Affluent Savers', 'Everyday Transactors', 'Digital-First Bankers', "
            f"'Multi-Product Holders', 'Branch-Loyal Seniors', 'Growth-Ready Professionals'\n"
            f"Bad names (avoid): 'Power Users', 'Core Actives', 'High Volume', anything vague or metric-only\n\n"
            f"Name (exactly 2 or 3 words, Title Case, describes the customer archetype):"
        )
        system = (
            "You are a bank marketing strategist naming customer personas. "
            "Output ONLY the segment name — exactly 2 or 3 words, Title Case. "
            "The name must describe the customer archetype (who they are), not just their metric rank. "
            "No punctuation, no explanation."
        )
        return self.generate_text(
            prompt=prompt, system=system, max_tokens=20, temperature=0.8,
            agent_name="agent_a", call_type="segment_name", first_line_only=True,
        )

    def generate_segment_profile(
        self,
        stats: dict,
        used_names: list = None,
        segment_type: str = "macro",
    ) -> dict:
        """
        Generate an archetype name AND narrative description for a banking segment in one LLM call.

        Returns {"name": "Wealth Builder", "description": "High-income ($142K)..."} or {} on failure.
        segment_type: "macro" for macro personas, "micro" for sub-segments.
        """
        if not self.is_available():
            return {}

        income   = stats.get('avg_income', 0)
        credit   = stats.get('avg_credit_score', 650)
        deposits = stats.get('avg_deposits', 0)
        digital  = stats.get('avg_digital_engagement', 0.5)
        products = stats.get('avg_products', 2.0)
        txn      = stats.get('avg_transactions', 20)
        churn    = stats.get('avg_churn_probability', 0.15)
        goal     = (stats.get('dominant_financial_goal') or '').replace('_', ' ')
        stage    = stats.get('dominant_life_stage', '')
        age      = stats.get('avg_age', 40)
        risk     = stats.get('dominant_risk_tolerance', 'Moderate')
        trait    = stats.get('primary_trait', 'deposits')
        clv      = stats.get('dominant_clv_tier', 'Silver')

        taken = ', '.join(used_names) if used_names else 'none yet'

        macro_parent   = stats.get('macro_parent', '')
        split_dims     = stats.get('split_dimensions', '')

        archetype_type = stats.get('archetype_type', '')
        parent_short   = stats.get('parent_short', '')
        feature_profile = stats.get('feature_profile', {})

        if segment_type == "micro":
            # Tight, simple prompt — models follow short clear instructions better than long ones
            diff = split_dims if split_dims else 'no strong differentiator'

            # Forbidden first words from sibling names already used
            forbidden_words = sorted({n.split()[0] for n in (used_names or []) if n.split()})
            forbidden_str = ', '.join(forbidden_words) if forbidden_words else 'none'
            # Show full sibling names so model avoids near-duplicates like "Senior" vs "Seasoned"
            siblings_str = ', '.join(f'"{n}"' for n in (used_names or [])) if used_names else 'none yet'

            # Archetype-unaware base banned list
            if "At-Risk" in macro_parent:
                banned = ""
            else:
                banned = "NEVER use: Borrower, Caution, Debt, Risky, Vulnerable.\n"

            # Archetype-aware semantic forbidden words — derived from macro parent name
            macro_lower = (macro_parent or '').lower()
            if any(w in macro_lower for w in ('retiree', 'anchor', 'loyal depositor', 'legacy', 'branch loyal', 'branch guardian')):
                banned += "ALSO NEVER use words that imply youth or early career: Young, Junior, New, Early, Entry, Student, Growing, Rising, Emerging.\n"
                extra_opts = ['Steady', 'Veteran', 'Conservative', 'Traditional']
                base_opts  = ['Active', 'Occasional', 'Established', 'Loyal', 'Selective', 'Focused']
            elif any(w in macro_lower for w in ('digital', 'native', 'mobile', 'app-first', 'pioneer')):
                banned += "ALSO NEVER use words that imply offline-only behaviour: Branch, Legacy, Traditional, Offline.\n"
                extra_opts = ['Mobile', 'Digital', 'Active', 'Frequent']
                base_opts  = ['Occasional', 'Established', 'Loyal', 'Selective', 'Focused', 'Open']
            elif any(w in macro_lower for w in ('wealth', 'premium', 'builder', 'high earner')):
                banned += "ALSO NEVER use words that imply financial difficulty: Poor, Stressed, Struggling, Marginal, Basic.\n"
                extra_opts = ['Selective', 'Strategic', 'Established', 'Focused']
                base_opts  = ['Active', 'Digital', 'Branch', 'Loyal', 'Open']
            else:
                extra_opts = []
                base_opts  = ['Digital', 'Branch', 'Active', 'Occasional', 'New', 'Established',
                               'Mobile', 'Loyal', 'Growing', 'Selective', 'Focused', 'Open']

            all_opts = extra_opts + [w for w in base_opts if w not in extra_opts]
            available = [w for w in all_opts if w not in forbidden_words][:4]
            available_str = ' / '.join(f"{w} {parent_short}" for w in available)

            prompt = (
                f"Name a sub-group inside the '{macro_parent}' banking segment.\n\n"
                f"What makes them different: {diff}\n"
                f"Age {age:.0f}, {products:.1f} products, {txn:.0f} transactions/month\n\n"
                f"NAME RULE: Exactly 2 words. Second word MUST be '{parent_short}'.\n"
                f"Names already used — yours must be DIFFERENT and NOT sound similar to these: {siblings_str}\n"
                f"FORBIDDEN first words: {forbidden_str}\n"
                f"{banned}"
                f"Available options (choose one or invent a clearly different unique word): {available_str}\n\n"
                f"DESCRIPTION: 2 plain-English sentences — what makes them different and what the bank can do.\n"
                f'Return ONLY: {{"name": "Word {parent_short}", "description": "2 sentences"}}'
            )
            max_tokens = 130
        else:
            # LLM generates BOTH name and description for the macro segment
            archetype_pools = {
                'HIGH-VALUE':    ('Wealth Builder', ['Wealth Builder', 'Premium Saver', 'High Earner']),
                'EVERYDAY':      ('Everyday Essential', ['Everyday Essential', 'Core Banker', 'Steady Saver']),
                'DIGITAL-FIRST': ('Digital Native', ['Digital Native', 'Mobile Pioneer', 'App-First Banker']),
                'LOYAL-STABLE':  ('Retiree Anchor', ['Retiree Anchor', 'Loyal Depositor', 'Branch Loyal']),
                'AT-RISK':       ('At-Risk Borrower', ['At-Risk Borrower', 'Rising Saver', 'Recovery Stage']),
            }
            canonical, pool = archetype_pools.get(archetype_type, ('', []))
            taken = ', '.join(used_names) if used_names else 'none yet'

            if archetype_type and pool:
                first_word = canonical.split()[0]
                name_instruction = (
                    f"SEGMENT TYPE: {archetype_type}\n"
                    f"NAME RULE: The first word of your name MUST be '{first_word}'. "
                    f"Only the second word may vary slightly.\n"
                    f"  CORRECT examples: '{canonical}', '{canonical}s', "
                    f"'{first_word} {pool[1].split()[-1] if len(pool) > 1 else canonical.split()[-1]}'\n"
                    f"  WRONG examples (do NOT do this): "
                    f"'Prosperity Builder', 'Stable Retirees', 'Vulnerable Investor', 'Rising Saver'\n"
                    f"  Names already taken (yours MUST be different): {taken}\n"
                )
            else:
                name_instruction = (
                    f"NAME STYLE — follow this exact format (simple, self-explanatory, 2-3 plain English words):\n"
                    f"  'Wealth Builder'     → high-income, savings-focused customers\n"
                    f"  'Everyday Essential' → middle-income, everyday banking customers\n"
                    f"  'Digital Native'     → young, tech-first customers\n"
                    f"  'Retiree Anchor'     → older, loyal, branch-preferring customers\n"
                    f"  'At-Risk Borrower'   → low-income, financially stretched customers\n"
                    f"  Names already taken (yours MUST be different): {taken}\n"
                )

            prompt = (
                f"{name_instruction}\n"
                f"Names already used (pick something DIFFERENT): {taken}\n\n"
                f"CUSTOMER STATS:\n"
                f"  Annual income: ${income:,.0f}  |  Credit score: {credit:.0f}  |  Savings: ${deposits:,.0f}\n"
                f"  Uses digital banking: {digital*100:.0f}%  |  Average age: {age:.0f}  |  Products held: {products:.1f}\n"
                f"  Transactions per month: {txn:.0f}  |  Financial goal: {goal}  |  Risk of leaving: {churn*100:.0f}%\n\n"
                f"Write 2-3 plain-English sentences explaining:\n"
                f"  1. Who these customers are (income level, age, lifestyle — make it human)\n"
                f"  2. Why the name fits — reference actual numbers\n"
                f"  3. What this means for the bank\n\n"
                f"LANGUAGE RULES — write for a bank manager presenting to executives:\n"
                f"  Say 'earns over $140,000 a year' NOT 'high income tier'\n"
                f"  Say 'rarely switches banks' NOT 'low churn probability'\n"
                f"  Say 'does most banking on their phone' NOT 'high digital engagement'\n"
                f"  NO jargon: avoid CLV, NPS, cross-sell, digital engagement score, portfolio depth\n\n"
                f'Return ONLY valid JSON: {{"name": "2-3 word name", "description": "plain-English description"}}\n'
                f'EXAMPLES OF PERFECT OUTPUT:\n'
                f'  {{"name": "Wealth Builder", "description": "These are the bank\'s most profitable customers, earning over $140K a year with excellent credit and large savings. They hold multiple banking products and almost never leave the bank. Primary goal: grow their wealth through smart investing."}}\n'
                f'  {{"name": "Retiree Anchor", "description": "Older, long-standing customers who have been with the bank for decades and keep solid savings. They strongly prefer branch banking over apps and have very low risk of leaving. They are the bank\'s most stable and loyal customer group."}}\n'
                f'  {{"name": "At-Risk Borrower", "description": "These customers face financial difficulty — lower incomes, stretched credit, and a higher chance of leaving the bank. They have near-zero savings and frequently overdraft. The bank\'s priority is retention and financial support, not upselling."}}'
            )
            max_tokens = 260

        system = (
            "You are a bank marketing strategist writing customer segment profiles. "
            "Output ONLY valid JSON with 'name' and 'description' keys. No markdown, no extra text."
        )
        temperature = 0.45 if segment_type == "micro" else 0.60
        raw = self.generate_text(
            prompt=prompt, system=system, max_tokens=max_tokens, temperature=temperature,
            agent_name="agent_a", call_type="segment_profile",
        )
        try:
            clean = (raw or '').strip()
            # strip any markdown fences
            for fence in ('```json', '```'):
                clean = clean.replace(fence, '')
            start = clean.find('{')
            end   = clean.rfind('}') + 1
            if start >= 0 and end > start:
                obj  = json.loads(clean[start:end])
                name = (obj.get('name') or '').strip()
                desc = (obj.get('description') or '').strip()
                if name:
                    return {'name': name, 'description': desc}
        except Exception as e:
            logger.warning("Segment profile JSON parse failed: %s — raw: %r", e, (raw or '')[:200])
        return {}

    def generate_micro_segment_name(self, macro_name: str, ltv_tier: str, characteristics: dict, used_names: list = None) -> str:
        """Generate a concise 2-word sub-segment name within a macro segment."""
        digital   = characteristics.get("avg_digital_engagement", 0.5)
        portfolio = characteristics.get("avg_portfolio_depth", 2.0)
        velocity  = characteristics.get("avg_transaction_velocity", 0.5)
        deposits  = characteristics.get("avg_deposits", 0)

        activity = "High Activity" if velocity > 1.0 else "Medium Activity" if velocity > 0.5 else "Low Activity"
        channel  = "Digital" if digital >= 0.65 else "Branch" if digital < 0.35 else "Hybrid"
        depth    = "Multi-Product" if portfolio >= 4 else "Focused" if portfolio < 2 else "Growing"
        taken    = ", ".join(used_names) if used_names else "none yet"

        # Words to explicitly avoid (macro name words + common tier words)
        macro_words = " / ".join(macro_name.split()[:3])

        prompt = (
            f"Create a unique 2-word banking sub-segment name.\n\n"
            f"Sub-group traits: {channel} channel, {depth} portfolio, {activity}\n"
            f"Deposits: ${deposits:,.0f}\n\n"
            f"Already used names (yours must be DIFFERENT): {taken}\n\n"
            f"Good names: 'Mobile Climbers', 'Branch Steady', 'App Builders', 'Loyal Spenders',\n"
            f"            'Rising Savers', 'Active Core', 'Digital Growers', 'Hybrid Loyal',\n"
            f"            'Frequent Movers', 'Steady Builders', 'Growth Ready', 'Deep Savers'\n\n"
            f"STRICT RULES:\n"
            f"- Exactly 2 words, Title Case\n"
            f"- NO parentheses anywhere in the output\n"
            f"- NO tier words: Gold, Silver, Platinum, Bronze, Elite, Premium\n"
            f"- DO NOT reuse any word from the parent macro name: {macro_words}\n"
            f"- Describe behavior or channel, not value tier\n\n"
            f"Name (2 words only):"
        )
        system = (
            "You are a banking strategist naming customer sub-segments. "
            "Output ONLY 2 words, Title Case. No parentheses, no tier words like Gold/Silver/Platinum/Bronze/Elite/Premium, no explanation."
        )
        return self.generate_text(
            prompt=prompt, system=system, max_tokens=15, temperature=0.75,
            agent_name="agent_a", call_type="micro_segment_name", first_line_only=True,
        )

    def generate_batch_rationale(self, top3_products: list, customer_info: dict, persona_name: str) -> dict:
        """
        One LLM call for top-3 product rationales.
        Returns {product_id: "1-sentence rationale"} or {} on failure.
        """
        if not self.is_available() or not top3_products:
            return {}

        product_lines = []
        for i, p in enumerate(top3_products[:3], 1):
            fee = p.get("annual_fee", p.get("monthly_fee", 0)) or 0
            product_lines.append(
                f"{i}. {p.get('product_name', p.get('product_id', 'Unknown'))} "
                f"(score {p.get('score', 0)*100:.0f}%, fee ${fee:.0f}/yr)"
            )

        life_stage     = str(customer_info.get("life_stage", "") or "")
        financial_goal = str(customer_info.get("financial_goal", "") or "").replace("_", " ")
        num_products   = int(float(customer_info.get("num_products", 0) or 0))
        primary_cat    = str(customer_info.get("primary_spending_category", "") or "")
        debt_total     = float(customer_info.get("outstanding_debt_total", 0) or 0)

        context_parts = []
        if life_stage:
            context_parts.append(f"life stage: {life_stage}")
        if financial_goal:
            context_parts.append(f"goal: {financial_goal}")
        if num_products:
            context_parts.append(f"holds {num_products} product(s)")
        if primary_cat:
            context_parts.append(f"top spend: {primary_cat}")
        if debt_total > 0:
            context_parts.append(f"outstanding debt: ${debt_total:,.0f}")

        extra_line = (f"Additional: {', '.join(context_parts)}\n" if context_parts else "")

        prompt = (
            f"Customer segment: {persona_name}\n"
            f"Profile: income ${customer_info.get('income', 0):,.0f}, "
            f"credit {customer_info.get('credit_score', 0)}, "
            f"deposits ${customer_info.get('total_deposits', 0):,.0f}\n"
            + extra_line +
            f"\nTop 3 Meridian Bank products:\n" + "\n".join(product_lines) +
            "\n\nWrite one sentence (max 18 words) explaining why each fits this customer. "
            "Reference a specific customer signal (goal, life stage, credit, or spending).\n"
            "Format:\n1: [rationale]\n2: [rationale]\n3: [rationale]"
        )
        system = (
            "You are a Meridian Bank relationship manager writing product recommendation rationales. "
            "Be specific — mention one customer signal per rationale."
        )
        raw = self.generate_text(
            prompt=prompt, system=system, max_tokens=120, temperature=0.6,
            agent_name="agent_b", call_type="batch_rationale",
        )

        result = {}
        for i, p in enumerate(top3_products[:3], 1):
            pid = p.get("product_id", str(i))
            for line in (raw or "").split("\n"):
                ls = line.strip()
                if ls.startswith(f"{i}:") or ls.startswith(f"{i}."):
                    text = ls.split(":", 1)[-1].strip().lstrip(".").strip()
                    if text:
                        result[pid] = text
                        break
        return result

    def generate_why_this_offer(
        self,
        product_name: str,
        persona_name: str,
        score: float,
        churn_category: str,
        customer_context: dict = None,
    ) -> list:
        """3 plain-English bullet points explaining the offer selection. Returns [] on failure."""
        cx = customer_context or {}
        income          = float(cx.get("income", 0) or 0)
        credit_score    = int(float(cx.get("credit_score", 0) or 0))
        life_stage      = str(cx.get("life_stage", "") or "")
        financial_goal  = str(cx.get("financial_goal", "") or "").replace("_", " ")
        debt_total      = float(cx.get("outstanding_debt_total", 0) or 0)
        has_competitor  = bool(cx.get("has_competitor_credit_card", False))
        primary_cat     = str(cx.get("primary_spending_category", "") or "")

        cx_lines = []
        if income > 0:
            cx_lines.append(f"Income: ${income:,.0f}/yr")
        if credit_score > 0:
            cx_lines.append(f"Credit score: {credit_score}")
        if life_stage:
            cx_lines.append(f"Life stage: {life_stage}")
        if financial_goal:
            cx_lines.append(f"Goal: {financial_goal}")
        if debt_total > 0:
            cx_lines.append(f"Outstanding debt: ${debt_total:,.0f}")
        if has_competitor:
            cx_lines.append("Has competitor credit card")
        if primary_cat:
            cx_lines.append(f"Top spend: {primary_cat}")

        cx_block = ("\n".join(cx_lines) + "\n") if cx_lines else ""

        prompt = (
            f"Write 3 short bullets (max 15 words each) explaining why this Meridian Bank "
            f"product is the best offer for this customer.\n\n"
            f"Segment: {persona_name}\n"
            f"Churn risk: {churn_category or 'Normal'}\n"
            f"Product: {product_name}\n"
            f"Match score: {score * 100:.0f}%\n"
            + cx_block +
            f"\nRules: plain English, no jargon, reference at least one customer signal "
            f"(goal, credit, income, life stage, or debt).\n"
            f"Format:\n- [bullet]\n- [bullet]\n- [bullet]"
        )
        system = "You are a Meridian Bank offer strategist writing customer-facing offer reasons."
        raw = self.generate_text(
            prompt=prompt, system=system, max_tokens=100, temperature=0.65,
            agent_name="agent_c", call_type="why_this_offer",
        )
        bullets = []
        for line in (raw or "").split("\n"):
            line = line.strip().lstrip("-*•").strip()
            if line and len(line) > 5:
                bullets.append(line)
        return bullets[:3]

    def generate_supervisor_copy(
        self,
        focus_source: str,
        product_name: str,
        persona_label: str,
        churn_category: str = "",
    ) -> dict:
        """Supervisor headline + detail for Agent D. Returns {"headline": ..., "detail": ...} or {}."""
        churn_note = f" (churn risk: {churn_category})" if churn_category and churn_category != "Low" else ""
        prompt = (
            f"Write a JPMorgan Chase supervisor briefing for a relationship manager.\n\n"
            f"Customer segment: {persona_label}{churn_note}\n"
            f"Focus signal: {focus_source}\n"
            f"Primary product: {product_name}\n\n"
            f"HEADLINE: One action-verb sentence, max 10 words.\n"
            f"DETAIL: Two sentences explaining the opportunity.\n\n"
            f"Rules: No jargon. No mention of Agent D, orchestrator, or algorithm."
        )
        system = "You are a JPMorgan Chase relationship manager supervisor writing advisor briefings."
        raw = self.generate_text(
            prompt=prompt, system=system, max_tokens=120, temperature=0.6,
            agent_name="agent_d", call_type="supervisor_copy",
        )
        result = {}
        for line in (raw or "").split("\n"):
            ls = line.strip()
            if ls.upper().startswith("HEADLINE:"):
                result["headline"] = ls.split(":", 1)[-1].strip()
            elif ls.upper().startswith("DETAIL:"):
                result["detail"] = ls.split(":", 1)[-1].strip()

        # Fallback: first non-empty line = headline, rest = detail
        if not result.get("headline"):
            lines = [l.strip() for l in (raw or "").split("\n") if l.strip()]
            if lines:
                result["headline"] = lines[0]
            if len(lines) > 1:
                result["detail"] = " ".join(lines[1:])
        return result

    def generate_cluster_quality_review(self, segment_summaries: list, silhouette_score: float) -> list:
        """Ask LLM to assess cluster quality. Returns list of warning strings."""
        summaries_text = "\n".join(
            f"- {s.get('name', 'Segment')}: {s.get('size', 0)} customers, "
            f"avg deposits ${s.get('avg_deposits', 0):,.0f}"
            for s in (segment_summaries or [])
        )
        prompt = (
            f"Review JPMorgan Chase customer segments. Silhouette score: {silhouette_score:.3f}\n"
            f"{summaries_text}\n\n"
            f"Flag any segment with: fewer than 5% of customers, nearly identical profile to another, "
            f"or unclear differentiation.\n"
            f"If all look good, write 'OK'.\n"
            f"Otherwise write one warning per line starting with the segment name."
        )
        system = "You are a banking analytics expert reviewing customer segmentation results."
        raw = self.generate_text(
            prompt=prompt, system=system, max_tokens=100, temperature=0.4,
            agent_name="agent_a", call_type="cluster_quality",
        )
        if not raw or raw.strip().upper() == "OK":
            return []
        return [w.strip() for w in raw.split("\n") if w.strip()]

    # ── private backends ──────────────────────────────────────────────────────

    def _call_anthropic(self, prompt: str, system: str, max_tokens: int, temperature: float, model: str):
        """Call Anthropic Claude API. Returns (text, usage_dict) — never raises silently."""
        import anthropic
        model_used = model or "claude-haiku-4-5-20251001"
        kwargs = dict(
            model=model_used,
            max_tokens=max(max_tokens, 10),
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system
        response = self._anthropic_client.messages.create(**kwargs)
        raw = response.content[0].text if response.content else ""
        usage = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
        completion_tokens = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
        return raw.strip(), {
            "model": model_used,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def _call_together(self, prompt: str, system: str, max_tokens: int, temperature: float):
        """Call Together AI chat completions with model fallback chain. Returns (text, usage_dict)."""
        import requests, urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        headers = {
            "Authorization": f"Bearer {self._together_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt or "Respond with OK."})

        payload = {
            "messages": messages,
            "max_tokens": max(max_tokens, 10),
            "temperature": temperature,
        }

        last_err = None
        for model in _TOGETHER_MODELS:
            try:
                payload["model"] = model
                resp = requests.post(
                    f"{_TOGETHER_BASE}/chat/completions",
                    json=payload, headers=headers,
                    verify=False, timeout=30,
                )
                if resp.status_code in (400, 404, 422):
                    last_err = f"HTTP {resp.status_code} for {model}"
                    continue
                resp.raise_for_status()
                data = resp.json()
                raw = data["choices"][0]["message"]["content"]
                usage = data.get("usage") or {}
                return (raw or "").strip(), {
                    "model": model,
                    "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
                    "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
                    "total_tokens": int(usage.get("total_tokens", 0) or 0),
                }
            except Exception as e:
                last_err = e
                continue

        raise RuntimeError(f"All Together AI models failed. Last error: {last_err}")
