# Databricks Deployment Details – For Academy Sports Repo

Use this document in the **Academy Sports product’s Cursor** so it can apply the same deployment setup and then deploy to Databricks via Git.

**Quick reference:** Run from repo root → `run_app.py` (sets cwd, runs FastAPI). Config → `app.yaml` (command only). API key → `.env` in repo (not in Git). Frontend → build with `VITE_API_BASE_URL=` and `VITE_BASE_PATH=/`, serve `frontend/dist` from FastAPI. One port for API + UI.

---

## 1. Code Updates Done in This Repo (Banking) Before Databricks Deployment

These are the patterns and files that were added or updated for Databricks deployment. Replicate the same ideas in the Academy Sports repo.

### 1.1 App entry point and port

- **`run_app.py`** at repo root:
  - Sets working directory to repo root (so `data/`, `api/`, `frontend/dist` resolve correctly).
  - Adds repo root to `sys.path` for imports.
  - Runs FastAPI via `uvicorn` on `host="0.0.0.0"` and port from `DATABRICKS_APP_PORT` (default `8080`).

- **`app.yaml`** (Databricks App config):
  - Single `command` that runs: `python run_app.py`.
  - No Secret env in `app.yaml`; API key is provided via `.env` in the repo (see below).

### 1.2 Environment variables (.env)

- **Load .env in API**: At the top of `api/main_unified_chromadb.py`, right after imports from stdlib:
  - `from dotenv import load_dotenv` and `load_dotenv()` so `.env` in repo root is loaded.
- **Load .env in utils**: In `utils/together_ai.py` (or wherever you call Together AI), load from repo root:
  - `env_path = Path(__file__).resolve().parent.parent / '.env'`
  - If `env_path.exists()`, call `load_dotenv(env_path)`.
- **API key usage**: Use `os.getenv("TOGETHER_API_KEY", "")` everywhere; no hardcoded keys in code.
- **.gitignore**: Ensure `.env`, `.env.local`, `.env.*.local` are in `.gitignore` so API keys are never committed.

### 1.3 Frontend build for single-port deployment

- **Build script**: In `frontend/package.json`, add (or keep) a script that builds with empty API base and base path for “same origin”:
  - `"build:single-port": "cross-env VITE_API_BASE_URL= VITE_BASE_PATH=/ vite build"`
- **Vite config**: In `frontend/vite.config.ts`, set `base` so that when `VITE_BASE_PATH` is set (e.g. to `/`), the app is served from root:
  - e.g. `base: process.env.VITE_BASE_PATH ? \`${process.env.VITE_BASE_PATH.replace(/\\/$/, '')}/\` : ...`
- **API base in frontend**: In the utility that builds API base URL (e.g. `getBankingApiBase()` or equivalent for Academy):
  - If `VITE_API_BASE_URL` is set (string), use it.
  - If not set (e.g. empty string in single-port build), use same origin: empty string or derive from `window.location.pathname` if you use a path prefix like `/academy-platform/v1`.
  - Local dev fallback: `http://localhost:8002` (or your backend port).

### 1.4 Backend serving the frontend (single port)

- In the FastAPI app (e.g. `api/main_unified_chromadb.py`):
  - Define `frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")`.
  - If `os.path.exists(frontend_dist)`:
    - Mount: `app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")`.
    - `GET "/"` → `FileResponse(os.path.join(frontend_dist, "index.html"))`.
    - `GET "/{full_path:path}"` → if `full_path` does not start with `api/`, return `FileResponse(index.html)` so SPA routing works; if it starts with `api/`, return 404 with a message like “API route not found. If you added a new endpoint, restart the backend.”
  - This way one process serves both API and frontend on the same port (Databricks Apps forwards to one port).

### 1.5 Deploy documentation in repo

- **`deploy/DATABRICKS_ENV_FILE.md`**: Step-by-step for adding a `.env` file **inside the repo in Databricks** with `TOGETHER_API_KEY=...`, and redeploying the app. Note: do not commit `.env`; create it only in the Databricks copy of the repo.
- **`app.yaml` comment**: In `app.yaml`, add a short comment that `TOGETHER_API_KEY` is set via a `.env` file in the repo and point to `deploy/DATABRICKS_ENV_FILE.md`.

---

## 2. Files to Create or Update in Academy Sports Repo

Give the Academy Sports Cursor this checklist. Paths are relative to repo root.

| Item | Path | Action |
|------|------|--------|
| App command | `app.yaml` | Create or update: `command: [python, run_app.py]` and comment about `.env`. |
| Launcher | `run_app.py` | Create: set repo root, `os.chdir(REPO_ROOT)`, `sys.path`, then `uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", "8080")))`. |
| Load .env in API | `api/main_*.py` (or main app file) | At top, add `from dotenv import load_dotenv` and `load_dotenv()`. |
| Load .env in utils | `utils/together_ai.py` (or equivalent) | Load `.env` from repo root with `Path(__file__).resolve().parent.parent / '.env'` and `load_dotenv(env_path)` if exists. |
| Frontend build | `frontend/package.json` | Add script: `"build:single-port": "cross-env VITE_API_BASE_URL= VITE_BASE_PATH=/ vite build"`. |
| Frontend base / API base | `frontend/vite.config.ts`, `frontend/src/utils/apiBase.ts` (or equivalent) | Use `VITE_BASE_PATH` and `VITE_API_BASE_URL` so production build works with same-origin API. |
| Serve frontend | `api/main_*.py` | Add `frontend_dist`, mount `/assets`, serve `index.html` for `/` and non-API paths. |
| Ignore .env | `.gitignore` | Ensure `.env` and `.env.*.local` are listed. |
| Docs | `deploy/DATABRICKS_ENV_FILE.md` | Add steps to create `.env` in Databricks repo and redeploy. |

---

## 3. Exact Snippets to Reuse

### 3.1 `run_app.py` (repo root)

```python
"""
Launcher for Databricks Apps: ensure we run from repo root, then start FastAPI.
Use this as the app command so paths (data/, api/, frontend/dist) resolve correctly.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if __name__ == "__main__":
    import uvicorn
    from api.main_unified_chromadb import app   # or your Academy main module
    port = int(os.environ.get("DATABRICKS_APP_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### 3.2 `app.yaml` (repo root)

```yaml
# Databricks Apps: run FastAPI on one port serving API + React frontend (same port).
# run_app.py sets working directory to repo root so data/, api/, frontend/dist resolve correctly.
#
# TOGETHER_API_KEY: Create a .env file in this repo in Databricks (same folder as run_app.py)
# with: TOGETHER_API_KEY=your_key. See deploy/DATABRICKS_ENV_FILE.md for steps.
command:
  - python
  - run_app.py
```

### 3.3 API: load .env (top of main API file)

```python
# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()
```

### 3.4 Frontend build (single-port)

```bash
cd frontend
npm run build:single-port
```

This must produce `frontend/dist/` with `index.html` and `assets/`. For Databricks Git deploy, either: (1) **Commit** `frontend/dist/` so the repo is self-contained and no Node/npm is needed in Databricks, or (2) **Do not commit** and run `npm ci && npm run build:single-port` in a Databricks job/notebook before starting the app.

### 3.5 API base for same-origin (concept)

```ts
// Empty string = same-origin (single-port deployment e.g. Databricks)
if (typeof import.meta.env.VITE_API_BASE_URL === 'string') {
  return import.meta.env.VITE_API_BASE_URL;
}
// Optional: if deployed under a path like /academy-platform/v1
if (typeof window !== 'undefined') {
  const m = window.location.pathname.match(/^(\/academy-platform\/v1)/);
  if (m) return m[1];
}
return 'http://localhost:8002';  // or your dev port
```

---

## 4. Git-based Deployment on Databricks

1. **Connect repo**: In Databricks, **Repos** → connect the Academy Sports GitHub repo.
2. **App config**: Create an App that runs from the repo with **App type** = Repo and **Path** = repo root (or the folder that contains `app.yaml` and `run_app.py`). Command is taken from `app.yaml` (python + run_app.py).
3. **.env in Databricks only**: In the Databricks repo browser, create a file named `.env` (same level as `run_app.py`), add `TOGETHER_API_KEY=your_key`, save. Do **not** commit `.env` to Git.
4. **Build frontend (if not committed)**: If you don’t commit `frontend/dist`, add a build step (e.g. in a notebook or job) that runs `cd frontend && npm ci && npm run build:single-port` before starting the app, and ensure the app runs from the repo root so `frontend/dist` exists when the API starts.
5. **Deploy / Restart**: Deploy or restart the App; it will use the repo root as cwd and read `.env` from there.
6. **Updates**: Push changes to Git; in Databricks Repos click **Update** (pull), then redeploy/restart the App.

---

## 5. Summary for Academy Sports Cursor

- Add or update **`run_app.py`** and **`app.yaml`** at repo root.
- Load **`.env`** in the main API file and in any util that uses `TOGETHER_API_KEY`; keep **`.env`** in **`.gitignore`**.
- Add **`build:single-port`** and ensure **Vite** and **API base** logic use empty/base path for same-origin in production.
- Serve **`frontend/dist`** from FastAPI (**/assets** + **index.html** for SPA).
- Add **`deploy/DATABRICKS_ENV_FILE.md`** with steps to create `.env` in the Databricks repo and redeploy.

After that, the Academy Sports app can be deployed to Databricks via Git the same way as this banking app.
