@echo off
echo ==========================================
echo  NBA Platform - First Time Setup
echo ==========================================
echo.

echo [1/3] Installing Python dependencies...
py -3.10 -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Installing Frontend dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Frontend dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo [3/3] Initializing ChromaDB database...
py -3.10 scripts/initialize_chromadb.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to initialize ChromaDB
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  Setup Complete!
echo ==========================================
echo.
echo To start the application, run:
echo   start.bat
echo.
pause

