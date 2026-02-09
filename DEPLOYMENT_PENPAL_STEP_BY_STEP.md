# Personalization Agent Banking – Penpal Server Deployment (Step-by-Step)

Deploy this project to **54.160.147.118** (AI Penpal server) without affecting the existing NBA platform at `/nba-platform/v3/`.

- **Server:** 54.160.147.118  
- **User:** aipenpaladm  
- **This app URL:** `https://54.160.147.118/banking-platform/v1/`  
- **Existing app (do not touch):** `https://penpal.latentview.com/nba-platform/v3/` (or same IP)

---

## Step 1 – Connect and run space/feasibility analysis

**Purpose:** Check disk space, existing projects, and that we do not overwrite anything.

Run on your **local machine** (PowerShell or Git Bash):

```bash
ssh aipenpaladm@54.160.147.118
```

After you are logged in, run these **one at a time** and share the output so we can confirm it’s safe to proceed.

**1a) Disk space**

```bash
df -h
```

**1b) Space under your home (existing projects)**

```bash
du -sh /home/aipenpaladm/* 2>/dev/null
```

**1c) What is using Nginx (existing URLs)**

```bash
ls -la /etc/nginx/sites-enabled/
```

```bash
grep -E "location|root|proxy_pass" /etc/nginx/sites-enabled/default
```

**1d) Ports in use (confirm 8000 is existing backend)**

```bash
sudo ss -tulnp | grep -E ":8000|:8001|:443"
```

**1e) Optional – run the project’s space check script if you already have the repo**

```bash
cd /home/aipenpaladm/personalization-agent-banking 2>/dev/null && bash check_server_space.sh || echo "Repo not cloned yet - skip"
```

Share the outputs of **1a–1d** (and 1e if you ran it). Once we confirm there is enough space and that `/nba-platform/v3/` and port 8000 are untouched, we proceed to Step 2.

---

## Step 2 – Clone or update the repo

**If the repo is not on the server yet:**

```bash
cd /home/aipenpaladm
git clone https://github.com/YOUR_ORG/personalization-agent-banking.git
cd personalization-agent-banking
```

*(Replace `YOUR_ORG` with your actual GitHub org or username.)*

**If the repo is already there (e.g. you pushed from your machine and want to deploy):**

```bash
cd /home/aipenpaladm/personalization-agent-banking
git pull origin main
```

Share the last few lines of the `git` command output so we know the code is up to date.

---

## Step 3 – Backend: virtualenv and dependencies

```bash
cd /home/aipenpaladm/personalization-agent-banking
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

If any `pip` step fails, paste the error. Otherwise, confirm with:

```bash
pip list | head -25
```

---

## Step 4 – Backend: quick run test (no systemd yet)

```bash
cd /home/aipenpaladm/personalization-agent-banking
source venv/bin/activate
uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8001
```

Leave this running. In **another** SSH session (or from your PC):

```bash
curl -s http://54.160.147.118:8001/api/banking/status
```

If you get JSON back, the backend is fine. Stop the uvicorn process with `Ctrl+C` and tell me you’re ready for Step 5.

---

## Step 5 – Backend: systemd service (port 8001)

We use port **8001** so the existing NBA backend on **8000** is not touched.

Create the service file:

```bash
sudo nano /etc/systemd/system/banking-backend.service
```

Paste this (path must be exactly your project path):

```ini
[Unit]
Description=Personalization Agent Banking Backend
After=network.target

[Service]
Type=simple
User=aipenpaladm
Group=aipenpaladm
WorkingDirectory=/home/aipenpaladm/personalization-agent-banking
Environment="PATH=/home/aipenpaladm/personalization-agent-banking/venv/bin"
ExecStart=/home/aipenpaladm/personalization-agent-banking/venv/bin/uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save and exit (`Ctrl+O`, Enter, `Ctrl+X`). Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable banking-backend
sudo systemctl start banking-backend
sudo systemctl status banking-backend
```

Share the `status` output. It should show “active (running)”. Then:

```bash
curl -s http://localhost:8001/api/banking/status
```

If that returns JSON, the backend is deployed. We’ll add Nginx and frontend next.

---

## Step 6 – Frontend: build with banking base path

On the server:

```bash
cd /home/aipenpaladm/personalization-agent-banking/frontend
npm install
```

Then build for the **banking** URL path (so we don’t touch `/nba-platform/v3/`):

```bash
VITE_BASE_PATH=/banking-platform/v1 VITE_API_BASE_URL=/banking-platform/v1 npm run build
```

If the build fails, share the error. If it succeeds, you should see a `dist` directory (Vite default). Confirm:

```bash
ls -la dist
```

---

## Step 7 – Nginx: add banking app and API proxy

We will add a **new** location block; the existing `/nba-platform/v3/` block stays as-is.

**7a) Backup and open config**

```bash
sudo cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.bak.$(date +%Y%m%d)
sudo nano /etc/nginx/sites-enabled/default
```

**7b) Add this block**  
Place it **inside** the `server { ... }` that listens on `443` (or your main server block). Do **not** remove any existing `location` blocks.

```nginx
    # Personalization Agent Banking (new app - do not remove nba-platform block)
    location /banking-platform/v1/ {
        alias /var/www/html/banking-platform/v1/;
        try_files $uri $uri/ /banking-platform/v1/index.html;
    }
    location /banking-platform/v1/api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
    }
```

**7c) Create the docroot and copy frontend build**

```bash
sudo mkdir -p /var/www/html/banking-platform/v1
sudo cp -r /home/aipenpaladm/personalization-agent-banking/frontend/dist/* /var/www/html/banking-platform/v1/
sudo chown -R www-data:www-data /var/www/html/banking-platform
```

**7d) Test and reload Nginx**

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Share the output of `nginx -t` and any reload errors. If both are OK, we’ll verify the URL.

---

## Step 8 – Verify deployment

From your browser or from the server:

- App: **https://54.160.147.118/banking-platform/v1/**  
- (If you use a domain for the same server, e.g. penpal.latentview.com: **https://penpal.latentview.com/banking-platform/v1/**)

From the server:

```bash
curl -s -o /dev/null -w "%{http_code}" https://54.160.147.118/banking-platform/v1/
curl -s https://54.160.147.118/banking-platform/v1/api/banking/status
```

Share the HTTP code (expect 200) and the JSON from the second command. Then we can mark the deployment complete and add a short “next time” checklist.

---

## Quick reference after first deployment

- **App URL:** `https://54.160.147.118/banking-platform/v1/`  
- **Backend port:** 8001 (service: `banking-backend`)  
- **Existing app (unchanged):** `/nba-platform/v3/` on port 8000  

**Next-time deploy (after `git push`):**

1. `ssh aipenpaladm@54.160.147.118`
2. `cd /home/aipenpaladm/personalization-agent-banking && git pull origin main`
3. `source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart banking-backend`
4. `cd frontend && npm install && VITE_BASE_PATH=/banking-platform/v1 VITE_API_BASE_URL=/banking-platform/v1 npm run build`
5. `sudo cp -r dist/* /var/www/html/banking-platform/v1/ && sudo systemctl reload nginx` (run from `frontend` directory)

---

**To start:** Run **Step 1** first and share the outputs; we’ll proceed one step at a time from there.
