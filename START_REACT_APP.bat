@echo off
echo ========================================
echo Starting Academy Sports React Application
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Installing frontend dependencies...
cd frontend
if not exist "node_modules" (
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

echo.
echo [2/4] Installing backend dependencies...
cd ..
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some backend dependencies may not have installed correctly
)

echo.
echo [3/4] Starting FastAPI Backend on port 8000...
start "FastAPI Backend (Port 8000)" cmd /k "py -3.10 -m uvicorn api.main_unified_chromadb:app --reload --port 8000"
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Starting React Frontend on port 5173...
cd frontend
start "React Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo ✅ Application Started Successfully!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to open the application in your browser...
pause >nul
start http://localhost:5173

echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the application.
pause

