# Add Together API key using a .env file in Databricks

If you can’t use Secrets, add a `.env` file **inside the repo in Databricks**. The app already loads it from the repo root.

---

## Step 1 – Open the repo in Databricks

1. In the left sidebar, click **Workspace** (or **Recents**).
2. Go to the folder where **personalization-agent-banking** lives (e.g. **Repos** → **personalization-agent-banking**, or your user folder → the repo).
3. Click the repo name so you see its files (e.g. `run_app.py`, `app.yaml`, `api/`, `frontend/`, etc.).

---

## Step 2 – Create a new file in the repo

1. In the repo view, look for **Create** or **Add file** (or a **+** button).
2. Click it and choose **Create** / **New file** (or **File**).
3. When asked for the file name, enter exactly:  
   **`.env`**  
   (dot, then the letters e-n-v, no space, no .txt.)

If the UI doesn’t allow a name starting with a dot:

- Try **Create** → **File** and type `.env` in the path/name field.
- Or create a file named `env.txt`, then rename it to `.env` if the UI has a rename option.
- Some UIs use a path like: `personalization-agent-banking/.env`.

---

## Step 3 – Put your API key in the file

1. Open the `.env` file you created.
2. Add **one line** (replace with your real key):

   ```text
   TOGETHER_API_KEY=your_together_api_key_here
   ```

   No spaces around `=`. No quotes unless your key has spaces (usually it doesn’t).

3. **Save** the file (e.g. **Save** or **Ctrl+S** / **Cmd+S**).

---

## Step 4 – Redeploy the app

1. Go to **Apps** in the sidebar and open your **personalization-agent-banking** app.
2. **Redeploy** (e.g. **Deploy** dropdown → **Deploy** again, or **Restart**).
3. The app runs from the repo root and will load `.env` from there, so it will now see `TOGETHER_API_KEY`.

---

## Checklist

- [ ] Repo **personalization-agent-banking** is open in Workspace.
- [ ] A file named **`.env`** exists in that repo (same level as `run_app.py`).
- [ ] The file contains: **`TOGETHER_API_KEY=your_key`** (and is saved).
- [ ] App was **redeployed** after adding `.env`.

---

## Security note

- **Do not** commit `.env` to Git. Keep it only in the Databricks repo so your key stays out of version control.
- Only people who can see or edit files in that repo in Databricks can see the key. Restrict repo access if needed.

---

## If you don’t add .env

The app still runs. Marketing opportunities will use the fallback (trait-based text with segment metrics) and will not call the Together API.
