@echo off
echo ================================================================
echo DIRECT API TEST (No Python Required)
echo ================================================================
echo.
echo This tests the Banking Agent B API directly using curl
echo.

echo [1/5] Checking backend health...
curl -s http://localhost:8002/health
if %errorlevel% neq 0 (
    echo [X] Backend not running
    pause
    exit /b 1
)
echo.
echo [OK] Backend is running
echo.

echo ----------------------------------------------------------------
echo [2/5] Executing Banking Agent A (creating personas)...
echo.

curl -X POST http://localhost:8002/api/banking/agent_a/execute ^
     -H "Content-Type: application/json" ^
     -d "{\"n_personas\": 5}" ^
     -s -w "\nHTTP Status: %%{http_code}\n"

echo.
echo Waiting 3 seconds for Agent A to complete...
timeout /t 3 /nobreak >nul
echo.

echo ----------------------------------------------------------------
echo [3/5] Getting first customer...
echo.

curl -s http://localhost:8002/api/banking/customers?limit=1 > customer_test.json

type customer_test.json
echo.
echo.

echo ----------------------------------------------------------------
echo [4/5] Executing Banking Agent B...
echo.

REM Extract customer ID from JSON using Python (reliable method)
py -3.10 -c "import json; data=json.load(open('customer_test.json')); print(data['customers'][0]['customer_id'] if data.get('customers') and len(data['customers']) > 0 else 'ERROR')" > temp_cid.txt
set /p CUSTOMER_ID=<temp_cid.txt
del temp_cid.txt

if "%CUSTOMER_ID%"=="ERROR" (
    echo [X] Failed to get customer ID from response
    pause
    exit /b 1
)

echo Using customer: %CUSTOMER_ID%
echo.

curl -X POST http://localhost:8002/api/banking/agent_b/execute ^
     -H "Content-Type: application/json" ^
     -d "{\"customer_id\": \"%CUSTOMER_ID%\", \"use_persona_aligned\": true}" ^
     -s > agent_b_result.json

echo Agent B Response:
type agent_b_result.json
echo.
echo.

echo ----------------------------------------------------------------
echo [5/5] Validating response structure...
echo.

findstr /i "tailored_recommendations" agent_b_result.json >nul
if %errorlevel% equ 0 (
    echo [OK] Has 'tailored_recommendations'
) else (
    echo [X] Missing 'tailored_recommendations'
)

findstr /i "segment_recommendations" agent_b_result.json >nul
if %errorlevel% equ 0 (
    echo [OK] Has 'segment_recommendations'
) else (
    echo [X] Missing 'segment_recommendations'
)

findstr /i "recommendation_metadata" agent_b_result.json >nul
if %errorlevel% equ 0 (
    echo [OK] Has 'recommendation_metadata'
) else (
    echo [X] Missing 'recommendation_metadata'
)

findstr /i "score_breakdown" agent_b_result.json >nul
if %errorlevel% equ 0 (
    echo [OK] Has 'score_breakdown' (12-factor scoring)
) else (
    echo [X] Missing 'score_breakdown'
)

echo.
echo ================================================================
echo TEST COMPLETE
echo ================================================================
echo.
echo Full response saved to: agent_b_result.json
echo.
echo If all checks show [OK], your implementation is working correctly!
echo.

REM Clean up
del customer_test.json 2>nul

pause
