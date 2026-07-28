"""
scripts/upload_meridian_to_databricks.py
=========================================
Upload ALL Meridian Bank preloaded CSVs to Databricks Unity Catalog
as Delta tables. Run this ONCE before using the Segment AI chatbot.

Tables created in {CATALOG}.{SCHEMA}:
  meridian_customers             (5,001 rows)
  meridian_products              (   29 rows)
  meridian_transactions          (876,553 rows)
  meridian_customer_profile      (5,001 rows)
  meridian_customer_engagement   (5,001 rows)
  meridian_mta_touchpoints       (42,287 rows)
  meridian_ad_spend_monthly      (  240 rows)
  meridian_recommendation_impressions (1,961 rows)
  meridian_wishlist              (  587 rows)
  meridian_incomplete_applications (  201 rows)

Usage:
    python scripts/upload_meridian_to_databricks.py

    # Dry-run (validate env + list files, no upload):
    python scripts/upload_meridian_to_databricks.py --dry-run

    # Skip already-existing tables:
    python scripts/upload_meridian_to_databricks.py --skip-existing

Prerequisites (.env):
    DATABRICKS_HOST               = https://<workspace>.azuredatabricks.net
    DATABRICKS_TOKEN              = dapi...
    DATABRICKS_SQL_WAREHOUSE_ID   = <warehouse-id>
    DOMAIN_CATALOG                = dev   (default)
    DOMAIN_SCHEMA                 = banking (default)
"""

import os, sys, time, uuid, pathlib, argparse
import requests
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent.parent / ".env")

# ── Config ─────────────────────────────────────────────────────────────────────
HOST      = os.environ.get("DATABRICKS_HOST", "").rstrip("/")
TOKEN     = os.environ.get("DATABRICKS_TOKEN", "")
WAREHOUSE = os.environ.get("DATABRICKS_SQL_WAREHOUSE_ID", "")
CATALOG   = os.environ.get("DOMAIN_CATALOG", "dev")
SCHEMA    = os.environ.get("DOMAIN_SCHEMA", "banking")
VOLUME    = "meridian_preloaded"
DATA_DIR  = pathlib.Path(__file__).parent.parent / "data" / "preloaded" / "meridian_bank"
RUN_ID    = uuid.uuid4().hex[:8]

# (csv_filename, delta_table_name)
TABLES = [
    ("customers.csv",                  "meridian_customers"),
    ("products.csv",                   "meridian_products"),
    ("transactions.csv",               "meridian_transactions"),          # 876K rows — slowest
    ("customer_profile.csv",           "meridian_customer_profile"),
    ("customer_engagement.csv",        "meridian_customer_engagement"),
    ("mta_touchpoint_history.csv",     "meridian_mta_touchpoints"),
    ("ad_spend_monthly.csv",           "meridian_ad_spend_monthly"),
    ("recommendation_impressions.csv", "meridian_recommendation_impressions"),
    ("wishlist.csv",                   "meridian_wishlist"),
    ("incomplete_applications.csv",    "meridian_incomplete_applications"),
]

# ── Auth headers ───────────────────────────────────────────────────────────────

def _headers(content_type: str = "application/json") -> dict:
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": content_type}


# ── SQL warehouse execution ────────────────────────────────────────────────────

def _sql(statement: str, timeout_secs: int = 360) -> dict:
    """Execute SQL via REST warehouse, poll until done. Raises on failure."""
    resp = requests.post(
        f"{HOST}/api/2.0/sql/statements",
        headers=_headers(),
        json={
            "warehouse_id": WAREHOUSE,
            "statement": statement,
            "wait_timeout": f"{min(timeout_secs, 50)}s",  # initial wait ≤50 s
            "on_wait_timeout": "CONTINUE",                 # then poll
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    sid = data.get("statement_id")

    deadline = time.time() + timeout_secs
    while True:
        state = data.get("status", {}).get("state", "UNKNOWN")
        if state in ("SUCCEEDED", "FAILED", "CANCELED", "CLOSED"):
            break
        if time.time() > deadline:
            raise TimeoutError(f"SQL timed out after {timeout_secs}s: {statement[:120]}")
        time.sleep(4)
        r = requests.get(f"{HOST}/api/2.0/sql/statements/{sid}", headers=_headers(), timeout=30)
        r.raise_for_status()
        data = r.json()

    if data.get("status", {}).get("state") != "SUCCEEDED":
        err = data.get("status", {}).get("error", {})
        raise RuntimeError(f"SQL FAILED [{err.get('error_code')}]: {err.get('message','')}\nSQL: {statement[:300]}")
    return data


def _sql_scalar(statement: str) -> str:
    """Return the first cell of the first row (as string)."""
    result = _sql(statement)
    try:
        return str(result["result"]["data_array"][0][0])
    except (KeyError, IndexError, TypeError):
        return "?"


# ── Volume file upload ─────────────────────────────────────────────────────────

def _upload_file(local_path: pathlib.Path, volume_path: str, dry_run: bool = False) -> None:
    """
    Upload a local file to a UC Volume via the Databricks Files API.
    volume_path must start with /Volumes/...  (no host, no /api/... prefix)
    """
    api_path = f"/api/2.0/fs/files{volume_path}"
    url      = f"{HOST}{api_path}"
    size_mb  = local_path.stat().st_size / (1024 * 1024)

    if dry_run:
        print(f"      [dry-run] would PUT {local_path.name} ({size_mb:.1f} MB) → {volume_path}")
        return

    print(f"      Uploading {local_path.name} ({size_mb:.1f} MB) ...", end=" ", flush=True)
    t0 = time.time()

    with open(local_path, "rb") as fh:
        resp = requests.put(
            url,
            headers={"Authorization": f"Bearer {TOKEN}"},
            data=fh,
            timeout=600,        # 10 min — transactions.csv is 876K rows
            stream=False,
        )
    resp.raise_for_status()
    elapsed = time.time() - t0
    print(f"done ({elapsed:.1f}s, {size_mb/elapsed:.1f} MB/s)")


# ── Table existence check ──────────────────────────────────────────────────────

def _table_exists(fqn: str) -> bool:
    try:
        _sql(f"DESCRIBE TABLE {fqn}")
        return True
    except Exception:
        return False


# ── Main orchestration ─────────────────────────────────────────────────────────

def _check_env() -> None:
    missing = []
    for name, val in [("DATABRICKS_HOST", HOST), ("DATABRICKS_TOKEN", TOKEN),
                      ("DATABRICKS_SQL_WAREHOUSE_ID", WAREHOUSE)]:
        if not val:
            missing.append(name)
    if missing:
        print("\nERROR: Missing required environment variables:")
        for m in missing:
            print(f"  {m}")
        print("\nAdd them to your .env file at the project root, then retry.\n")
        sys.exit(1)
    print(f"  Workspace  : {HOST}")
    print(f"  Catalog    : {CATALOG}")
    print(f"  Schema     : {SCHEMA}")
    print(f"  Volume     : {VOLUME}")
    print(f"  Warehouse  : {WAREHOUSE}")


def upload_all(dry_run: bool = False, skip_existing: bool = False) -> None:
    banner = "[DRY RUN] " if dry_run else ""
    print(f"\n{'='*64}")
    print(f"  {banner}Meridian Bank -> Databricks Unity Catalog")
    print(f"  {len(TABLES)} tables | Run ID: {RUN_ID}")
    print(f"{'='*64}\n")

    # ── Validate env
    print("Checking environment...")
    _check_env()
    print()

    # ── Validate source files
    print("Checking source files in data/preloaded/meridian_bank/:")
    missing_files = []
    for csv_name, _ in TABLES:
        p = DATA_DIR / csv_name
        exists = p.exists()
        size_mb = p.stat().st_size / (1024 * 1024) if exists else 0
        status = f"{size_mb:.1f} MB" if exists else "MISSING"
        print(f"  {'OK' if exists else '--'}  {csv_name:<45} {status}")
        if not exists:
            missing_files.append(csv_name)
    if missing_files:
        print(f"\nWARNING: {len(missing_files)} file(s) not found — they will be skipped.")
    print()

    if dry_run:
        print("[dry-run] Stopping here — no changes made.\n")
        return

    # ── Step 1: Ensure schema
    print(f"1/4  Ensuring schema `{CATALOG}`.`{SCHEMA}` exists ...")
    _sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`")
    print("     OK\n")

    # ── Step 2: Ensure volume
    print(f"2/4  Ensuring UC Volume `{CATALOG}`.`{SCHEMA}`.`{VOLUME}` exists ...")
    _sql(f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.`{VOLUME}`")
    vol_base = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
    print(f"     OK  {vol_base}\n")

    # ── Step 3: Upload CSVs
    print(f"3/4  Uploading {len(TABLES)} CSVs to Volume path /{RUN_ID}/...\n")
    uploaded: list[str] = []
    for csv_name, _ in TABLES:
        p = DATA_DIR / csv_name
        if not p.exists():
            print(f"     SKIP {csv_name} (file not found)")
            continue
        _upload_file(p, f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/{RUN_ID}/{csv_name}")
        uploaded.append(csv_name)
    print()

    # ── Step 4: Create Delta tables
    print(f"4/4  Creating Delta tables in `{CATALOG}`.`{SCHEMA}`...\n")
    results = []
    for csv_name, table_name in TABLES:
        if csv_name not in uploaded:
            continue

        fqn       = f"`{CATALOG}`.`{SCHEMA}`.`{table_name}`"
        vol_file  = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/{RUN_ID}/{csv_name}"

        if skip_existing and _table_exists(fqn):
            print(f"     SKIP {fqn} (already exists, --skip-existing)")
            results.append({"fqn": fqn, "status": "skipped"})
            continue

        create_sql = f"""
CREATE OR REPLACE TABLE {fqn}
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact'   = 'true'
)
AS
SELECT * FROM read_files(
  '{vol_file}',
  format      => 'csv',
  header      => true,
  inferSchema => true
)
""".strip()

        print(f"     Creating {fqn} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            _sql(create_sql, timeout_secs=360)
            elapsed = time.time() - t0
            row_count = _sql_scalar(f"SELECT COUNT(*) FROM {fqn}")
            print(f"done ({elapsed:.0f}s) — {int(row_count):,} rows")
            results.append({"fqn": fqn, "rows": row_count, "status": "ok"})
        except Exception as exc:
            print(f"\n     ERROR: {exc}\n")
            results.append({"fqn": fqn, "status": "error", "error": str(exc)})

    # ── Summary
    ok    = [r for r in results if r["status"] == "ok"]
    skip  = [r for r in results if r["status"] == "skipped"]
    fail  = [r for r in results if r["status"] == "error"]

    print(f"\n{'='*64}")
    print(f"  UPLOAD COMPLETE: {len(ok)} created | {len(skip)} skipped | {len(fail)} failed")
    print(f"{'='*64}")
    for r in ok:
        print(f"  OK     {r['fqn']}  ({r['rows']} rows)")
    for r in skip:
        print(f"  SKIP   {r['fqn']}")
    for r in fail:
        print(f"  ERROR  {r['fqn']}  {r.get('error','')[:80]}")

    if ok:
        print(f"""
Next steps:
  1. Go to your Databricks workspace -> AI/BI -> Genie
  2. Open (or create) your Genie space
  3. Add all {len(ok)} tables above as data sources:
       {CATALOG}.{SCHEMA}.meridian_customers
       {CATALOG}.{SCHEMA}.meridian_customer_profile
       {CATALOG}.{SCHEMA}.meridian_transactions
       ... (all meridian_* tables)
  4. Copy the space ID from the URL and update GENIE_SPACE_ID in .env
  5. Restart the backend: uvicorn api.main_unified_chromadb:app --port 8002 --reload
  6. Run Agent A segmentation in the app
  7. Click "Sync to Databricks" -> use Segment AI chatbot
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Meridian Bank data to Databricks Unity Catalog")
    parser.add_argument("--dry-run",       action="store_true", help="Validate env + list files without uploading")
    parser.add_argument("--skip-existing", action="store_true", help="Skip tables that already exist in the catalog")
    args = parser.parse_args()
    upload_all(dry_run=args.dry_run, skip_existing=args.skip_existing)
