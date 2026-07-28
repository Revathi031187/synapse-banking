# Fresh Clone Deployment - Clean Start
**Date**: January 13, 2026  
**Action**: Delete existing Academy code, fresh clone from GitHub  
**⚠️ ONLY affects /home/aipenpaladm/personalization-agent - Other projects safe!**

---

## ✅ Step-by-Step Fresh Clone

### Step 1: Kill ALL Backend Processes

```bash
# Kill any process on port 8002
sudo fuser -k 8002/tcp

# Double check it's gone
sudo lsof -i :8002
# Should show: (empty)

# Kill any uvicorn processes
pkill -f "uvicorn.*main_unified_chromadb"

# Kill any screen sessions
screen -ls | grep nba | cut -d. -f1 | awk '{print $1}' | xargs -r kill

# Verify nothing is running
ps aux | grep uvicorn | grep -v grep
# Should show: (empty)
```

---

### Step 2: Backup Current Directory (Safety)

```bash
cd /home/aipenpaladm

# Create backup with timestamp
BACKUP_NAME="personalization-agent-OLD-$(date +%Y%m%d-%H%M%S)"
mv personalization-agent "$BACKUP_NAME"

echo "✅ Backed up to: $BACKUP_NAME"
ls -la | grep personalization
```

---

### Step 3: Fresh Clone from GitHub

```bash
cd /home/aipenpaladm

# Clone fresh code
git clone https://github.com/Revathi031187/NBA.git personalization-agent

cd personalization-agent

# Verify you have latest commit
git log -1
# Should show: 89fbc61 - Academy Sports Platform - Complete Fixes

# Check what we got
ls -la
```

---

### Step 4: Setup Python Virtual Environment

```bash
cd /home/aipenpaladm/personalization-agent

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "fastapi|uvicorn|pandas|numpy"
```

---

### Step 5: Setup Frontend

```bash
cd /home/aipenpaladm/personalization-agent/frontend

# Install dependencies
npm install

# Build production frontend
npm run build

# Verify dist/ was created with NEW code
ls -la dist/
# Should see: index.html, assets/ folder

# Check the asset filenames (should be NEW hashes)
ls -la dist/assets/
# Should see files like: index-FOzfMhnp.js (NEW hash!)

cd ..
```

---

### Step 6: Create Logs Directory

```bash
cd /home/aipenpaladm/personalization-agent

# Create logs directory if it doesn't exist
mkdir -p logs

# Set permissions
chmod 755 logs
```

---

### Step 7: Start Backend (Clean)

```bash
cd /home/aipenpaladm/personalization-agent

# Make sure virtual environment is activated
source venv/bin/activate

# Start backend in screen session
screen -dmS nba-backend bash -c 'cd /home/aipenpaladm/personalization-agent && source venv/bin/activate && uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload > logs/backend.log 2>&1'

# Wait for startup
sleep 5

# Check if it's running
sudo lsof -i :8002
# Should show python process listening on 8002

# Test API
curl http://localhost:8002/api/health
# Should return some JSON (not "Not Found")

# Check datasets endpoint
curl http://localhost:8002/api/academy/datasets
# Should return dataset info

# View logs
tail -20 logs/backend.log
# Should see "Application startup complete" with TODAY's date (2026-01-13)
```

---

### Step 8: Verify Screen Session

```bash
# List screen sessions
screen -ls
# Should show: nba-backend

# Attach to see logs (optional)
screen -r nba-backend
# Press Ctrl+A then D to detach

# If screen session died, check logs:
tail -50 logs/backend.log
# Look for errors
```

---

### Step 9: Update Nginx Configuration (If Needed)

```bash
# Check current nginx config
sudo cat /etc/nginx/sites-available/personalization | grep -A 15 "location /nba-platform-v2"

# The paths should point to:
# alias /home/aipenpaladm/personalization-agent/frontend/dist/;

# If paths are wrong, edit:
sudo nano /etc/nginx/sites-available/personalization

# Find the nba-platform-v2 section and ensure:
# location /nba-platform-v2/ {
#     alias /home/aipenpaladm/personalization-agent/frontend/dist/;
#     index index.html;
#     try_files $uri $uri/ /nba-platform-v2/index.html;
# }

# Test nginx config
sudo nginx -t

# Reload nginx
sudo nginx -s reload
```

---

### Step 10: Fix vite.svg 404 Error

The `/vite.svg:1 Failed to load resource: 404` error is because vite.svg is referenced but missing.

```bash
cd /home/aipenpaladm/personalization-agent/frontend

# Check if vite.svg exists in public folder
ls -la public/

# If missing, create a dummy one or remove reference from index.html
# Option 1: Remove the link from index.html
nano index.html
# Find and delete or comment out: <link rel="icon" ... href="/vite.svg" />

# Option 2: Copy a favicon
cp public/logo.png public/vite.svg 2>/dev/null || true

# Rebuild if you made changes
npm run build

# Reload nginx
sudo nginx -s reload
```

---

### Step 11: Clear ALL Caches & Test

```bash
# On server - verify everything is working
curl -I http://localhost:8002/api/health
curl -I http://localhost/nba-platform-v2/
curl http://localhost:8002/api/academy/datasets | head -20

# In Browser:
# 1. Open Incognito/Private window (bypasses all caches)
# 2. Go to: https://penpal.latentview.com/nba-platform-v2/academy/
# 3. Check:
#    - No console errors
#    - Agent A page shows new design
#    - No "Switch Industry" button
#    - "Visual Dashboard" shows "⚠️ Run Agent A first"
```

---

## 🧪 Complete Test Sequence

### Test 1: Backend API
```bash
# Health check
curl http://localhost:8002/api/health

# Datasets
curl http://localhost:8002/api/academy/datasets

# Agent A results (should be 404 initially)
curl http://localhost:8002/api/academy/agent_a/results
# Expected: {"detail":"No Agent A results available..."}
```

### Test 2: Frontend
```bash
# Check index.html is served
curl -I http://localhost/nba-platform-v2/

# Check assets are served
curl -I http://localhost/nba-platform-v2/assets/index-FOzfMhnp.js
```

### Test 3: Full Flow in Browser
1. ✅ Go to: https://penpal.latentview.com/nba-platform-v2/academy/
2. ✅ Page loads without errors
3. ✅ Academy Dashboard shows correctly
4. ✅ Click "Agent A: Customer Segmentation"
5. ✅ Empty state shows: "Ready to Discover Customer Segments"
6. ✅ Click "Run K-Prototypes Clustering"
7. ✅ Wait 30-60 seconds
8. ✅ Segments appear
9. ✅ Go to "Macro Dashboard"
10. ✅ Segments visible
11. ✅ Click a customer
12. ✅ Product recommendations show
13. ✅ All 3 products match customer's category!

---

## 📋 Quick Command Summary (Copy-Paste All)

```bash
# 1. Kill everything
sudo fuser -k 8002/tcp
pkill -f "uvicorn.*main_unified_chromadb"
screen -ls | grep nba | cut -d. -f1 | awk '{print $1}' | xargs -r kill

# 2. Backup & delete old
cd /home/aipenpaladm
mv personalization-agent "personalization-agent-OLD-$(date +%Y%m%d-%H%M%S)"

# 3. Fresh clone
git clone https://github.com/Revathi031187/NBA.git personalization-agent
cd personalization-agent
git log -1  # Verify: 89fbc61

# 4. Setup Python
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Build frontend
cd frontend
npm install
npm run build
ls -la dist/
cd ..

# 6. Create logs directory
mkdir -p logs

# 7. Start backend
screen -dmS nba-backend bash -c 'cd /home/aipenpaladm/personalization-agent && source venv/bin/activate && uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload > logs/backend.log 2>&1'

# 8. Wait and verify
sleep 5
sudo lsof -i :8002
curl http://localhost:8002/api/academy/datasets
tail -20 logs/backend.log

# 9. Reload nginx
sudo nginx -s reload

# 10. Test in browser (Incognito mode)
# https://penpal.latentview.com/nba-platform-v2/academy/
```

---

## ✅ Success Checklist

- [ ] Old processes killed
- [ ] Old directory backed up
- [ ] Fresh code cloned (commit 89fbc61)
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Frontend built (new dist/ with new hashes)
- [ ] Backend started (port 8002 listening)
- [ ] API health check passes
- [ ] Logs show "Application startup complete" (today's date)
- [ ] Nginx reloaded
- [ ] Browser shows new code (test in Incognito)
- [ ] Agent A runs successfully
- [ ] Product recommendations are category-accurate

---

## 🎉 This Will Give You

- ✅ Clean codebase (no conflicts)
- ✅ Latest code from GitHub (89fbc61)
- ✅ Fresh virtual environment
- ✅ New frontend build
- ✅ Clean backend process
- ✅ No lingering processes
- ✅ All fixes working

---

**Run the command summary and you'll have a fresh, working deployment!** 🚀
