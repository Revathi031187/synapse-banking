@echo off
chcp 65001 >nul 2>&1

echo ================================================================
echo RESTARTING BACKEND WITH DATAFRAME FIX
echo ================================================================
echo.
echo Fix applied: Convert DataFrame to dict before storing
echo.
echo ================================================================
echo [1/2] Stopping old backend...
================================================================

taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Stopped

echo.
echo ================================================================
echo [2/2] Starting backend with Python 3.10...
echo ================================================================
echo.
echo Backend: http://127.0.0.1:8002
echo.

py -3.10 -m uvicorn api.main_unified_chromadb:app --reload --host 0.0.0.0 --port 8002

pause
