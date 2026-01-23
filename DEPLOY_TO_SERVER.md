# 🚀 Deployment Guide for 54.160.147.118

## 📋 **Pre-Deployment Checklist**

### **1. Check Server Disk Space**

SSH into server:
```bash
ssh aipenpaladm@54.160.147.118
```

Check available space:
```bash
# Overall disk usage
df -h

# Should show at least 2GB free
# Recommended: 5GB+ free
```

---

## 📦 **Space Requirements**

| Component | Size |
|-----------|------|
| Source Code | ~50 MB |
| Frontend (node_modules) | ~500 MB |
| Python Packages | ~300 MB |
| Data Files | ~100 MB |
| ChromaDB | ~200 MB |
| Buffer Space | ~850 MB |
| **TOTAL** | **~2 GB** |

---

## 🔧 **Deployment Options**

### **Option A: Standard Deployment (Recommended)**

#### **On Your Local Machine:**

1. **Clean up unnecessary files:**
```bash
# Remove development files
rm -rf frontend/node_modules/.cache
rm -rf chroma_db/*
rm -rf logs/*
rm -rf __pycache__
rm -rf streamlit_app
```

2. **Create deployment package:**
```bash
# Create archive without heavy folders
tar -czf personalization-agent.tar.gz \
  --exclude='frontend/node_modules' \
  --exclude='chroma_db' \
  --exclude='logs' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='streamlit_app' \
  .
```

3. **Upload to server:**
```bash
scp personalization-agent.tar.gz aipenpaladm@54.160.147.118:/home/aipenpaladm/
```

#### **On the Server:**

1. **Extract and setup:**
```bash
cd /home/aipenpaladm
mkdir personalization-agent
cd personalization-agent
tar -xzf ../personalization-agent.tar.gz

# Install dependencies
pip3 install -r requirements.txt
cd frontend && npm install && cd ..
```

2. **Initialize ChromaDB:**
```bash
python3 scripts/initialize_chromadb_academy.py
```

3. **Start services:**
```bash
# Backend
nohup python3 -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8000 &

# Frontend
cd frontend
nohup npm run build && npm run preview -- --host 0.0.0.0 --port 5173 &
```

---

### **Option B: Git Deployment (Cleaner)**

#### **On the Server:**

1. **Clone from GitHub:**
```bash
cd /home/aipenpaladm
git clone https://github.com/Revathi031187/NBA.git personalization-agent
cd personalization-agent
```

2. **Install dependencies:**
```bash
# Python
pip3 install -r requirements.txt

# Node.js
cd frontend
npm install
npm run build
cd ..
```

3. **Setup environment:**
```bash
# Create .env file
cat > .env << EOF
TOGETHER_API_KEY=your_key_here
DATA_DIR=data/preloaded/academy_sports
EOF
```

4. **Initialize data:**
```bash
python3 scripts/initialize_chromadb_academy.py
```

---

## 🌐 **Production Setup with Nginx**

### **1. Install Nginx (if not installed):**
```bash
sudo apt update
sudo apt install nginx
```

### **2. Create Nginx config:**
```bash
sudo nano /etc/nginx/sites-available/personalization-agent
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name 54.160.147.118;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **3. Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/personalization-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔐 **Security Setup**

### **1. Setup SSL (Optional but Recommended):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### **2. Firewall Configuration:**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw enable
```

---

## 🔄 **Process Management (Keep Services Running)**

### **Option A: Using systemd (Recommended)**

#### **Backend Service:**
```bash
sudo nano /etc/systemd/system/personalization-backend.service
```

Add:
```ini
[Unit]
Description=Personalization Agent Backend
After=network.target

[Service]
Type=simple
User=aipenpaladm
WorkingDirectory=/home/aipenpaladm/personalization-agent
ExecStart=/usr/bin/python3 -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### **Frontend Service:**
```bash
sudo nano /etc/systemd/system/personalization-frontend.service
```

Add:
```ini
[Unit]
Description=Personalization Agent Frontend
After=network.target

[Service]
Type=simple
User=aipenpaladm
WorkingDirectory=/home/aipenpaladm/personalization-agent/frontend
ExecStart=/usr/bin/npm run preview -- --host 0.0.0.0 --port 5173
Restart=always

[Install]
WantedBy=multi-user.target
```

#### **Enable and start services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable personalization-backend
sudo systemctl enable personalization-frontend
sudo systemctl start personalization-backend
sudo systemctl start personalization-frontend

# Check status
sudo systemctl status personalization-backend
sudo systemctl status personalization-frontend
```

---

### **Option B: Using PM2 (Node.js Process Manager)**

```bash
# Install PM2
sudo npm install -g pm2

# Start backend
pm2 start "python3 -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8000" --name backend

# Start frontend
cd frontend
pm2 start "npm run preview -- --host 0.0.0.0 --port 5173" --name frontend

# Save configuration
pm2 save
pm2 startup

# Monitor
pm2 monit
```

---

## 📊 **Monitoring Commands**

```bash
# Check disk space regularly
df -h

# Check memory usage
free -h

# Check running services
sudo systemctl status personalization-backend
sudo systemctl status personalization-frontend

# View logs
sudo journalctl -u personalization-backend -f
sudo journalctl -u personalization-frontend -f

# Or with PM2
pm2 logs
```

---

## 🔄 **Update Deployment**

When you need to update the code:

```bash
cd /home/aipenpaladm/personalization-agent
git pull origin master

# Update Python dependencies
pip3 install -r requirements.txt

# Update and rebuild frontend
cd frontend
npm install
npm run build
cd ..

# Restart services
sudo systemctl restart personalization-backend
sudo systemctl restart personalization-frontend

# Or with PM2
pm2 restart all
```

---

## 🧪 **Testing After Deployment**

1. **Check backend:**
```bash
curl http://localhost:8000/api/industries
```

2. **Check frontend:**
```bash
curl http://localhost:5173
```

3. **Access from browser:**
```
http://54.160.147.118
```

---

## ⚠️ **Troubleshooting**

### **If services won't start:**
```bash
# Check ports
sudo netstat -tulpn | grep -E '8000|5173'

# Kill processes if needed
sudo kill -9 $(sudo lsof -t -i:8000)
sudo kill -9 $(sudo lsof -t -i:5173)
```

### **If running out of space:**
```bash
# Clean npm cache
npm cache clean --force

# Clean pip cache
pip3 cache purge

# Remove old logs
sudo journalctl --vacuum-time=7d
```

---

## 📝 **Estimated Timeline**

- SSH and space check: 5 minutes
- File transfer/clone: 10 minutes
- Dependency installation: 15 minutes
- Service setup: 10 minutes
- Testing: 10 minutes

**Total: ~50 minutes**

---

## ✅ **Success Criteria**

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Nginx reverse proxy configured
- [ ] Services auto-restart on reboot
- [ ] Data loading works
- [ ] Agent A clustering works
- [ ] Agent B recommendations work
- [ ] Accessible from http://54.160.147.118

---

## 📞 **Need Help?**

Check logs:
```bash
# Backend logs
sudo journalctl -u personalization-backend -n 100

# Frontend logs
sudo journalctl -u personalization-frontend -n 100

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

