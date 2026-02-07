@echo off
echo ========================================
echo Starting Banking Personalization Agent
echo ========================================
echo.
echo This will open 2 terminals:
echo 1. Backend API (port 8002)
echo 2. Frontend UI (port 5173)
echo.
echo Press any key to start...
pause

REM Start backend in new window
echo Starting Backend Server...
start "Banking Backend (Port 8002)" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python api/main_unified_chromadb.py"

REM Wait a bit for backend to start
timeout /t 5 /nobreak

REM Start frontend in new window
echo Starting Frontend Server...
start "Banking Frontend (Port 5173)" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================
echo BOTH SERVERS STARTING!
echo ========================================
echo.
echo Backend: http://localhost:8002
echo Frontend: http://localhost:5173
echo.
echo Wait 10 seconds, then open:
echo   http://localhost:5173/banking/agent-a
echo.
echo Close this window after both servers start.
echo ========================================
timeout /t 15

REM Open browser
start http://localhost:5173/banking/agent-a

exit
