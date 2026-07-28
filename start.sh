#!/bin/bash

echo "=========================================="
echo " NBA Personalization Platform"
echo "=========================================="
echo

# Check if ChromaDB is initialized
if [ ! -d "chroma_db" ]; then
    echo "[WARN] ChromaDB not initialized yet!"
    echo
    echo "Please run first-time setup:"
    echo "  python3.10 scripts/initialize_chromadb.py"
    echo
    exit 1
fi

echo "Starting NBA Personalization Platform..."
echo

# Start Backend
echo "[1/2] Starting Backend Server (Port 8002)..."
gnome-terminal --title="Backend Server" -- bash -c "python3.10 api/main_unified_chromadb.py; exec bash" 2>/dev/null || \
xterm -T "Backend Server" -e "python3.10 api/main_unified_chromadb.py" 2>/dev/null &

sleep 3

# Start Frontend
echo "[2/2] Starting Frontend Server (Port 5173)..."
gnome-terminal --title="Frontend Server" -- bash -c "cd frontend && npm run dev; exec bash" 2>/dev/null || \
xterm -T "Frontend Server" -e "cd frontend && npm run dev" 2>/dev/null &

sleep 3

echo
echo "=========================================="
echo " Application Started Successfully!"
echo "=========================================="
echo
echo "Backend:  http://localhost:8002"
echo "Frontend: http://localhost:5173"
echo
echo "Opening browser..."
sleep 2
xdg-open http://localhost:5173 2>/dev/null || open http://localhost:5173 2>/dev/null
echo
echo "To stop: Close both terminal windows"
echo "=========================================="

