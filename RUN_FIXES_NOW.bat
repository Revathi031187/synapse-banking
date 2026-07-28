@echo off
cls
echo ================================================================================
echo APPLY ALL FIXES - AUTOMATED
echo ================================================================================
echo.
echo This will fix ALL identified issues:
echo   1. Micro segment syntax error (already in code)
echo   2. Transaction volume inflation (303x)
echo   3. Out-of-range income values (149 customers)
echo   4. Inconsistent annual transaction values
echo.
echo Then automatically restart the backend.
echo.
echo SAFE: Automatic backup will be created!
echo.
pause

echo.
echo ================================================================================
echo STEP 1: FIXING DATA ISSUES
echo ================================================================================
echo.

python fix_all_data_issues.py 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ ERROR: Data fix failed!
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo STEP 2: RESTARTING BACKEND
echo ================================================================================
echo.
echo Stopping backend if running...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting backend...
echo.
start "Backend Server" cmd /k "cd /d %~dp0 && uvicorn api.main_unified_chromadb:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo ================================================================================
echo ✅ ALL FIXES APPLIED!
echo ================================================================================
echo.
echo Backend is starting in a new window...
echo.
echo NEXT STEPS:
echo   1. Wait 10 seconds for backend to fully start
echo   2. Open browser: http://localhost:5173/banking/agent-a
echo   3. Click "Load Data"
echo   4. Click "Run Segmentation"
echo   5. Click "View Micro-Segments" on any segment
echo.
echo Expected results:
echo   ✓ Micro segments load successfully (no syntax error)
echo   ✓ Transaction volumes are accurate (low values like 0.5-2.5)
echo   ✓ All data quality issues resolved
echo.
echo READ: 🔧_DATA_QUALITY_FIXES_COMPLETE.md for full details
echo.
pause
