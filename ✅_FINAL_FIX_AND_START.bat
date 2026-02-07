@echo off
cls
echo ================================================================
echo FINAL FIX: STARTING WITH ALL FIXES APPLIED
echo ================================================================
echo.
echo Fixes applied:
echo  1. Removed 'agent_a' parameter (backend code)
echo  2. Simple embedding function (no onnxruntime needed)
echo  3. Using Python 3.10 (stable version)
echo.
echo ================================================================
echo [1/3] Stopping old backend...
echo ================================================================
echo.

taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul
echo [OK] Old processes stopped

echo.
echo ================================================================
echo [2/3] Checking Python 3.10...
echo ================================================================
echo.

py -3.10 --version
if %ERRORLEVEL% NEQ 0 (
    echo [X] Python 3.10 not found via 'py' launcher
    echo.
    echo Please run: SWITCH_TO_PYTHON_310.bat
    pause
    exit /b 1
)

echo [OK] Python 3.10 found!

echo.
echo ================================================================
echo [3/3] Starting backend with all fixes...
echo ================================================================
echo.
echo Backend will start at: http://127.0.0.1:8002
echo.
echo Wait for "Application startup complete" message
echo Then run: TEST_API_DIRECT.bat
echo.
echo Starting...
timeout /t 2 /nobreak >nul
echo.

py -3.10 -m uvicorn api.main_unified_chromadb:app --port 8002 --reload
