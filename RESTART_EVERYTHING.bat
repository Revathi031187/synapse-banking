@echo off
echo ================================================================================
echo RESTARTING BANKING AGENT B WITH ALL FIXES
echo ================================================================================
echo.

echo [1/3] Checking if processes are running...
tasklist /FI "IMAGENAME eq python.exe" | find /I "python.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo    WARNING: Python is running. Please stop the backend manually ^(Ctrl+C^)
    pause
)

echo.
echo [2/3] Starting Backend...
echo    Starting API on http://localhost:8002
start "Banking API" cmd /k "cd /d %~dp0 && py -3.10 api/main_unified_chromadb.py"

timeout /t 5 /nobreak >nul

echo.
echo [3/3] Starting Frontend...
echo    Starting UI on http://localhost:5173
start "Banking Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ================================================================================
echo STARTUP COMPLETE
echo ================================================================================
echo.
echo Backend API:  http://localhost:8002
echo Frontend UI:  http://localhost:5173/banking/agent-b
echo.
echo TROUBLESHOOTING:
echo   1. If Agent B shows blank screen, press Ctrl+Shift+R in browser
echo   2. If micro-segments show 404, click the segment again
echo   3. Check Console ^(F12^) for any red errors
echo.
echo Press any key to open Agent B in browser...
pause >nul

start http://localhost:5173/banking/agent-b

echo.
echo All services started! Check the terminal windows for logs.
echo.
pause
