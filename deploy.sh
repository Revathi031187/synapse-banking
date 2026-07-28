#!/bin/bash
# Quick Deployment Script
# Run this on the server (54.160.147.118) after uploading

set -e  # Exit on error

echo "========================================="
echo "🚀 Personalization Agent Deployment"
echo "========================================="
echo ""

# 1. Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip nodejs npm nginx

# 2. Setup project directory
PROJECT_DIR="/home/aipenpaladm/personalization-agent"
echo "📁 Setting up project in: $PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# 3. Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# 4. Install Node.js dependencies and build frontend
echo "⚛️ Installing and building frontend..."
cd frontend
npm install
npm run build
cd ..

# 5. Setup environment
echo "🔧 Setting up environment..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
TOGETHER_API_KEY=your_key_here
DATA_DIR=data/preloaded/academy_sports
EOF
    echo "⚠️ Don't forget to edit .env with your actual API key!"
fi

# 6. Initialize ChromaDB
echo "💾 Initializing ChromaDB..."
python3 scripts/initialize_chromadb_academy.py || echo "⚠️ ChromaDB initialization optional, skipping..."

# 7. Setup systemd services
echo "🔄 Setting up systemd services..."

# Backend service
sudo tee /etc/systemd/system/personalization-backend.service > /dev/null << EOF
[Unit]
Description=Personalization Agent Backend
After=network.target

[Service]
Type=simple
User=aipenpaladm
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
sudo tee /etc/systemd/system/personalization-frontend.service > /dev/null << EOF
[Unit]
Description=Personalization Agent Frontend
After=network.target

[Service]
Type=simple
User=aipenpaladm
WorkingDirectory=$PROJECT_DIR/frontend
ExecStart=/usr/bin/npm run preview -- --host 0.0.0.0 --port 5173
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 8. Setup Nginx reverse proxy
echo "🌐 Setting up Nginx..."
sudo tee /etc/nginx/sites-available/personalization-agent > /dev/null << 'EOF'
server {
    listen 80;
    server_name 54.160.147.118;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/personalization-agent /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 9. Start services
echo "▶️ Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable personalization-backend personalization-frontend
sudo systemctl start personalization-backend personalization-frontend

# 10. Check status
echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "📊 Service Status:"
sudo systemctl status personalization-backend --no-pager -l
echo ""
sudo systemctl status personalization-frontend --no-pager -l
echo ""
echo "🌐 Access your application at:"
echo "   http://54.160.147.118"
echo ""
echo "📝 Useful commands:"
echo "   - View backend logs: sudo journalctl -u personalization-backend -f"
echo "   - View frontend logs: sudo journalctl -u personalization-frontend -f"
echo "   - Restart backend: sudo systemctl restart personalization-backend"
echo "   - Restart frontend: sudo systemctl restart personalization-frontend"
echo ""

