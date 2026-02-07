@echo off
chcp 65001 >nul 2>&1
echo ================================================================
echo AGENT B TEST (With Correct JSON Parsing)
echo ================================================================
echo.

echo [1/5] Checking backend health...
curl -s http://localhost:8002/api/banking/status >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Backend not running - run RESTART_WITH_FIX.bat first
    pause
    exit /b 1
)
echo [OK] Backend is running
echo.

echo ----------------------------------------------------------------
echo [2/5] Executing Banking Agent A...
echo.

curl -X POST http://localhost:8002/api/banking/agent_a/execute ^
     -H "Content-Type: application/json" ^
     -d "{\"n_personas\": 3, \"n_clusters\": 3, \"gamma\": 0.3}" ^
     -s -w "\nHTTP Status: %%{http_code}\n"

echo.
echo Waiting for Agent A to complete...
timeout /t 3 /nobreak >nul
echo.

echo ----------------------------------------------------------------
echo [3/5] Getting first customer (using Python for JSON parsing)...
echo.

curl -s "http://localhost:8002/api/banking/customers?limit=1" > customer_test.json

REM Use Python to extract customer_id properly
py -3.10 -c "import json; data=json.load(open('customer_test.json')); print(data['customers'][0]['customer_id'] if data.get('customers') and len(data['customers']) > 0 else 'ERROR')" > temp_cid.txt
set /p CUSTOMER_ID=<temp_cid.txt
del temp_cid.txt

if "%CUSTOMER_ID%"=="ERROR" (
    echo [X] Failed to get customer ID
    type customer_test.json
    pause
    exit /b 1
)

echo [OK] Got customer: %CUSTOMER_ID%
echo.

echo ----------------------------------------------------------------
echo [4/5] Executing Banking Agent B...
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

REM Check if recommendations are not empty
py -3.10 -c "import json; data=json.load(open('agent_b_result.json')); recs=data.get('tailored_recommendations',[])+data.get('segment_recommendations',[]); print('yes' if len(recs)>0 else 'no')" > temp_check.txt
set /p HAS_RECS=<temp_check.txt
del temp_check.txt

if "%HAS_RECS%"=="yes" (
    echo [OK] Has actual recommendations
) else (
    echo [!] Recommendations are empty - this might be expected if customer has no transactions
)

echo.
echo ================================================================
echo TEST COMPLETE
echo ================================================================
echo.
echo Customer used: %CUSTOMER_ID%
echo Full response saved to: agent_b_result.json
echo.

REM Clean up
del customer_test.json 2>nul

pause
