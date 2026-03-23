# Banking Agent D — dataset tables

Agent D **next-best** (`POST /api/banking/agent_d/next-best`) uses three CSV tables under `data/preloaded/fmb_bank/`, plus live **Agent B** and **Agent C** outputs.

## wishlist.csv

Products the customer saved (goals / watchlist).

| Column       | Type   | Description        |
|-------------|--------|--------------------|
| customer_id | string | Customer ID        |
| product_id  | string | Banking product ID |
| added_at    | string | ISO datetime       |

## incomplete_applications.csv

Started-but-not-finished applications (banking analog of abandoned checkout).

| Column       | Type   | Description           |
|-------------|--------|-----------------------|
| customer_id | string | Customer ID           |
| product_id  | string | Product applied for   |
| abandoned_at| string | ISO datetime          |
| session_id  | string | Optional session ID   |

## recommendation_impressions.csv

Tracks what was recommended and whether the customer engaged.

| Column         | Type   | Description                          |
|----------------|--------|--------------------------------------|
| customer_id    | string | Customer ID                          |
| product_id     | string | Product ID                           |
| recommended_at | string | When shown in a next-best run        |
| clicked_at     | string | When customer engaged (empty if not) |

**Rule:** A product is **excluded** from the next run if there is any row for `(customer_id, product_id)` with **empty** `clicked_at`.  
**Click:** `POST /api/banking/agent_d/click` sets `clicked_at` so the product can appear again.

## Synthetic data

```bash
python scripts/generate_banking_agent_d_tables.py
```

Overwrites `wishlist.csv` and `incomplete_applications.csv`. Impressions are populated at runtime.

## Ranking (next-best)

1. Agent C primary offer  
2. Incomplete applications  
3. Wishlist  
4. Agent B ranked products (persona fit)  
5. Catalog fallback (category-capped)

Run **Agent A** (and ideally **B/C**) first so scores and offers are meaningful.
