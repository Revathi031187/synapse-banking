@echo off
echo ========================================================================
echo  RESTART WITH SHORT, UNIQUE NAME EXPLANATIONS
echo ========================================================================
echo.
echo WHAT'S NEW:
echo   - Name explanations now SHORT (1 sentence)
echo   - Each explanation is UNIQUE to that segment
echo   - Segment NAME included in explanation
echo   - No more repetitive text
echo.
echo ========================================================================
echo  Killing existing backend...
echo ========================================================================
echo.

taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq FMB Backend*" >nul 2>&1
timeout /t 3 /nobreak >nul

echo ========================================================================
echo  Starting Backend (Port 8002)
echo ========================================================================
echo.

cd /d "%~dp0"
start "FMB Backend" cmd /k "python -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload"

echo Waiting for backend to initialize...
timeout /t 10 /nobreak >nul

echo.
echo ========================================================================
echo  ✓ BACKEND RESTARTED WITH SHORT EXPLANATIONS!
echo ========================================================================
echo.
echo   Backend: http://localhost:8002
echo   Frontend: http://localhost:5173 (if running)
echo.
echo WHAT TO CHECK:
echo   1. Go to Segments View
echo   2. Click "Show Segment Insights"
echo   3. Look at "Why This Name?" section
echo   4. Should now be SHORT (1 sentence)
echo   5. Each segment has UNIQUE explanation
echo   6. Segment name appears IN the explanation
echo.
echo EXAMPLES:
echo   - Elite Savers: "Elite Savers reflects top-tier wealth ($2.5M deposits)..."
echo   - Digital Natives: "Digital Natives identifies mobile-first customers with 87% digital usage..."
echo   - Traditional Members: "Traditional Members captures loyal customers with $4.1M deposits..."
echo.
pause
