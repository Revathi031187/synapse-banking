@echo off
cls
echo ================================================================
echo STARTING BACKEND WITH PYTHON 3.10
echo ================================================================
echo.

:: Kill existing backend
echo Stopping any existing backend...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo ----------------------------------------------------------------
echo.

:: Check if virtual environment exists
if exist "venv310\Scripts\activate.bat" (
    echo Using Python 3.10 virtual environment...
    call venv310\Scripts\activate.bat
    echo.
    python --version
    echo.
    echo Starting backend on port 8002...
    echo.
    python -m uvicorn api.main_unified_chromadb:app --port 8002 --reload
) else (
    echo [!] Virtual environment not found
    echo.
    echo Please run SWITCH_TO_PYTHON_310.bat first to create it!
    echo.
    pause
)
