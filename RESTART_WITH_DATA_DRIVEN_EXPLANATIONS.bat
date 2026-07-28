@echo off
echo ========================================================================
echo  RESTART WITH DATA-DRIVEN NAME EXPLANATIONS
echo ========================================================================
echo.
echo NEW FEATURES:
echo   1. Name explanations now use ACTUAL customer data
echo   2. Explains WHY each segment earned its specific name
echo   3. Shows real metrics: deposits, transactions, digital %, products
echo   4. Compares to other segments (percentile rankings)
echo   5. Tells a story about each segment's unique characteristics
echo.
echo ========================================================================
echo  STEP 1: Kill existing backend
echo ========================================================================
echo.

taskkill /F /IM uvicorn.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo ========================================================================
echo  STEP 2: Start Backend (Port 8002)
echo ========================================================================
echo.

cd /d "%~dp0"
start "FMB Backend" cmd /k "python -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload"

echo Waiting for backend to start...
timeout /t 10 /nobreak >nul

echo.
echo ========================================================================
echo  ✓ BACKEND RESTARTED!
echo ========================================================================
echo.
echo   Backend: http://localhost:8002
echo   Frontend: http://localhost:5173 (if running)
echo.
echo WHAT TO TEST:
echo   1. Go to Segments View
echo   2. Click "Show Segment Insights" on ANY macro segment
echo   3. Look for "Why This Name?" section
echo   4. You'll see DATA-DRIVEN explanations like:
echo      - "Exceptional wealth: $3M average deposits (top 5%%)"
echo      - "High engagement: 245 monthly transactions"
echo      - "Tech-forward: 87%% digital adoption"
echo.
echo   5. Expand micro segments and check their explanations too!
echo.
pause
