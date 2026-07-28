#!/usr/bin/env bash
# Copy local F&M preloaded CSVs to DBFS for notebooks / Genie staging.
# Prereq: Databricks CLI logged in (`databricks auth login` or `databricks configure`).
#
# Usage (from repo root):
#   bash scripts/databricks/copy_preload_to_dbfs.sh
# Optional:
#   DBFS_DEST=dbfs:/FileStore/my_team/fmb_bank bash scripts/databricks/copy_preload_to_dbfs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC="$REPO_ROOT/data/preloaded/fmb_bank"
DEST="${DBFS_DEST:-dbfs:/FileStore/fmb_bank}"

if [[ ! -d "$SRC" ]]; then
  echo "Source folder not found: $SRC" >&2
  exit 1
fi

echo "Copying:"
echo "  From: $SRC"
echo "  To:   $DEST"
echo ""

databricks fs cp -r "$SRC" "$DEST"

echo ""
echo "Done. In a notebook use path like: $DEST/customers.csv"
