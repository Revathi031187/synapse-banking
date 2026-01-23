@echo off
echo ========================================
echo Restarting Application with Fixed Ports
echo ========================================
echo.

echo Stopping any running instances...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Backend on Port 8000...
start "Backend (Port 8000)" cmd /k "py -3.10 -m uvicorn api.main_unified_chromadb:app --reload --port 8000"
timeout /t 5 /nobreak >nul

echo.
echo Starting Frontend on Port 5173...
cd frontend
start "Frontend (Port 5173)" cmd /k "npm run dev"

echo.
echo ========================================
echo ✅ Application Restarted!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
timeout /t 3 /nobreak >nul
start http://localhost:5173

pause

