# CLAUDE.md — Personalization Agent Banking

## Project Overview

Enterprise-grade AI-powered personalization platform serving two domains:
- **F&M Bank** — Financial product recommendations (credit cards, loans, savings accounts)
- **Academy Sports** — Retail product recommendations (sporting goods, outdoor gear)

A 4-agent pipeline processes customers from raw segmentation through behavioral feedback.

---

## Architecture

### Multi-Agent Pipeline

```
Customers + Products + Transactions
        ↓
Agent A → Agent B → Agent C → Agent D
(Segment) (Recommend) (Best Offer) (Behavior)
```

| Agent | File | Purpose |
|-------|------|---------|
| A | `agents/agent_a_banking_enhanced.py` | K-Prototypes clustering → 5 personas |
| B | `agents/agent_b_banking_chromadb.py` | 12-factor scoring → ranked product list |
| C | `agents/agent_c_banking.py` | Selects single best offer per customer |
| D | `agents/agent_d_banking.py` | Impression ledger, click tracking, next-visit directives |

Academy Sports mirrors this pattern with `agent_a_academy_enhanced.py`, `agent_b_academy_chromadb.py`.

### Stack

**Backend**
- FastAPI 0.104.1 + Uvicorn (port 8002)
- Python 3.10+
- ChromaDB 0.4.22 (vector store, persistent at `./chroma_db/`)
- Sentence-Transformers `all-MiniLM-L6-v2` (384-dim embeddings)
- Scikit-learn + KModes (K-Prototypes clustering)
- Together AI API (LLM for explanations/naming)
- Pandas + NumPy (data-first ML)

**Frontend**
- React 18.2.0 + TypeScript 5.3.3
- Vite 5.0.11 (dev port 5173, proxies `/api` → port 8002)
- Tailwind CSS + Recharts + Framer Motion
- Zustand (global state) + TanStack Query (server state)
- Axios (API client in `frontend/src/services/api.ts`)

---

## Directory Structure

```
api/
  main_unified_chromadb.py   # FastAPI app — all endpoints
  schemas.py                 # Pydantic models
agents/
  agent_a_banking_enhanced.py
  agent_a_academy_enhanced.py
  agent_b_banking_chromadb.py        # Main banking rec engine
  agent_b_banking_logit_enhanced.py  # Hybrid ML variant
  agent_b_academy_chromadb.py
  agent_c_banking.py
  agent_d_banking.py
  banking_12_factor_scorer.py
  enhanced_12_factor_scorer.py
utils/
  chromadb_client.py         # ChromaDB wrapper
  together_ai.py             # LLM integration
  logger.py
  feature_scorer.py
data/preloaded/
  fmb_bank/                  # 5K customers, ~20 products, 50K transactions
  academy_sports/            # 5K customers, 1K+ products, 50K+ purchases
frontend/src/
  pages/banking/             # BankingAgentA–D, BankingDataLoader, BankingDashboard
  pages/academy/             # AcademyAgentA–B, AcademyMacroDashboard
  components/                # CustomerInsightModal, visualizations/
  services/api.ts
tests/
  test_agent_b_banking.py
  test_agent_c_banking.py
  test_agent_d_banking.py
  test_micro_segmentation.py
deploy/                      # Systemd + Nginx configs
chroma_db/                   # ChromaDB persistent storage
```

---

## Key Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run API server (development)
uvicorn api.main_unified_chromadb:app --port 8002 --reload

# Run tests
python -m pytest tests/ -v
python -m pytest tests/test_agent_b_banking.py -v
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # Dev server at http://localhost:5173
npm run build        # Production build to frontend/dist/
```

### Databricks Apps
```bash
npm run build:single-port   # Build frontend for single-port deployment
python run_app.py           # FastAPI serves API + static frontend on one port
```

---

## API Endpoint Pattern

All endpoints follow `POST /api/{industry}/agent_{letter}/{action}`:

```
POST /api/banking/agent_a/execute          → personas + segmented customers
POST /api/banking/agent_b/execute          → ranked product recommendations
POST /api/banking/agent_c/get_one_best_offer → single offer + reasoning
POST /api/banking/agent_d/orchestrate      → final stack + next-visit directives

POST /api/academy/agent_a/execute
POST /api/academy/agent_b/execute
```

---

## Banking 12-Factor Scoring

Agent B scores each product per customer across 12 factors (weights sum to ~115%):

1. Credit eligibility (credit score vs product minimum)
2. Income alignment
3. Deposit balance matching
4. Product ownership (upsell/cross-sell signals)
5. Digital engagement
6. Life event signals
7. Loyalty indicators
8. Channel preference
9. Frequency optimizations
10. CLV tier matching
11. Regulatory/compliance flags
12. Time-to-decision signals

Scoring logic lives in `agents/banking_12_factor_scorer.py`.

---

## ChromaDB

- Client wrapper: `utils/chromadb_client.py`
- Persistent storage: `./chroma_db/`
- Collections: `banking_customers`, `banking_personas`, `banking_products`, `academy_products`
- Initialize/rebuild: `python initialize_chromadb.py`
- Fallback: hash-based embeddings if `onnxruntime` unavailable

---

## Environment Variables

Required in `.env` at project root:

```
TOGETHER_API_KEY=...            # LLM for explanations and segment naming
DATABRICKS_HOST=...             # Azure Databricks workspace URL
DATABRICKS_TOKEN=...            # PAT token
DATABRICKS_SQL_WAREHOUSE_ID=... # SQL warehouse for Genie
GENIE_SPACE_ID=...              # Databricks Genie space
DOMAIN_CATALOG=dev
DOMAIN_SCHEMA=banking
```

---

## Agent D Behavioral Loop

Agent D maintains a CSV-backed impression ledger:
- Tracks `shown_count` and `click_count` per customer-product pair
- Deprioritizes products shown 3+ times with zero clicks
- Recovers incomplete applications from `wishlist.csv` + `incomplete_applications.csv`
- Outputs `directives_for_next` that modify the next Agent B run
- Enforces max 3 products per category, max 12 in live stack

---

## Frontend State

- **Zustand store**: selected customer, agent results, loading state
- **TanStack Query**: server cache for agent responses (60s stale time)
- **Routing**: React Router v6, one route per agent page per domain
- **API base URL**: `VITE_API_URL` env var or defaults to `http://localhost:8000`; Vite proxies `/api` to port 8002 in dev

---

## Deployment

**Linux (production)**
- Nginx reverse proxy at `/nba-platform-v2/`
- Uvicorn runs as systemd service (`deploy/banking-backend.service`)
- Frontend served as static files from `frontend/dist/`

**Databricks Apps**
- Single-port: `run_app.py` serves everything on one port
- Config: `app.yaml`

---

## Testing Notes

- Framework: PyTest (no pytest.ini; run from project root)
- Tests use minimal synthetic DataFrames — no real data required
- Phase-based: each test file validates one agent end-to-end
- No database mocking; agents are tested with in-memory DataFrames
