@echo off
echo ========================================
echo Installing K-Modes Library
echo ========================================
echo.

cd %~dp0

echo Trying py -3.10...
py -3.10 -m pip install kmodes==0.12.2

if %errorlevel% neq 0 (
    echo.
    echo Trying python...
    python -m pip install kmodes==0.12.2
)

if %errorlevel% neq 0 (
    echo ERROR: Installation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo K-Modes installed successfully!
echo ========================================
pause

