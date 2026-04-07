# Genie space instructions (Databricks UI)

Copy these into your **Genie space → Instructions** (and add matching **SQL samples** / **Sample questions**). Replace `dev.banking` with your Unity Catalog location. The API resolves catalog/schema in one place: **`DOMAIN_CATALOG` / `DOMAIN_SCHEMA`** first, then **`ACADEMY_CATALOG` / `ACADEMY_SCHEMA`** if unset (backward compatibility).

## Domain description

This space answers questions about **banking personalization**: customers, products, transactions, and **model-driven personas** synced from the segmentation app.

All curated tables live under **`dev.banking`** (example). The SQL warehouse attached to this space must have **SELECT** on this catalog/schema.

## Tables (fully qualified)

| Table | Purpose |
|--------|---------|
| `dev.banking.customers` | Customer attributes; join key `customer_id` |
| `dev.banking.products` | Product catalog |
| `dev.banking.transactions` | Transaction history |
| `dev.banking.persona_assignments` | **Current** segment: `customer_id`, `cluster_id`, `persona_name` (synced after each segmentation run) |
| `dev.banking.persona_definitions` | Segment rollups: `cluster_id`, `persona_name`, `size`, `total_revenue`, `avg_spend`, `percentage` |

Adjust names if your ETL uses different table names; keep **persona_assignments** and **persona_definitions** as the canonical persona outputs from the app.

## Rules

1. For **persona, segment, or cluster** questions, join `customers` to **`dev.banking.persona_assignments`** on **`customer_id`**. Use **`persona_assignments.persona_name`** and **`cluster_id`** as the source of truth.
2. **Do not** use legacy persona columns on `customers` if present (e.g. old `persona_name`, `segment`, or deprecated IDs). Prefer **`persona_assignments`** only.
3. For **segment-level KPIs** (size, revenue, share), use **`dev.banking.persona_definitions`** or aggregate from **`persona_assignments`** joined to facts.
4. Prefer **qualified** names: `dev.banking.<table>`.

## Example SQL — revenue by persona (assignments + transactions)

```sql
SELECT
  pa.persona_name,
  SUM(t.amount) AS total_txn_amount
FROM dev.banking.persona_assignments pa
JOIN dev.banking.transactions t ON t.customer_id = pa.customer_id
GROUP BY pa.persona_name
ORDER BY total_txn_amount DESC;
```

## Example SQL — segment sizes from definitions

```sql
SELECT persona_name, size, percentage, total_revenue, avg_spend
FROM dev.banking.persona_definitions
ORDER BY size DESC;
```

## Example SQL — customers in one persona

```sql
SELECT c.customer_id, c.customer_name, pa.cluster_id
FROM dev.banking.persona_assignments pa
JOIN dev.banking.customers c ON c.customer_id = pa.customer_id
WHERE pa.persona_name = 'Tech Adopters';
```

## Sample natural-language questions

- “What are the largest personas by customer count?”
- “Show total transaction volume by persona name using persona_assignments.”
- “How many customers are in the segment named ‘Household Savers’?”
- “Compare average balance by persona using definitions.”

## Operational order (analysts)

1. Load **customers**, **products**, **transactions** into Unity Catalog (`dev.banking` or your schema).  
   **From this app’s API:** set `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_SQL_WAREHOUSE_ID`, and optional `DOMAIN_CATALOG` / `DOMAIN_SCHEMA` / `DATABRICKS_UC_VOLUME_NAME`, then call **`POST /api/banking/uc/preloaded/upload`** or use **Banking → Data Loader → “Upload preloaded data to UC”**. That copies `data/preloaded/fmb_bank` into a UC volume and runs `CREATE OR REPLACE TABLE … AS SELECT * FROM read_files(…)` on the SQL warehouse.  
   **Alternative:** Databricks notebook `scripts/databricks/load_fmb_bank_to_uc.py` if Spark runs inside the workspace.
2. Run **segmentation** in the app (Agent A).
3. Call **`POST /api/banking/genie/sync-personas`** (or use the UI button) to refresh **`persona_assignments`** and **`persona_definitions`**.
4. Confirm tables in **Catalog Explorer**.
5. Ask questions in the app **Ask Genie** page or in the Genie UI; **re-sync** after each new segmentation run.

## App environment (Databricks App / API)

Set:

- `DATABRICKS_HOST` — workspace URL (with or without `https://`; normalized at runtime)  
- **`GENIE_SPACE_ID`** — real space id from Genie **Settings** or `GET /api/2.0/genie/spaces` (hex string, e.g. 32 characters). Not a placeholder like `paste_your_genie_space_id_here`.  
- **Authentication (Genie on Azure):** Microsoft documents **OAuth** for the Genie Conversation API. A **personal access token alone often returns** `Credential was not sent or was of an unsupported type`. Prefer one of:
  - **Databricks OAuth M2M:** `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET` (service principal in the workspace), or  
  - **Azure Entra service principal:** `ARM_CLIENT_ID` + `ARM_CLIENT_SECRET` + `ARM_TENANT_ID` (same variable names the Databricks SDK uses for Azure auth).  
  You can keep `DATABRICKS_TOKEN` in `.env` for other APIs (e.g. warehouse/SQL). If **both** PAT and `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` are set, the Databricks SDK errors unless one method is chosen: this app sets `auth_type` automatically. **Default for Genie:** OAuth M2M when those client vars exist. To **force PAT** for Genie only, set **`DATABRICKS_GENIE_AUTH=pat`**. For explicit OAuth: **`DATABRICKS_GENIE_AUTH=oauth-m2m`**. Azure Entra SP: **`DATABRICKS_GENIE_AUTH=azure-client-secret`** (requires `ARM_*` vars).  
- `DATABRICKS_TOKEN` — optional if using OAuth above; PAT for SQL / Files where accepted  
- `DOMAIN_CATALOG` / `DOMAIN_SCHEMA` (fallback: `ACADEMY_CATALOG` / `ACADEMY_SCHEMA`) — must match registered tables; one resolver is used for sync, Genie context, and `/genie/status`  
- Optional: `DOMAIN_CUSTOMERS_TABLE` — fully qualified customers table if not `{catalog}.{schema}.customers`  
- **`DATABRICKS_SQL_WAREHOUSE_ID`** — required for **`POST /api/banking/uc/preloaded/upload`** (preloaded CSV → UC)  
- Optional: **`DATABRICKS_UC_VOLUME_NAME`** — managed volume under `catalog.schema` for staging CSVs (default `fmb_preloaded`); PAT needs **Files API** (preview) permission where applicable  

Install SDK: `pip install -r requirements-databricks.txt` (Genie). UC upload from the API uses **httpx** only (already in `requirements.txt`).
