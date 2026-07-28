@echo off
cls
echo.
echo ================================================================
echo     QUICK AGENT B COMPARISON TEST (AUTO MODE)
echo ================================================================
echo.
echo This will automatically:
echo   [*] Execute Banking Agent A (if needed)
echo   [*] Test Banking Agent B
echo   [*] Validate structure matches Academy Sports
echo   [*] Check all banking-specific features
echo.
echo Prerequisites:
echo   - Backend must be running on port 8002
echo.
echo ----------------------------------------------------------------
echo.

REM Check if backend is running
curl -s http://localhost:8002/health >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Backend is NOT running on port 8002
    echo.
    echo Please start the backend:
    echo    ^> RESTART_ACADEMY_MATCH.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Backend is running
echo.
echo Installing dependencies...
pip install colorama requests pandas --quiet >nul 2>&1

echo.
echo ================================================================
echo Running comparison test...
echo ================================================================
echo.

python test_agent_b_comparison.py

echo.
echo ================================================================
echo.
pause
