@echo off
echo ====================================================================
echo RESTARTING BACKEND WITH ALL 7 FIXES
echo ====================================================================
echo.
echo Fixes included:
echo   1. Python 3.10 (not 3.14 alpha)
echo   2. onnxruntime mocked
echo   3. agent_a parameter removed
echo   4. DataFrame serialization fixed
echo   5. Test script JSON parsing fixed
echo   6. Column name mismatch fixed (cluster)
echo   7. product_id added to transactions
echo.
echo [1/2] Killing existing backend processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM py.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/2] Starting backend with Python 3.10...
echo.
echo ====================================================================
echo BACKEND STARTING - Wait for "Application startup complete"
echo ====================================================================
echo.

py -3.10 -m uvicorn api.main_unified_chromadb:app --reload --port 8002

echo.
echo ====================================================================
echo Backend stopped
echo ====================================================================
pause
