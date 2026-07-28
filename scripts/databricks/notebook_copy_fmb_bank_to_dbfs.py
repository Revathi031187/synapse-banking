# Databricks notebook — find repo + copy banking preloaded CSVs to DBFS (for Genie / Spark loads).
# Paste cells below into a Python notebook on a cluster, or %run this file from Repos.
#
# Banking data lives at: data/preloaded/fmb_bank/
# (not academy_sports)

from pathlib import Path

# --- Cell 1: find repo root (adjust emails / folder names to match YOUR Repos checkout) ---
candidates = [
    Path("/Workspace/Repos/jaisonsamuel.d@latentviewo365.onmicrosoft.com/NBA"),
    Path("/Workspace/Repos/jaisonsamuel.d@latentview365.onmicrosoft.com/NBA"),
    Path("/Workspace/Repos/jaisonsamuel.d@latentviewo365.onmicrosoft.com/personalization-agent-banking"),
    Path("/Workspace/Repos/jaisonsamuel.d@latentview365.onmicrosoft.com/personalization-agent-banking"),
    Path("/Repos/jaisonsamuel.d@latentviewo365.onmicrosoft.com/NBA"),
    Path("/Repos/jaisonsamuel.d@latentviewo365.onmicrosoft.com/personalization-agent-banking"),
]

# Subfolder if repo is nested
expanded = []
for base in list(candidates):
    expanded.append(base)
    expanded.append(base / "personalization-agent-banking")
    expanded.append(base / "personalization-agent")

repo_root = None
for p in expanded:
    if not p.exists():
        continue
    fmb = p / "data" / "preloaded" / "fmb_bank"
    run_app = p / "run_app.py"
    api_main = p / "api" / "main_unified_chromadb.py"
    if fmb.exists():
        repo_root = p
        print(f"FOUND fmb_bank: {fmb}")
        print(f"  CSV files: {sorted(x.name for x in fmb.glob('*.csv'))}")
        break
    if run_app.exists() or api_main.exists():
        print(f"Repo candidate (no fmb_bank yet): {p}")
        if (p / "data" / "preloaded").exists():
            print(f"  preloaded: {list((p / 'data' / 'preloaded').iterdir())}")

if repo_root is None:
    print("fmb_bank not found in candidates. Listing /Workspace/Repos (first level)...")
    repos = Path("/Workspace/Repos")
    if repos.exists():
        for user_dir in repos.iterdir():
            if not user_dir.is_dir():
                continue
            for proj in user_dir.iterdir():
                if not proj.is_dir():
                    continue
                fmb = proj / "data" / "preloaded" / "fmb_bank"
                if fmb.exists():
                    repo_root = proj
                    print(f"FOUND fmb_bank: {fmb}")
                    break
            if repo_root:
                break

if repo_root is None:
    raise FileNotFoundError(
        "Could not find data/preloaded/fmb_bank under known paths. "
        "Set repo_root manually, e.g. repo_root = Path('/Workspace/Repos/<you>/<repo>')"
    )

# --- Cell 2: copy F&M banking CSVs to DBFS (driver-local /dbfs path) ---
import shutil

src = repo_root / "data" / "preloaded" / "fmb_bank"
dst = Path("/dbfs/FileStore/fmb_bank")

if not src.exists():
    raise FileNotFoundError(f"Banking data not found at {src}. Check repo path.")

dst.mkdir(parents=True, exist_ok=True)
copied = []
for f in sorted(src.glob("*.csv")):
    # Skip obvious backups if you want only core tables:
    # if "OLD_BACKUP" in f.name or "BACKUP" in f.name:
    #     continue
    shutil.copy2(f, dst / f.name)
    copied.append(f.name)

print("Copied to DBFS:", dst)
print("Files:", sorted(copied))
print("\nUse in Spark / load script, e.g. BASE_PATH = 'dbfs:/FileStore/fmb_bank'")

# --- Cell 3: REQUIRED for Unity Catalog — DBFS files alone do NOT show up under dev.banking ---
# Catalog Explorer only lists managed/external TABLES. You must run Spark saveAsTable (below).
# Cluster: Single-user or Shared with Unity Catalog (not legacy Hive-only).

CATALOG = "dev"
SCHEMA = "banking"
DBFS_CSV = "dbfs:/FileStore/fmb_bank"  # must match Cell 2 destination

_tables = [
    ("customers", "customers.csv"),
    ("products", "products.csv"),
    ("transactions", "transactions.csv"),
]

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

for table_name, csv_name in _tables:
    path = f"{DBFS_CSV.rstrip('/')}/{csv_name}"
    fqn = f"{CATALOG}.{SCHEMA}.{table_name}"
    print(f"UC load: {path} -> {fqn}")
    df = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .option("multiLine", True)
        .option("escape", '"')
        .csv(path)
    )
    n = df.count()
    print(f"  rows: {n}")
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(fqn)
    )

print("\nVerify in SQL editor (catalog = dev, NOT hive_metastore):")
print("  SHOW TABLES IN dev.banking;")
print("  SELECT COUNT(*) FROM dev.banking.customers;")

spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}").show(truncate=False)
