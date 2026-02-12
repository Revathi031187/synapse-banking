"""
Launcher for Databricks Apps: ensure we run from repo root, then start FastAPI.
Use this as the app command so paths (data/, api/, frontend/dist) resolve correctly.
"""
import os
import sys
from pathlib import Path

# Repo root = directory containing this script
REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if __name__ == "__main__":
    import uvicorn
    from api.main_unified_chromadb import app
    # Databricks Apps proxy forwards to the port in DATABRICKS_APP_PORT; use it or 8080 locally
    port = int(os.environ.get("DATABRICKS_APP_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
