@echo off
cls
echo ============================================================
echo RESTART BACKEND WITH FIXED MICRO SEGMENT NAMES
echo ============================================================
echo.
echo Fixed: Micro segments now have unique, descriptive names
echo.
echo Examples:
echo   - Ultra High-Value Multi-Bankers (Platinum)
echo   - Frequent Multi-Channel Users (Gold)
echo   - High-Earning Tech Professionals (Silver)
echo   - Established High-Net-Worth Legacy (Bronze)
echo.
echo Stopping old backend...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting backend with fixes...
start "Backend Server" cmd /k "cd /d %~dp0 && uvicorn api.main_unified_chromadb:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo BACKEND RESTARTED!
echo ============================================================
echo.
echo NEXT STEPS:
echo   1. Go to: http://localhost:5173/banking/agent-a
echo   2. Click "Load Data"
echo   3. Click "Run Segmentation"  
echo   4. Click "View Micro-Segments" on any macro segment
echo.
echo You should now see 4 UNIQUE names per macro segment!
echo.
pause
