@echo off
cls
echo ================================================================
echo RESTARTING BACKEND WITH FIX
echo ================================================================
echo.
echo Fixed Issue: Removed invalid 'agent_a' parameter from Agent B init
echo.
echo Killing old backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM uvicorn.exe 2>nul

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo.
echo Starting backend on port 8002...
echo.
echo [!] Backend will start in a NEW WINDOW
echo [!] Keep that window open
echo [!] After backend starts, run: TEST_API_DIRECT.bat
echo.
pause

start "Banking Backend" cmd /k "python -m uvicorn api.main_unified_chromadb:app --port 8002 --reload"

echo.
echo ================================================================
echo Backend starting in new window...
echo ================================================================
echo.
echo Wait 5-10 seconds for backend to fully start, then run:
echo.
echo    TEST_API_DIRECT.bat
echo.
pause
