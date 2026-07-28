@echo off
cls
echo ================================================================
echo QUICK START WITH PYTHON 3.10 (Using py launcher)
echo ================================================================
echo.
echo This uses the Windows Python Launcher to select Python 3.10
echo.

:: Kill existing backend
echo Stopping any existing backend...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Testing Python 3.10...
py -3.10 --version

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ Python 3.10 found!
    echo.
    echo Installing/upgrading packages...
    py -3.10 -m pip install --upgrade pip
    py -3.10 -m pip install -r requirements.txt
    echo.
    echo ================================================================
    echo STARTING BACKEND WITH PYTHON 3.10
    echo ================================================================
    echo.
    py -3.10 -m uvicorn api.main_unified_chromadb:app --port 8002 --reload
) else (
    echo.
    echo [X] Python 3.10 not found via py launcher
    echo.
    echo Try running: SWITCH_TO_PYTHON_310.bat
    echo.
    pause
)
