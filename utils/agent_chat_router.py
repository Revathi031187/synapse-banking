"""
Multi-source routing layer for the Segment AI chatbot.

Decides whether a question needs the existing text-to-SQL pipeline
(utils/chat_sql_engine.py), one or more of Agents A/B/C/D, or more
information from the user — possibly more than one of these at once
(e.g. "how's the Premium segment doing, and what should we offer its top
customer?" needs sql, then agent_b). Fetches condensed data from each
resolved source and produces one structured Claude-written answer.

Cheap-by-construction: an ordinary analytics question that resolves to a
single "sql" need with nothing missing is routed straight back through
ask_chatbot() unmodified — zero added LLM cost over today's behavior. Only
questions that actually touch an agent (or need more than one source) pay
for the small planner call and the narration/synthesis call.
"""
from __future__ import annotations

import copy
import json
import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Used only for routing, never for the detailed answer itself — kept on
# Together AI so planner traffic never competes with the Claude answer budget.
# The smaller models in config/llm_priority.json's Together list
# (Meta-Llama-3-8B-Instruct-Lite, Qwen2.5-7B-Instruct-Turbo) returned
# "non-serverless model" 400s when probed live against this account's
# TOGETHER_API_KEY — only the larger *-Turbo flagship models are enabled as
# serverless here. If a genuinely smaller model is enabled later, swap it in;
# until then this doesn't change the token COUNT budget (the planner prompt
# is still capped small below), only which model answers it.
_PLANNER_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
_VALID_SOURCES = {"sql", "agent_a", "agent_b", "agent_c", "agent_d"}
_MAX_NEEDS = 3

_MISSING_CUSTOMER_QUESTION = {
    "agent_b": "Which customer (ID or name) or persona would you like product recommendations for?",
    "agent_c": "Which customer (ID or name) would you like the single best offer for?",
    "agent_d": "Which customer (ID or name) would you like next-visit recommendations for?",
}
_NO_SEGMENTATION_MESSAGE = (
    "I don't have a customer segmentation to work from yet — please run Agent A "
    "on the Data Loader tab first, then ask me again."
)

_PLANNER_SYSTEM = """You are the routing brain for Segment AI, a banking analytics chatbot. Given a user's \
question (and a little recent conversation), decide which data source(s) can answer it.

Sources:
- "sql": general data/analytics questions over customers, products, transactions, deposits, ad spend, \
segments — counts, averages, breakdowns, trends, comparisons of METRICS (income, churn, deposits, etc).
- "agent_a": which customer personas/segments exist and their stats.
- "agent_b": product recommendations for ONE customer or persona.
- "agent_c": the single best offer for ONE customer.
- "agent_d": what to show a customer on their NEXT VISIT / behavioral next-best-action.

CRITICAL: recommendations, best offers, and next-visit guidance ONLY ever come from agent_b/agent_c/agent_d \
— NEVER from "sql", even when the question compares several customers/personas or uses the word "compare". \
SQL has no idea what Agent B/C/D would actually recommend; guessing it from raw tables gives WRONG numbers \
that won't match what those agents really produce. If a question asks "compare the recommendation/offer for \
X and Y", emit ONE need per entity (X and Y each get their own agent_b/agent_c need, same source, each with \
its own customer_id/customer_name/persona) — never collapse it into a single "sql" need.

Example: "Compare the offers for Wealth Saver vs At-Risk Saver" ->
{"needs": [
  {"source": "agent_c", "purpose": "best offer for Wealth Saver", "customer_id": null, "customer_name": null, "persona": "Wealth Saver"},
  {"source": "agent_c", "purpose": "best offer for At-Risk Saver", "customer_id": null, "customer_name": null, "persona": "At-Risk Saver"}
]}

A question can need more than one source too — e.g. "how's the Premium segment doing and what would you \
recommend for its top customer" needs "sql" then "agent_b". Extract any customer_id, customer_name, or \
persona name the question or recent conversation already gives you for each need — use null if none given, \
never guess one, and never shorten/paraphrase a persona name (copy it exactly as given, e.g. "Wealth Saver" \
not "Saver" or "Wealth").

IMPORTANT: if the question asks for recommendations, an offer, or next-visit guidance but does NOT name a \
customer or segment, still answer with the matching source ("agent_b"/"agent_c"/"agent_d") and leave \
customer_id/customer_name/persona null — do NOT fall back to "sql" just because no customer was given. \
Leaving those null is expected; the app will ask the user who they mean.

Respond with ONLY this JSON, nothing else, no markdown fences:
{"needs": [{"source": "sql|agent_a|agent_b|agent_c|agent_d", "purpose": "short phrase", \
"customer_id": null, "customer_name": null, "persona": null}]}

At most 3 needs. If the question is general analytics, small talk, or you are unsure, use a single "sql" need."""

_ANSWER_SYSTEM = """You are Segment AI, a banking analytics assistant. You have been given structured data \
already fetched from the bank's systems for this question — never invent numbers, names, or products that \
aren't in it.

Formatting rules — the answer must NOT be a single paragraph:
- Use "## " or "### " headers when the answer covers more than one part.
- Bold every number, dollar amount, product name, and customer/segment name using **text**.
- Use "- " bullet points for 3 or more items.
- Use "1. " "2. " numbered lists for ranked or sequential items (e.g. top recommendations).
- Keep paragraphs short.

If a "STILL NEED" section is provided, answer everything you CAN from the data first, then end your \
answer with a direct, specific question for whatever is still missing — never skip the parts you can \
answer just because something else is missing."""


def _parse_json_object(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
    try:
        return json.loads(text)
    except Exception:
        return {}


def _format_history(history: Optional[List[Dict[str, Any]]], limit: int, max_chars: int) -> str:
    if not history:
        return ""
    lines = []
    for h in history[-limit:]:
        role = "User" if h.get("role") == "user" else "Assistant"
        content = str(h.get("content") or "")[:max_chars]
        if content:
            lines.append(f"{role}: {content}")
    return ("\n".join(lines) + "\n\n") if lines else ""


def plan_needs(question: str, history: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Small, cheap Together-AI call that decides which source(s) a question needs.
    Never raises — falls back to a single "sql" need (today's behavior) on any
    failure or malformed output."""
    default = {"needs": [{"source": "sql", "purpose": question, "customer_id": None,
                           "customer_name": None, "persona": None}]}
    try:
        from utils.together_ai import together_ai
        hist_text = _format_history(history, limit=2, max_chars=200)
        prompt = f"{hist_text}Question: {question}"
        raw = together_ai.generate_text(
            prompt=prompt,
            system_message=_PLANNER_SYSTEM,
            model=_PLANNER_MODEL,
            max_tokens=250,
            temperature=0.0,
            agent_name="chatbot_router",
            call_type="intent_planning",
        )
        parsed = _parse_json_object(raw)
        needs = parsed.get("needs")
        if not isinstance(needs, list) or not needs:
            return default
        cleaned = []
        for n in needs[:_MAX_NEEDS]:
            if not isinstance(n, dict) or n.get("source") not in _VALID_SOURCES:
                continue
            cleaned.append({
                "source": n["source"],
                "purpose": str(n.get("purpose") or question)[:200],
                "customer_id": (str(n.get("customer_id")).strip() or None) if n.get("customer_id") else None,
                "customer_name": (str(n.get("customer_name")).strip() or None) if n.get("customer_name") else None,
                "persona": (str(n.get("persona")).strip() or None) if n.get("persona") else None,
            })
        return {"needs": cleaned} if cleaned else default
    except Exception:
        logger.warning("agent_chat_router: planner failed, defaulting to sql", exc_info=True)
        return default


def _lookup_customers_by_name(name: str) -> List[Dict[str, str]]:
    name = (name or "").strip()
    if not name:
        return []
    try:
        from utils.chat_sql_engine import _get_con
        con = _get_con()
        rows = con.execute(
            "SELECT DISTINCT customer_id, customer_name FROM customers WHERE customer_name ILIKE ? LIMIT 10",
            [f"%{name}%"],
        ).fetchall()
        return [{"customer_id": str(r[0]), "customer_name": str(r[1])} for r in rows]
    except Exception:
        logger.warning("agent_chat_router: customer name lookup failed", exc_info=True)
        return []


def _guess_persona_from_table(table: Optional[Dict[str, Any]]) -> Optional[str]:
    """Cross-need dependency support: if an earlier sql need's result has a
    segment/persona-like column, its top row is a reasonable guess for "the top
    segment" a later need (e.g. agent_b) refers to — no extra LLM call needed."""
    if not table or not table.get("columns") or not table.get("rows"):
        return None
    cols = [str(c).lower() for c in table["columns"]]
    for key in ("persona_name", "segment_name", "persona", "segment"):
        if key in cols:
            idx = cols.index(key)
            row = table["rows"][0]
            if idx < len(row) and row[idx]:
                return str(row[idx])
    return None


def _cap_table(table: Optional[Dict[str, Any]], n: int) -> Optional[Dict[str, Any]]:
    if not table or not table.get("rows"):
        return table
    rows = table["rows"]
    return {"columns": table.get("columns"), "rows": rows[:n], "truncated": len(rows) > n}


def _condense_agent_a(personas: Dict[str, Any], wanted: Optional[str]) -> Dict[str, Any]:
    def _row(cid, p):
        name = p.get("persona_name") or p.get("name") or f"Segment {cid}"
        chars = p.get("characteristics") or {}
        return {"persona_name": name, "size": p.get("size"),
                "avg_income": chars.get("avg_income"), "avg_deposits": chars.get("avg_deposits")}

    items = []
    for cid, p in (personas or {}).items():
        if not isinstance(p, dict):
            continue
        row = _row(cid, p)
        if wanted and wanted.strip().lower() not in str(row["persona_name"]).lower():
            continue
        items.append(row)
    if wanted and not items:  # requested name didn't match anything — show everything instead
        items = [_row(cid, p) for cid, p in (personas or {}).items() if isinstance(p, dict)]
    return {"personas": items[:8]}


def _condense_agent_b(result: Any) -> Dict[str, Any]:
    if not isinstance(result, dict) or result.get("error"):
        return {"error": (result or {}).get("error", "Agent B failed") if isinstance(result, dict) else "Agent B failed"}
    recs = result.get("recommendations") or []
    return {
        "persona": result.get("persona"),
        "recommendations": [
            {"product_name": r.get("product_name"), "score": r.get("score"), "reason": r.get("reason")}
            for r in recs[:5]
        ],
    }


def _condense_agent_c(result: Any) -> Dict[str, Any]:
    if not isinstance(result, dict) or result.get("error"):
        return {"error": (result or {}).get("error", "Agent C failed") if isinstance(result, dict) else "Agent C failed"}
    offer = result.get("offer") or {}
    expl = result.get("explainability") or {}
    return {
        "persona": result.get("persona"),
        "best_offer": offer.get("product_name"),
        "category": offer.get("category"),
        "score": result.get("score"),
        "reason": result.get("reason"),
        "why_this_offer": expl.get("why_this_offer"),
        "best_channel": result.get("best_channel"),
        "best_channel_reason": result.get("best_channel_reason"),
    }


def _condense_agent_d(result: Any) -> Dict[str, Any]:
    if not isinstance(result, dict) or result.get("error"):
        return {"error": (result or {}).get("error", "Agent D failed") if isinstance(result, dict) else "Agent D failed"}
    sv = result.get("supervisor_view") or {}
    directives = result.get("next_visit_directives") or {}
    return {
        "persona": result.get("persona_name"),
        "supervisor_narrative": result.get("supervisor_narrative"),
        "focus_product": sv.get("focus_product"),
        "primary_offer": sv.get("agent_c_primary_offer"),
        "priority_pin_product_id": directives.get("priority_pin_product_id"),
        "boost_product_ids": (directives.get("boost_product_ids") or [])[:5],
        "deprioritize_product_ids": (directives.get("deprioritize_product_ids") or [])[:5],
    }


class _RouterContext:
    def __init__(self, has_agent_a_results, personas, resolve_persona_customer_id,
                 run_agent_b, run_agent_c, run_agent_d):
        self.has_agent_a_results = has_agent_a_results
        self.personas = personas
        self.resolve_persona_customer_id = resolve_persona_customer_id
        self.run_agent_b = run_agent_b
        self.run_agent_c = run_agent_c
        self.run_agent_d = run_agent_d
        self.sql_top_persona_guess: Optional[str] = None
        self.name_ambiguity: Optional[List[Dict[str, str]]] = None


async def _resolve_customer_id(need: Dict[str, Any], ctx: _RouterContext) -> Optional[str]:
    if need.get("customer_id"):
        return str(need["customer_id"]).strip()
    if need.get("customer_name"):
        matches = _lookup_customers_by_name(need["customer_name"])
        if len(matches) == 1:
            return matches[0]["customer_id"]
        if len(matches) > 1:
            ctx.name_ambiguity = matches
        return None
    if need.get("persona") and ctx.resolve_persona_customer_id:
        cid = ctx.resolve_persona_customer_id(need["persona"])
        if cid:
            return cid
    if ctx.sql_top_persona_guess and ctx.resolve_persona_customer_id:
        cid = ctx.resolve_persona_customer_id(ctx.sql_top_persona_guess)
        if cid:
            return cid
    return None


async def _resolve_and_fetch(need: Dict[str, Any], ctx: _RouterContext) -> "tuple[Optional[Dict[str, Any]], Optional[str]]":
    """Returns (condensed_data, None) if the need was resolved and fetched, or
    (None, clarifying_question) if there wasn't enough information."""
    source = need["source"]

    if source == "agent_a":
        if not ctx.has_agent_a_results:
            return None, _NO_SEGMENTATION_MESSAGE
        return _condense_agent_a(ctx.personas, need.get("persona")), None

    cid = await _resolve_customer_id(need, ctx)
    if not cid:
        return None, _MISSING_CUSTOMER_QUESTION.get(source, "Which customer would you like that for?")
    if not ctx.has_agent_a_results:
        return None, _NO_SEGMENTATION_MESSAGE

    try:
        if source == "agent_b":
            raw = await ctx.run_agent_b(cid)
            condensed = _condense_agent_b(raw)
        elif source == "agent_c":
            raw = await ctx.run_agent_c(cid)
            condensed = _condense_agent_c(raw)
        elif source == "agent_d":
            raw = await ctx.run_agent_d(cid)
            condensed = _condense_agent_d(raw)
        else:
            return None, None
    except Exception as e:
        logger.warning("agent_chat_router: %s fetch failed for %s: %s", source, cid, e)
        return None, f"I ran into a problem getting that ({source}) — could you try again?"

    if condensed.get("error"):
        return None, f"I couldn't get that: {condensed['error']}"
    condensed["customer_id"] = cid
    return condensed, None


def _sum_usage(a: Dict[str, int], b: Dict[str, int]) -> Dict[str, int]:
    keys = ("prompt_tokens", "completion_tokens", "total_tokens", "calls")
    return {k: int(a.get(k, 0)) + int(b.get(k, 0)) for k in keys}


def answer(
    question: str,
    history: Optional[List[Dict[str, Any]]],
    resolved: List[Dict[str, Any]],
    unresolved: List[str],
) -> Dict[str, Any]:
    """One Claude call that turns whatever was resolved (one or more sources)
    into a single structured markdown answer, closing with a request for
    anything still missing."""
    hist_text = _format_history(history, limit=4, max_chars=400)
    sections = [
        f"[{r['source'].upper()} DATA]\n{json.dumps(r['data'], default=str)[:2500]}"
        for r in resolved
    ]
    data_block = "\n\n".join(sections)
    still_need = (
        "\n\nSTILL NEED (ask the user for this at the end of your answer):\n"
        + "\n".join(f"- {q}" for q in unresolved)
    ) if unresolved else ""
    prompt = f"{hist_text}Question: {question}\n\n{data_block}{still_need}"

    text = ""
    try:
        from utils.claude_client import get_claude_client
        text = get_claude_client().generate_text(
            prompt=prompt,
            system=_ANSWER_SYSTEM,
            max_tokens=1200,
            temperature=0.3,
            agent_name="chatbot",
            call_type="agent_narration",
        )
    except Exception:
        logger.warning("agent_chat_router: answer generation failed", exc_info=True)

    if not text:
        text = ("I found the relevant data but couldn't put together a written answer just now — "
                "please try asking again.")
    return {"success": True, "narrative": text, "sql": None, "table": None, "chart": None, "follow_ups": []}


async def route_and_answer(
    question: str,
    history: Optional[List[Dict[str, Any]]],
    *,
    has_agent_a_results: bool,
    personas: Dict[str, Any],
    resolve_persona_customer_id: Callable[[str], Optional[str]],
    run_agent_b: Callable[[str], Awaitable[Dict[str, Any]]],
    run_agent_c: Callable[[str], Awaitable[Dict[str, Any]]],
    run_agent_d: Callable[[str], Awaitable[Dict[str, Any]]],
) -> Dict[str, Any]:
    from utils.token_tracker import reset_scope, get_scope_usage
    from utils.chat_sql_engine import ask_chatbot

    reset_scope()
    plan = plan_needs(question, history)
    planner_usage = get_scope_usage()  # snapshot now — ask_chatbot() below resets this scope internally
    needs = plan.get("needs") or [{"source": "sql", "purpose": question}]

    ctx = _RouterContext(has_agent_a_results, personas, resolve_persona_customer_id,
                          run_agent_b, run_agent_c, run_agent_d)

    # A "sql" need is executed once, up front, via the existing full pipeline —
    # its table also feeds the cross-need persona-resolution heuristic below.
    sql_result: Optional[Dict[str, Any]] = None
    ran_sql = False
    for need in needs:
        if need.get("source") == "sql":
            sub_question = need.get("purpose") or question if len(needs) > 1 else question
            sql_result = ask_chatbot(sub_question, history=history or [])
            ctx.sql_top_persona_guess = _guess_persona_from_table(sql_result.get("table"))
            ran_sql = True
            break  # a second "sql" need would just repeat the same pipeline — one is enough

    resolved: List[Dict[str, Any]] = []
    unresolved: List[str] = []
    if ran_sql:
        resolved.append({"source": "sql", "data": {
            "sql": sql_result.get("sql"),
            "table": _cap_table(sql_result.get("table"), 15),
        }})

    for need in needs:
        if need.get("source") in ("sql",) or need.get("source") not in _VALID_SOURCES:
            continue
        data, clarifying = await _resolve_and_fetch(need, ctx)
        if data is not None:
            resolved.append({"source": need["source"], "data": data})
        elif clarifying:
            unresolved.append(clarifying)

    name_ambiguity_chips = (
        [f'{m["customer_name"]} ({m["customer_id"]})' for m in ctx.name_ambiguity[:6]]
        if ctx.name_ambiguity else []
    )

    final_usage = _sum_usage(planner_usage, get_scope_usage()) if ran_sql else get_scope_usage()

    only_sql = ran_sql and len(resolved) == 1 and not unresolved
    if only_sql:
        # Ordinary analytics question — return ask_chatbot()'s own result exactly
        # as today, at exactly today's cost. No agent/synthesis call spent.
        sql_result["token_usage"] = final_usage
        return sql_result

    if not resolved and unresolved:
        seen = list(dict.fromkeys(unresolved))
        narrative = "To answer that, I need a bit more:\n\n" + "\n".join(f"- {q}" for q in seen)
        return {
            "success": True, "narrative": narrative, "sql": None, "table": None, "chart": None,
            "follow_ups": name_ambiguity_chips, "token_usage": final_usage,
        }

    reply = answer(question, history, resolved, unresolved)
    if ran_sql and sql_result:
        reply["sql"] = sql_result.get("sql")
        reply["table"] = sql_result.get("table")
        reply["chart"] = sql_result.get("chart")
    reply["follow_ups"] = list(dict.fromkeys((reply.get("follow_ups") or []) + name_ambiguity_chips))[:6]
    # ask_chatbot() resets the token scope internally (if it ran), wiping the
    # planner's already-recorded usage — add it back in; otherwise the scope
    # opened by reset_scope() above already covers planner + narration together.
    reply["token_usage"] = _sum_usage(planner_usage, get_scope_usage()) if ran_sql else get_scope_usage()
    return reply
