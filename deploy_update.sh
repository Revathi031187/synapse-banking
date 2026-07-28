#!/bin/bash

###############################################################################
# Academy Sports Platform - Automated Deployment Script
# 
# This script pulls the latest code from GitHub and deploys it to production.
# Run this script on the server: ./deploy_update.sh
###############################################################################

set -e  # Exit on any error

echo "🚀 Starting deployment..."
echo "================================================"

# Configuration
PROJECT_DIR="/home/aipenpaladm/personalization-agent"
BACKEND_PORT=8002
SCREEN_SESSION="nba-backend"

cd "$PROJECT_DIR"

echo ""
echo "📥 Step 1: Pulling latest code from GitHub..."
echo "================================================"
git fetch origin
git pull origin main

echo ""
echo "🔧 Step 2: Installing/updating Python dependencies..."
echo "================================================"
source venv/bin/activate
pip install -r requirements.txt --quiet

echo ""
echo "🎨 Step 3: Rebuilding frontend..."
echo "================================================"
cd frontend
npm install --silent
npm run build

echo ""
echo "🔄 Step 4: Restarting backend..."
echo "================================================"
cd "$PROJECT_DIR"

# Kill existing backend process
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   Stopping existing backend on port $BACKEND_PORT..."
    fuser -k $BACKEND_PORT/tcp || true
    sleep 2
fi

# Kill existing screen session if it exists
if screen -list | grep -q "$SCREEN_SESSION"; then
    echo "   Stopping existing screen session '$SCREEN_SESSION'..."
    screen -S "$SCREEN_SESSION" -X quit || true
    sleep 1
fi

# Start new backend in screen session
echo "   Starting new backend in screen session '$SCREEN_SESSION'..."
screen -dmS "$SCREEN_SESSION" bash -c "cd $PROJECT_DIR && source venv/bin/activate && uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port $BACKEND_PORT --reload > logs/backend.log 2>&1"

# Wait for backend to start
echo "   Waiting for backend to start..."
sleep 3

# Verify backend is running
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   ✅ Backend is running on port $BACKEND_PORT"
else
    echo "   ❌ ERROR: Backend failed to start!"
    exit 1
fi

echo ""
echo "🌐 Step 5: Reloading nginx..."
echo "================================================"
sudo nginx -t
sudo nginx -s reload

echo ""
echo "✅ Deployment completed successfully!"
echo "================================================"
echo ""
echo "🎯 Application URLs:"
echo "   HTTPS: https://penpal.latentview.com/nba-platform/v3/academy/"
echo ""
echo "📊 Monitoring:"
echo "   Backend logs:  tail -f $PROJECT_DIR/logs/backend.log"
echo "   Nginx logs:    sudo tail -f /var/log/nginx/access.log"
echo "   Screen session: screen -r $SCREEN_SESSION"
echo ""
echo "🎉 Done!"
