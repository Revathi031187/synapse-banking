@echo off
cls
echo ================================================================
echo   BANKING AGENT B - START WITH PYTHON 3.10
echo ================================================================
echo.
echo This will:
echo  1. Use your existing Python 3.10 (stable)
echo  2. Install packages if needed
echo  3. Start the backend
echo.
echo Press any key to continue, or Ctrl+C to cancel...
pause >nul
cls

echo ================================================================
echo [1/4] Checking Python 3.10...
echo ================================================================
echo.

py -3.10 --version
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Python 3.10 not found via 'py' launcher
    echo.
    echo Trying to find it manually...
    if exist "C:\Python310\python.exe" (
        echo [FOUND] C:\Python310\python.exe
        set PY_CMD=C:\Python310\python.exe
    ) else if exist "C:\Program Files\Python310\python.exe" (
        echo [FOUND] C:\Program Files\Python310\python.exe
        set PY_CMD="C:\Program Files\Python310\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
        echo [FOUND] %LOCALAPPDATA%\Programs\Python\Python310\python.exe
        set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    ) else (
        echo.
        echo [X] Could not find Python 3.10 anywhere!
        echo.
        echo Please check where Python 3.10 is installed and run:
        echo    USE_PYTHON_310_DIRECTLY.bat
        echo.
        pause
        exit /b 1
    )
) else (
    echo [OK] Python 3.10 found!
    set PY_CMD=py -3.10
)

echo.
echo ================================================================
echo [2/4] Stopping old backend...
echo ================================================================
echo.

taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul
echo [OK] Old processes stopped

echo.
echo ================================================================
echo [3/4] Installing/updating packages...
echo ================================================================
echo.

%PY_CMD% -m pip install --upgrade pip -q
%PY_CMD% -m pip install -r requirements.txt -q

if %ERRORLEVEL% EQU 0 (
    echo [OK] Packages ready
) else (
    echo [!] Some packages may have issues, continuing anyway...
)

echo.
echo ================================================================
echo [4/4] Starting backend with Python 3.10...
echo ================================================================
echo.
echo Backend will run at: http://127.0.0.1:8002
echo.
echo After it starts, run: TEST_API_DIRECT.bat
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul
echo.

%PY_CMD% -m uvicorn api.main_unified_chromadb:app --port 8002 --reload
