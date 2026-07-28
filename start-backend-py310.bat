@echo off
echo ============================================
echo  Starting FastAPI Backend (Python 3.10)
echo ============================================
echo.

REM Try to find Python 3.10
set PYTHON_CMD=

REM Check common Python 3.10 installations
where py >nul 2>&1
if %errorlevel% == 0 (
    py -3.10 --version >nul 2>&1
    if %errorlevel% == 0 (
        set PYTHON_CMD=py -3.10
        echo Found Python 3.10 via py launcher
    )
)

if "%PYTHON_CMD%"=="" (
    python --version 2>&1 | findstr "3.10" >nul
    if %errorlevel% == 0 (
        set PYTHON_CMD=python
        echo Found Python 3.10 as default
    )
)

if "%PYTHON_CMD%"=="" (
    python3.10 --version >nul 2>&1
    if %errorlevel% == 0 (
        set PYTHON_CMD=python3.10
        echo Found python3.10
    )
)

if "%PYTHON_CMD%"=="" (
    echo.
    echo ================================================
    echo ERROR: Python 3.10 not found!
    echo ================================================
    echo.
    echo Python 3.14 is too new for FastAPI/Pydantic.
    echo Please install Python 3.10 or 3.11 or 3.12.
    echo.
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Using: %PYTHON_CMD%
echo.

REM Install/upgrade required packages
echo Installing/upgrading FastAPI packages...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install --upgrade fastapi uvicorn pydantic

echo.
echo Starting FastAPI backend...
echo Backend will run on: http://localhost:8000
echo.
%PYTHON_CMD% api/main_enhanced.py

pause

