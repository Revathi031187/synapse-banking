# Databricks notebook: load F&M Bank CSVs into Unity Catalog `dev.banking`.
#
# Prefer the web app when the API can reach Databricks: POST /api/banking/uc/preloaded/upload
# reads data/preloaded/fmb_bank from the server and uploads via Files API + SQL warehouse.
#
# IMPORTANT: Running this file only *defines* load_fmb_bank_to_uc() unless auto-run runs.
# Tables are created only when that function RUNS (see auto-run at bottom, or add your own cell).
#
# UC: dev.banking = catalog `dev` + schema `banking`.
#
# 1) Upload CSVs (from laptop, repo root):
#    databricks fs cp -r data/preloaded/fmb_bank dbfs:/FileStore/fmb_bank/
#
# 2) Cluster must use Unity Catalog (access mode Single user / Shared with UC).
#
# 3) Run this notebook. By default the bottom of this file auto-runs the load.
#    Override path:  FMB_BANK_UC_PATH=/Volumes/dev/banking/raw/fmb_bank  (cluster env)
#    Or disable auto-run: FMB_BANK_UC_AUTO_RUN=0

from __future__ import annotations

import os
from typing import Iterable, List, Tuple

DEFAULT_BASE_PATH = "dbfs:/FileStore/fmb_bank"


def verify_uploaded_csvs(base_path: str) -> None:
    """List folder; raises if missing. Requires dbutils (Databricks)."""
    base = base_path.rstrip("/")
    try:
        dbutils  # type: ignore[name-defined]
    except NameError:
        print("skip verify: dbutils not available")
        return
    try:
        entries = dbutils.fs.ls(base)  # type: ignore[name-defined]
        names = sorted([e.name for e in entries])
        print(f"Contents of {base} ({len(names)} entries): {names[:20]}{'...' if len(names) > 20 else ''}")
        needed = {"customers.csv", "products.csv", "transactions.csv"}
        missing = needed - set(names)
        if missing:
            raise FileNotFoundError(
                f"Missing CSV(s) in {base}: {missing}. "
                f"Upload with: databricks fs cp -r data/preloaded/fmb_bank {base}/"
            )
    except Exception as e:
        if "FileNotFoundException" in type(e).__name__ or "does not exist" in str(e).lower():
            raise FileNotFoundError(
                f"Path not found: {base}. Upload CSVs there or set FMB_BANK_UC_PATH to the correct folder."
            ) from e
        raise


def load_fmb_bank_to_uc(
    spark,
    base_path: str,
    catalog: str = "dev",
    schema: str = "banking",
    tables: Iterable[Tuple[str, str]] | None = None,
    verify_first: bool = True,
) -> List[str]:
    """
    Read CSVs from base_path and overwrite Delta tables catalog.schema.<name>.

    :param spark: SparkSession
    :param base_path: e.g. dbfs:/FileStore/fmb_bank or /Volumes/dev/banking/landing/fmb_bank
    :param catalog: Unity Catalog catalog (default dev)
    :param schema: Unity Catalog schema (default banking)
    :param tables: list of (table_name, csv_filename); default core banking trio
    :param verify_first: list DBFS/Volume folder and check for required CSV names
    :return: list of fully qualified table names written
    """
    if tables is None:
        tables = [
            ("customers", "customers.csv"),
            ("products", "products.csv"),
            ("transactions", "transactions.csv"),
        ]
    tables = list(tables)

    base = base_path.rstrip("/")
    if verify_first:
        verify_uploaded_csvs(base)

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")

    written: List[str] = []
    for table_name, csv_name in tables:
        csv_path = f"{base}/{csv_name}"
        fqn = f"{catalog}.{schema}.{table_name}"
        print(f"Loading {csv_path} -> {fqn}")
        df = (
            spark.read.option("header", True)
            .option("inferSchema", True)
            .option("multiLine", True)
            .option("escape", '"')
            .csv(csv_path)
        )
        n = df.count()
        if n == 0:
            raise RuntimeError(
                f"No rows read from {csv_path}. Check path, permissions, and that the file is not empty."
            )
        print(f"  rows read: {n}")
        (
            df.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(fqn)
        )
        written.append(fqn)
        print(f"  OK: {fqn}")

    print("Done. In SQL: SHOW TABLES IN dev.banking;  SELECT COUNT(*) FROM dev.banking.customers;")
    return written


# =============================================================================
# Auto-run when this file is executed as a notebook (Run All)
# Set cluster env FMB_BANK_UC_AUTO_RUN=0 to only define the function.
# Set FMB_BANK_UC_PATH to your folder if not using dbfs:/FileStore/fmb_bank
# =============================================================================
def _maybe_auto_run() -> None:
    if os.environ.get("FMB_BANK_UC_AUTO_RUN", "1").strip().lower() in ("0", "false", "no"):
        print(
            "FMB_BANK_UC_AUTO_RUN is off. Run manually:\n"
            "  load_fmb_bank_to_uc(spark, 'dbfs:/FileStore/fmb_bank', catalog='dev', schema='banking')"
        )
        return
    try:
        spark_session = spark  # noqa: F821  # provided by Databricks notebook
    except NameError:
        print(
            "No `spark` session — not running inside a Databricks Python notebook, or cell order is wrong.\n"
            "Add a cell with:\n"
            f"  load_fmb_bank_to_uc(spark, '{DEFAULT_BASE_PATH}', catalog='dev', schema='banking')"
        )
        return

    base = os.environ.get("FMB_BANK_UC_PATH", "").strip() or DEFAULT_BASE_PATH
    print(f"Auto-run: loading from {base} (override with env FMB_BANK_UC_PATH)")
    try:
        load_fmb_bank_to_uc(spark_session, base, catalog="dev", schema="banking")
    except Exception as e:
        print(f"LOAD FAILED: {e}\n")
        print(
            "Checklist:\n"
            "  1) Upload CSVs: databricks fs cp -r data/preloaded/fmb_bank dbfs:/FileStore/fmb_bank/\n"
            "  2) Catalog Explorer: open catalog **dev** → schema **banking** (not hive_metastore)\n"
            "  3) Cluster: UC-enabled (Data governance + Unity Catalog)\n"
            "  4) Permission: CREATE TABLE on dev.banking\n"
        )
        raise


_maybe_auto_run()


# =============================================================================
# Manual second cell (if you disabled auto-run or use %run as library)
# =============================================================================
# load_fmb_bank_to_uc(spark, "dbfs:/FileStore/fmb_bank", catalog="dev", schema="banking")
#
# Optional widgets (run once to create):
# dbutils.widgets.text("base_path", "dbfs:/FileStore/fmb_bank")
# load_fmb_bank_to_uc(spark, dbutils.widgets.get("base_path"))
#
# Extra tables:
# EXTRA = [("wishlist", "wishlist.csv"), ("incomplete_applications", "incomplete_applications.csv")]
# load_fmb_bank_to_uc(spark, BASE_PATH, tables=[("customers","customers.csv"),("products","products.csv"),("transactions","transactions.csv"), *EXTRA])
