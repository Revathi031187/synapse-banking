# Step-by-step: Add Together API key via Databricks Secrets

Use these steps so your Databricks App gets **unique marketing opportunities per segment** using the Together AI API.

---

## Part 1: Create the secret in Databricks

### Step 1.1 – Open Secret Scopes

1. In your Databricks workspace, click the **Settings** (gear) icon in the left sidebar.
2. Under **Workspace**, click **Secrets** (or **Secret scopes**).
3. You’ll see the list of secret scopes.

**Shortcut (if your workspace allows):**  
Go to: `https://<your-workspace-url>#secrets/createScope`  
(Replace `<your-workspace-url>` with your actual Databricks URL, e.g. `adb-xxxxx.azuredatabricks.net`.)

---

### Step 1.2 – Create a secret scope (if you don’t have one)

1. Click **Create scope** (or **Create secret scope**).
2. **Name:** e.g. `personalization-app` (only letters, numbers, dashes, underscores; max 128 chars).
3. **Manage principal:** choose **Creator** (only you) or **All workspace users** (if others need access).
4. Click **Create**.

If you already have a scope (e.g. for other app secrets), you can use that and skip to Step 1.3.

---

### Step 1.3 – Add the Together API key as a secret

1. Open the scope you created (e.g. `personalization-app`) by clicking its name.
2. Click **Add secret** (or **Add** / **New secret**).
3. Fill in:
   - **Key:** `together_api_key`  
     (This is the name of the secret inside the scope. Use exactly this if you want to match the steps below.)
   - **Value:** paste your Together AI API key (from [Together AI](https://api.together.xyz/settings/api-keys)).
4. Click **Save** (or **Add**).

You should now see `together_api_key` listed under that scope.

---

### Step 1.4 – (Optional) Using the CLI instead of the UI

If you use the Databricks CLI:

```bash
# Create scope (if needed)
databricks secrets create-scope personalization-app

# Add the API key (replace YOUR_ACTUAL_KEY with your key)
databricks secrets put-secret --json '{"scope": "personalization-app", "key": "together_api_key", "string_value": "YOUR_ACTUAL_KEY"}'
```

---

## Part 2: Give your App access to the secret

The App must have a **resource** that points to this secret. Databricks will inject it as the environment variable `TOGETHER_API_KEY` (as defined in your `app.yaml`).

### Step 2.1 – Open your App

1. In the left sidebar, click **Apps** (or **Dev** → **Apps** / **Applications**).
2. Open the app that runs this repo (the one that uses `run_app.py`).

---

### Step 2.2 – Open App configuration

1. Click the **⋮** (three dots) or **Settings** for the app.
2. Choose **Edit** or **Configure** (or the option that shows the app’s **Resources** and **Environment**).

---

### Step 2.3 – Add a Secret resource

1. Find the **Resources** section.
2. Click **Add resource** (or **+ Resource**).
3. Select **Secret**.
4. Fill in:
   - **Secret scope:** the scope you used (e.g. `personalization-app`).
   - **Secret key:** the key you used (e.g. `together_api_key`).
   - **Resource key:** `together_api_key`  
     ⚠️ **Important:** This must be exactly `together_api_key` because your `app.yaml` has:
     ```yaml
     env:
       - name: TOGETHER_API_KEY
         valueFrom: together_api_key
     ```
5. Save the resource (e.g. **Add** / **Save**).

---

### Step 2.4 – Save the App

Click **Save** (or **Update**) so the App configuration is stored.

---

## Part 3: Redeploy the App

1. **Redeploy** the app (e.g. **Deploy** dropdown → **Deploy** again, or **Restart** if your UI has it).
2. After the app is running, it will receive `TOGETHER_API_KEY` from the secret and use it for marketing opportunities.

---

## Checklist

- [ ] Secret scope created (e.g. `personalization-app`).
- [ ] Secret added with key `together_api_key` and value = your Together API key.
- [ ] App resource added: type **Secret**, scope and secret key set, **resource key** = `together_api_key`.
- [ ] App configuration saved.
- [ ] App redeployed.

---

## If something doesn’t work

- **App still uses fallback text:**  
  Confirm the secret’s **resource key** in the App is exactly `together_api_key` (no spaces, same spelling).  
  Confirm the app was **redeployed** after adding the resource.

- **Permission errors:**  
  Your user (or the app’s identity) needs at least **Can read** on the secret scope. In **Settings → Secrets**, open the scope and check **Permission** / **Access control**.

- **No “Secrets” in Settings:**  
  Your workspace may use a different location for secrets (e.g. under **Workspace** or **Admin**). Ask your admin or check [Databricks secret management](https://docs.databricks.com/en/security/secrets/).

---

**If you don’t add the secret:**  
The app still runs. Marketing opportunities will use the fallback (trait-based text with segment metrics) and will not call the Together API.
