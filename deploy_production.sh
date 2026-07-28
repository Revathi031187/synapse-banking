#!/bin/bash
# Production Deployment Script for NBA Personalization Platform
# Deploys on port 8002 without affecting other apps

echo "=========================================="
echo " NBA Platform - Production Deployment"
echo "=========================================="

# Step 1: Build Frontend
echo "[1/4] Building frontend..."
cd frontend
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi
cd ..
echo "✅ Frontend built successfully"

# Step 2: Stop existing processes
echo "[2/4] Stopping existing processes..."
pkill -f "uvicorn.*main_unified_chromadb"
sleep 2

# Step 3: Create systemd service
echo "[3/4] Creating systemd service..."
sudo tee /etc/systemd/system/nba-platform.service > /dev/null <<EOF
[Unit]
Description=NBA Personalization Platform API
After=network.target

[Service]
Type=simple
User=aipenpaladm
WorkingDirectory=/home/aipenpaladm/personalization-agent
Environment="PATH=/home/aipenpaladm/personalization-agent/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/aipenpaladm/personalization-agent/venv/bin/python api/main_unified_chromadb.py
Restart=always
RestartSec=10
StandardOutput=append:/home/aipenpaladm/personalization-agent/logs/nba-platform.log
StandardError=append:/home/aipenpaladm/personalization-agent/logs/nba-platform-error.log

[Install]
WantedBy=multi-user.target
EOF

# Step 4: Start service
echo "[4/4] Starting NBA Platform service..."
sudo systemctl daemon-reload
sudo systemctl enable nba-platform
sudo systemctl start nba-platform

sleep 3

# Check status
if sudo systemctl is-active --quiet nba-platform; then
    echo ""
    echo "=========================================="
    echo " ✅ DEPLOYMENT SUCCESSFUL!"
    echo "=========================================="
    echo ""
    echo "Application URL: http://54.160.147.118:8002"
    echo ""
    echo "Useful Commands:"
    echo "  sudo systemctl status nba-platform   - Check status"
    echo "  sudo systemctl restart nba-platform  - Restart app"
    echo "  sudo systemctl stop nba-platform     - Stop app"
    echo "  tail -f logs/nba-platform.log        - View logs"
    echo ""
else
    echo "❌ Deployment failed! Check logs:"
    echo "  sudo journalctl -u nba-platform -n 50"
fi

