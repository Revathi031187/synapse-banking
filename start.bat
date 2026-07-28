@echo off
echo ==========================================
echo  NBA Personalization Platform
echo ==========================================
echo.

REM Check if ChromaDB is initialized
if not exist "chroma_db\" (
    echo [WARN] ChromaDB not initialized yet!
    echo.
    echo Please run first-time setup:
    echo   py -3.10 scripts/initialize_chromadb.py
    echo.
    pause
    exit /b
)

echo Starting NBA Personalization Platform...
echo.
echo [1/2] Starting Backend Server (Port 8002)...
start "Backend Server" cmd /k "py -3.10 api/main_unified_chromadb.py"

timeout /t 5 /nobreak > nul

echo [2/2] Starting Frontend Server (Port 5173)...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak > nul

echo.
echo ==========================================
echo  Application Started Successfully!
echo ==========================================
echo.
echo Backend:  http://localhost:8002
echo Frontend: http://localhost:5173
echo.
echo Opening browser...
timeout /t 3 /nobreak > nul
start http://localhost:5173
echo.
echo To stop: Close both terminal windows
echo ==========================================

