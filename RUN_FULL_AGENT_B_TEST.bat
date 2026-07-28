@echo off
echo ========================================
echo COMPLETE AGENT B COMPARISON TEST
echo ========================================
echo.
echo This script will:
echo   1. Check if backend is running
echo   2. Execute Academy Sports Agent A
echo   3. Execute Banking Agent A
echo   4. Run comparison test
echo.
echo ========================================
echo.

REM Check if backend is running
echo Checking if backend is running on port 8002...
curl -s http://localhost:8002/health >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [X] Backend is NOT running!
    echo.
    echo Please start the backend first:
    echo    RESTART_ACADEMY_MATCH.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Backend is running!
echo.

echo ========================================
echo STEP 1: Execute Academy Sports Agent A
echo ========================================
echo.

curl -X POST http://localhost:8002/api/academy/agent_a/execute ^
     -H "Content-Type: application/json" ^
     -d "{\"n_personas\": 5}" ^
     -s -o academy_result.json

if %errorlevel% equ 0 (
    echo [OK] Academy Agent A executed successfully
) else (
    echo [!] Academy Agent A failed - continuing anyway
)
echo.
timeout /t 2 /nobreak >nul

echo ========================================
echo STEP 2: Execute Banking Agent A
echo ========================================
echo.

curl -X POST http://localhost:8002/api/banking/agent_a/execute ^
     -H "Content-Type: application/json" ^
     -d "{\"n_personas\": 5}" ^
     -s -o banking_result.json

if %errorlevel% equ 0 (
    echo [OK] Banking Agent A executed successfully
) else (
    echo [X] Banking Agent A failed
    echo.
    echo Check backend logs for errors
    pause
    exit /b 1
)
echo.
timeout /t 2 /nobreak >nul

REM Clean up temp files
del academy_result.json banking_result.json 2>nul

echo ========================================
echo STEP 3: Run Comparison Test
echo ========================================
echo.
timeout /t 1 /nobreak >nul

REM Install dependencies
pip install colorama requests pandas >nul 2>&1

python test_agent_b_comparison.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
echo.
echo If all checks passed, your implementation is ready!
echo.
echo Next steps:
echo   1. Test in browser (Banking Agent B page)
echo   2. Verify two sections appear (Tailored + Segment)
echo   3. Click "Get AI Explanation" button
echo.

pause
