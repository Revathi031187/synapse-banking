# CMO Demo Feedback – Plan & Implementation Steps

Based on demo feedback (Jennifer / Office of the CMO, banking). **Plan and implementation steps only** – implement later when approved.

---

## 1. Strategic priorities (from feedback)

| Priority | Theme | CMO ask |
|----------|--------|---------|
| **P0** | Agent C + explainability + cross-channel | One best offer per customer; how/why AI got there; why our approach is better; actionable cross-channel |
| **P1** | Modularity & selective deployment | Deploy only the agents customers care about (e.g. C only) |
| **P1** | Churn-risk cohort | Use existing data; build churn-risk target in demo flow |
| **P1** | End-user controls | Exclude products by persona, geo, or customer profile |
| **P2** | 2nd/3rd party data | What to ingest; how it improves the model; concrete suggestions |
| **P2** | Agentic workflows | Workflows with parameters/constraints, not one-off campaigns |
| **P2** | Channel execution workflow | Consume offers across website, branch, email; handoffs to execution systems |
| **P2** | Agent 3 ready | For next meeting and formal play partner / commitments |
| **P3** | B2B, large banks | Nice-to-have; some modules for larger banks if story is strong |
| **Platform** | Databricks + Genie | Build on Databricks; maximize Genie usage for adoption |

---

## 2. Plan overview

### Phase 1 – Agent C & “one best offer” story (CMO-critical)
- Make Agent C the hero: **one best offer per customer** with clear reasoning.
- Add **explainability**: why this offer, why this score, why our approach beats rules/heuristics.
- Design **cross-channel actionability**: one offer, many channels (web, branch, email) with handoff shape.

### Phase 2 – Demo & targeting
- Add **churn-risk cohort** to the demo (data exists; expose in UI and in Agent C logic).
- Keep **modular deployment**: document and support “Agent C only” or “A + C” etc.
- Align story to **mid-sized banks**; optional slide for large banks / B2B.

### Phase 3 – Controls & workflows
- **End-user controls**: exclude products by persona, geo, profile (config + UI).
- **Agentic workflows**: define workflows with parameters and constraints (not only one-by-one campaigns).
- **Channel workflow**: how campaigns are consumed per channel and handed off to execution systems.

### Phase 4 – Data & platform
- **2nd/3rd party data**: list recommended sources; where they plug in (features, propensity, churn); how they improve outcomes.
- **Databricks + Genie**: move more logic into Databricks; use Genie for discovery, lineage, and consumption.

---

## 3. Implementation steps (how to do it)

### 3.1 Agent C – one best offer & explainability (P0)

1. **Define “one best offer” output**
   - For each customer: single recommended offer (product/action) plus score and short reason.
   - Decide where it lives: e.g. Agent C API response + table/views in Lakehouse.

2. **Add explainability layer**
   - Per recommendation: “Why this offer?” (e.g. segment, propensity, churn risk, constraints).
   - “Why our AI?”: compare to rule-based or segment-only (e.g. lift, accuracy, fairness) – can be slide + optional dashboard later.
   - Expose in API and in a simple “reasoning” panel in the demo UI.

3. **Implement or refactor Agent C**
   - Input: customer id (and available context).
   - Output: one best offer + score + reason(s) + optional runner-up.
   - Use existing propensity/churn/segment signals; add overrides (Phase 3) later.

4. **Cross-channel actionability (design)**
   - Define “campaign payload”: offer id, customer id, channel, copy/snippet, link or CTA.
   - Document how this payload is consumed by website, branch, email (and later by execution systems).
   - In demo: show one offer and “this same offer can be shown on web, in branch, in email” with example payload.

### 3.2 Churn-risk cohort in demo (P1)

1. **Identify churn model / data**
   - Where churn risk or churn flag lives (e.g. table, column, model output).
   - If not built: define a simple churn-risk score (e.g. from engagement, balance, tenure) and publish to a table.

2. **Expose in demo**
   - Add “High churn risk” (or similar) as a filter or segment in the demo UI.
   - Show a pre-built “Churn risk” cohort (e.g. list of customers or count) and allow drilling into offers for that cohort.
   - Optionally: Agent C uses churn risk as an input to the one best offer (e.g. prioritize retention offers for high-risk).

3. **Document for CMO**
   - One slide: “We have the data; here’s the churn-risk cohort and how we use it in targeting.”

### 3.3 Modular / selective deployment (P1)

1. **Configuration**
   - Add a config (e.g. in app or repo): which agents are enabled (e.g. `agents_enabled: [C]` or `[A, C]`).
   - App only loads and exposes APIs for enabled agents.

2. **Documentation**
   - One-pager: “Deploy Agent A only”, “Deploy Agent C only”, “Deploy A + C”.
   - Dependencies (e.g. C may need segment data from A if used).

3. **Demo**
   - Show “Agent C only” or “A + C” as a deployment option in the story.

### 3.4 End-user controls – exclusions (P1)

1. **Data model**
   - Tables or config for exclusions: (product_id, exclude_for: persona | geo | profile_attribute).
   - Define “profile_attribute” (e.g. segment, risk tier, custom flag).

2. **API & engine**
   - Agent C (and any agent that recommends products) checks exclusions before returning the one best offer.
   - Input to exclusion check: customer’s persona, geo, profile; list of candidate offers; output: filtered list.

3. **UI (later)**
   - Settings page: “Exclude product X from persona Y / region Z / profile W.”
   - Persist to same config/table; API reads it at runtime.

4. **Demo**
   - Show one example: “Product P excluded for Traditional Members” and that the offer for that segment never suggests P.

### 3.5 2nd/3rd party data – strategy & use (P2)

1. **List recommended sources**
   - e.g. Credit bureau (affordability, risk), demographics (age, income band), geo (branch proximity, region), engagement (email opens, app logins), 3rd party (life events, spending signals).
   - One slide or doc: “Recommended 2nd/3rd party data and why.”

2. **Map to model**
   - For each source: which feature(s), which agent or model (propensity, churn, next-best-offer).
   - How it improves outcome (e.g. “Bureau data improves affordability filter and reduces bad offers”).

3. **Integration pattern**
   - Ingest into Lakehouse (batch or streaming); build feature tables; Agent C (and others) read from these.
   - Document “where to plug in” so banks can add their own 2nd/3rd party data the same way.

### 3.6 Agentic workflows (P2)

1. **Define workflow model**
   - Workflow = named flow with: trigger (e.g. “weekly”, “on segment refresh”), steps (e.g. run Agent A → run Agent C → publish offers), parameters (e.g. segment_ids, channel), constraints (e.g. max offers per customer, exclusion rules).

2. **Implement workflow runner**
   - Config-driven: read workflow definition (YAML/JSON or table); execute steps in order; pass parameters; enforce constraints.
   - Run on Databricks (job or Genie-triggered) where possible.

3. **UI (later)**
   - “Create workflow”: pick trigger, steps, parameters; save and run. Contrast with “one-by-one campaign” in the story.

### 3.7 Channel execution workflow (P2)

1. **Campaign output contract**
   - Standard payload per (customer, offer, channel): customer_id, offer_id, channel, creative_id, link/CTA, expiry.
   - API or table that execution systems (web, branch, email) can consume.

2. **Handoff points**
   - Document: “Campaign table / API → Website (how),” “→ Branch (how),” “→ Email (how),” “→ CRM/Marketing cloud (how).”
   - Optional: small adapter per channel (e.g. “export for Email platform X”) or generic export (e.g. CSV/API for any system).

3. **Demo**
   - Show “one offer, multiple channels” and a sample export/API that a channel system would consume.

### 3.8 Agent 3 (P2)

1. **Scope Agent 3**
   - Decide role (e.g. channel optimization, creative, or another CMO priority from feedback).
   - Align with “one best offer” and explainability if it recommends anything.

2. **Build & integrate**
   - Same pattern as A/C: config, API, optional UI; respect modular deployment and exclusions.

3. **Prepare for next meeting**
   - Demo A + C + 3; stress Agent C and one best offer; mention churn cohort, controls, and workflows as “next” or “in progress.”

### 3.9 Databricks & Genie (platform)

1. **Databricks**
   - Run Agent C (and A, 3) from Databricks where possible (notebooks/jobs or Apps).
   - Store inputs/outputs, segment and churn tables, campaign table in Lakehouse.
   - Use Delta for versioning and governance.

2. **Genie**
   - Publish key assets (segment definitions, churn cohort, one-best-offer table, campaign export) so business users can discover and consume via Genie.
   - Use Genie for lineage (e.g. “this offer comes from this agent and this data”).

3. **Story**
   - “Built on Databricks; insights and campaigns consumable via Genie” – align with FY27 GTM (Genie, Lakebase).

---

## 4. Suggested order of execution

| Order | Step | Outcome |
|-------|------|--------|
| 1 | 3.1 Agent C – one best offer + explainability | CMO-ready story for “one offer + why” |
| 2 | 3.2 Churn-risk cohort in demo | Churn targeting visible in demo |
| 3 | 3.3 Modular deployment config + doc | Can sell “Agent C only” |
| 4 | 3.4 Exclusions – data model + API | Controls ready for story/demo |
| 5 | 3.7 Channel payload + handoff doc | Cross-channel actionability clear |
| 6 | 3.8 Agent 3 scope + build | Ready for next meeting |
| 7 | 3.5 2nd/3rd party data doc | Slide/document for CMO |
| 8 | 3.6 Agentic workflows | Differentiator vs one-by-one campaigns |
| 9 | 3.9 Databricks + Genie | Platform alignment and adoption |

---

## 5. Success criteria (for plan validation)

- **CMO story:** One best offer per customer, with “how/why” and “why our AI,” and clear path to cross-channel execution.
- **Demo:** Churn cohort visible; optional exclusions; modular (e.g. C only); Agent 3 in place for next meeting.
- **Platform:** More logic and data in Databricks; key outputs consumable via Genie.
- **Roadmap:** Controls, agentic workflows, and channel handoffs documented and either in progress or planned.

Use this plan to prioritize backlog and align implementation with the CMO feedback and FY27 Databricks GTM.
