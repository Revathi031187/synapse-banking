# Quick Deployment Steps
**Server**: penpal.latentview.com (54.160.147.118)  
**Project**: Academy Sports Platform ONLY  
**⚠️ DO NOT touch other projects!**

---

## 🚀 Quick Steps (Copy & Paste)

### 1. SSH into Server
```bash
ssh aipenpaladm@54.160.147.118
```

### 2. Navigate & Backup
```bash
cd /home/aipenpaladm/personalization-agent
pwd  # Verify correct directory

# Create backup
BACKUP_DIR="/home/aipenpaladm/backups/personalization-agent-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r agents/ api/ frontend/dist/ $BACKUP_DIR/ 2>/dev/null || true
echo "✅ Backup: $BACKUP_DIR"
```

### 3. Pull Latest Code
```bash
git stash
git pull origin master
# Should show: Updating fcdf1a6..89fbc61
```

### 4. Rebuild Frontend
```bash
cd frontend
npm install
npm run build
ls -la dist/  # Verify dist/ exists
cd ..
```

### 5. Restart Backend
```bash
# Option A: Using systemd (if available)
sudo systemctl restart nba-backend
sudo systemctl status nba-backend

# Option B: Manual
sudo fuser -k 8002/tcp
nohup ./venv/bin/uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload > logs/backend.log 2>&1 &
tail -f logs/backend.log  # Ctrl+C to stop
```

### 6. Reload Nginx
```bash
sudo nginx -t
sudo nginx -s reload
sudo systemctl status nginx
```

### 7. Verify
```bash
# Test API
curl http://localhost:8002/api/health
curl http://localhost:8002/api/academy/datasets

# Test frontend
curl -I http://localhost/nba-platform-v2/
```

### 8. Test in Browser
Open: https://penpal.latentview.com/nba-platform-v2/academy/

**Check**:
- [ ] Page loads
- [ ] Agent A page shows empty state
- [ ] Run Agent A → Generates segments
- [ ] Product recommendations match categories ✅
- [ ] Each customer gets different products ✅

---

## ⚠️ If Something Fails

```bash
# Check logs
tail -f /home/aipenpaladm/personalization-agent/logs/backend.log
sudo tail -f /var/log/nginx/error.log

# Restart everything
sudo systemctl restart nba-backend nginx

# Rollback if needed
cd /home/aipenpaladm/backups/
# Copy files back from most recent backup
```

---

**See `DEPLOY_TO_SERVER_FINAL.md` for detailed guide!**
