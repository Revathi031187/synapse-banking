# Fix Deployment Now - Clean Install
**Issue**: Local changes blocking git pull, backend service not found  
**Solution**: Stash local changes, pull fresh code, find & restart backend properly

---

## 🔧 Step 1: Fix Git Pull (Stash Local Changes)

```bash
cd /home/aipenpaladm/personalization-agent

# Stash local changes (saves them but clears working directory)
git stash

# Now pull latest code
git pull origin master

# Should see:
# Updating fcdf1a6..89fbc61
# Fast-forward
# 13 files changed, 2272 insertions(+), 653 deletions(-)

# Verify you have latest code
git log -1
# Should show: 89fbc61 - Academy Sports Platform - Complete Fixes
```

---

## 🔧 Step 2: Rebuild Frontend (With NEW Code)

```bash
cd /home/aipenpaladm/personalization-agent/frontend

# Install any new dependencies
npm install

# Build production frontend
npm run build

# Verify build completed
ls -la dist/
# Should see: index.html, assets/ with NEW file names

cd ..
```

---

## 🔧 Step 3: Find & Kill Old Backend Process

The backend is NOT running as a systemd service. Let's find how it's actually running:

```bash
# Check if backend is running on port 8002
sudo lsof -i :8002

# You should see something like:
# COMMAND   PID         USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# python  12345  aipenpaladm    3u  IPv4 123456      0t0  TCP *:8002 (LISTEN)

# Note the PID (process ID), then kill it:
sudo kill -9 <PID>

# OR use fuser to kill directly:
sudo fuser -k 8002/tcp

# OR check if it's running with pm2:
pm2 list

# OR check if it's running with nohup:
ps aux | grep uvicorn

# OR check for screen sessions:
screen -ls
```

---

## 🔧 Step 4: Start Backend with NEW Code

```bash
cd /home/aipenpaladm/personalization-agent

# Make sure virtual environment is activated
source venv/bin/activate

# Start backend (choose ONE method that works):

# Method 1: Direct uvicorn (recommended for testing)
./venv/bin/uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload

# OR Method 2: Background with nohup
nohup ./venv/bin/uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload > logs/backend.log 2>&1 &

# OR Method 3: Background with screen (recommended)
screen -dmS nba-backend ./venv/bin/uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload

# Verify it's running
curl http://localhost:8002/api/health
# Should return: {"status":"healthy"} or similar

# Check if port 8002 is listening
sudo lsof -i :8002
```

---

## 🔧 Step 5: Clear Browser Cache & Test

```bash
# On the server, verify API works:
curl http://localhost:8002/api/academy/datasets

# Verify frontend is served:
curl -I http://localhost/nba-platform-v2/

# If both work, the issue is browser cache!
```

**In Browser**:
1. Open: https://penpal.latentview.com/nba-platform-v2/academy/
2. **Hard Refresh**: Ctrl + Shift + R (or Ctrl + F5)
3. If still old code, **Clear Cache**:
   - Chrome: Ctrl + Shift + Delete → Clear cache
   - Or open in **Incognito/Private window**

---

## 🔧 Step 6: Verify New Code is Running

### Test in Browser:
1. Go to: https://penpal.latentview.com/nba-platform-v2/academy/
2. **Check**:
   - ✅ Agent A page shows "Ready to Discover Customer Segments" (new design)
   - ✅ No "Switch Industry" button in header
   - ✅ "Visual Dashboard" card shows "⚠️ Run Agent A first"

3. **Run Agent A**:
   - Click "Run K-Prototypes Clustering"
   - Wait 30-60 seconds
   - Segments should appear

4. **Test Recommendations**:
   - Go to Macro Dashboard
   - Click a customer with "Sleeping Bags + Airbeds" preference
   - **Expected**: All 3 products from "Sleeping Bags + Airbeds" category
   - **NOT Expected**: Coolers or Backpacks

### Check Backend Logs:
```bash
# If using nohup:
tail -f /home/aipenpaladm/personalization-agent/logs/backend.log

# If using screen:
screen -r nba-backend
# Press Ctrl+A then D to detach

# Look for:
# ✅ "Application startup complete"
# ✅ No "KeyError: 'main_category'" errors
# ✅ "ENHANCED Scoring breakdown" in logs
```

---

## 🎯 Complete Command Sequence (Copy-Paste)

```bash
# 1. Fix git pull
cd /home/aipenpaladm/personalization-agent
git stash
git pull origin master
git log -1  # Verify: 89fbc61

# 2. Rebuild frontend with NEW code
cd frontend
npm install
npm run build
ls -la dist/
cd ..

# 3. Kill old backend
sudo fuser -k 8002/tcp

# 4. Start new backend in screen
screen -dmS nba-backend bash -c 'source venv/bin/activate && uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload'

# 5. Verify backend is running
sleep 2
curl http://localhost:8002/api/health

# 6. Check what's running
sudo lsof -i :8002
screen -ls

# 7. Test in browser (hard refresh!)
# https://penpal.latentview.com/nba-platform-v2/academy/
```

---

## 🐛 If Still Showing Old Code

### Issue: CDN/Load Balancer Caching

The server might be behind a CDN or Load Balancer that's caching the old code.

**Check Nginx Config**:
```bash
sudo cat /etc/nginx/sites-available/personalization | grep -A 10 "location /nba-platform-v2"
```

**If you see caching headers, disable them temporarily**:
```bash
sudo nano /etc/nginx/sites-available/personalization

# Find the /nba-platform-v2/ location block and add:
location /nba-platform-v2/ {
    alias /home/aipenpaladm/personalization-agent/frontend/dist/;
    index index.html;
    try_files $uri $uri/ /nba-platform-v2/index.html;
    
    # ADD THESE LINES:
    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
    expires off;
}

# Save (Ctrl+X, Y, Enter)

# Test and reload
sudo nginx -t
sudo nginx -s reload
```

---

## 🗑️ Nuclear Option: Erase & Re-clone (If Nothing Else Works)

**ONLY if above steps don't work**:

```bash
# Backup current directory
cd /home/aipenpaladm
mv personalization-agent personalization-agent-backup-$(date +%Y%m%d-%H%M%S)

# Fresh clone
git clone https://github.com/Revathi031187/NBA.git personalization-agent
cd personalization-agent

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Start backend
screen -dmS nba-backend bash -c 'source venv/bin/activate && uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload'

# Reload nginx
sudo nginx -s reload
```

---

## ✅ Success Checklist

- [ ] Git pull successful (shows 89fbc61)
- [ ] Frontend rebuilt (new dist/ with different file hashes)
- [ ] Old backend killed (port 8002 free)
- [ ] New backend started (listening on 8002)
- [ ] Backend health check passes
- [ ] Browser hard refresh done
- [ ] New UI visible (new empty state design)
- [ ] Agent A runs successfully
- [ ] Product recommendations are category-accurate

---

**Follow these steps in order and the new code will be live!** 🚀
