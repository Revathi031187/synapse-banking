@echo off
echo ================================================================================
echo NBA PLATFORM - PRODUCTION SETUP
echo ================================================================================
echo.

echo [1/5] Installing Python dependencies...
py -3.10 -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo [2/5] Creating necessary directories...
if not exist "chroma_db" mkdir chroma_db
if not exist "logs" mkdir logs
if not exist "data\banking_nba" mkdir data\banking_nba
if not exist "data\retail_nba" mkdir data\retail_nba
echo ✓ Directories created
echo.

echo [3/5] Checking for datasets...
if not exist "data\banking_nba\customers.csv" (
    echo WARNING: Banking dataset not found
    echo Please ensure data files are in data\banking_nba\
)
if not exist "data\retail_nba\customers.csv" (
    echo WARNING: Retail dataset not found
    echo Please ensure data files are in data\retail_nba\
)
echo.

echo [4/5] Initializing ChromaDB with pre-computed data...
echo This will take a few minutes...
py -3.10 scripts\initialize_chromadb.py
if errorlevel 1 (
    echo ERROR: ChromaDB initialization failed
    pause
    exit /b 1
)
echo ✓ ChromaDB initialized
echo.

echo [5/5] Setup complete!
echo.
echo ================================================================================
echo NEXT STEPS:
echo ================================================================================
echo 1. Start the backend: start_chromadb_backend.bat
echo 2. Start the frontend: cd frontend ^&^& npm run dev
echo 3. Access the app: http://localhost:5173
echo ================================================================================
echo.
pause

