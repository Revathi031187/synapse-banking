#!/bin/bash

echo "=========================================="
echo " NBA Platform - First Time Setup"
echo "=========================================="
echo

echo "[1/3] Installing Python dependencies..."
python3.10 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies"
    exit 1
fi

echo
echo "[2/3] Installing Frontend dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Frontend dependencies"
    exit 1
fi
cd ..

echo
echo "[3/3] Initializing ChromaDB database..."
python3.10 scripts/initialize_chromadb.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to initialize ChromaDB"
    exit 1
fi

echo
echo "=========================================="
echo " Setup Complete!"
echo "=========================================="
echo
echo "To start the application, run:"
echo "  chmod +x start.sh"
echo "  ./start.sh"
echo

