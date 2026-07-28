@echo off
echo ========================================
echo   FINAL COMPREHENSIVE TEST
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Testing Banking Implementation...
echo.

REM Test 1: Check data files exist
echo [TEST 1] Checking data files...
if exist "data\preloaded\banking_nba\customers.csv" (
    echo ✅ customers.csv exists
) else (
    echo ❌ customers.csv MISSING
)

if exist "data\preloaded\banking_nba\products.csv" (
    echo ✅ products.csv exists
) else (
    echo ❌ products.csv MISSING
)

if exist "data\preloaded\banking_nba\transactions.csv" (
    echo ✅ transactions.csv exists
) else (
    echo ❌ transactions.csv MISSING
)

echo.

REM Test 2: Verify customer count
echo [TEST 2] Verifying customer count...
python -c "import pandas as pd; df = pd.read_csv('data/preloaded/banking_nba/customers.csv'); count = len(df); print(f'Total customers: {count}'); print('✅ PASS: 5000 customers' if count == 5000 else '❌ FAIL: Expected 5000')"

echo.

REM Test 3: Test Agent A import
echo [TEST 3] Testing Agent A import...
python -c "from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced; print('✅ Agent A imports successfully')" 2>nul && echo ✅ Agent A OK || echo ❌ Agent A import FAILED

echo.

REM Test 4: Test Micro Agent import
echo [TEST 4] Testing Micro Agent import...
python -c "from agents.agent_a_banking_micro import AgentA_Banking_Micro; print('✅ Micro Agent imports successfully')" 2>nul && echo ✅ Micro Agent OK || echo ❌ Micro Agent import FAILED

echo.

REM Test 5: Test Image Mapper
echo [TEST 5] Testing Image Mapper...
python -c "from utils.image_mapper import get_image_mapper; mapper = get_image_mapper(); print('✅ Image Mapper loaded'); print(f'   Banking categories: {len([k for k in mapper.MACRO_PERSONA_IMAGES.keys() if k in [\"wealth_management\", \"business_banking\", \"digital_banking\", \"investment\", \"traditional_banking\", \"financial_planning\", \"entrepreneurship\", \"retirement\"]]}')}" 2>nul && echo ✅ Image Mapper OK || echo ❌ Image Mapper FAILED

echo.

REM Test 6: Quick API test
echo [TEST 6] Testing API endpoints (requires backend running)...
curl -s http://localhost:8002/api/banking/status >nul 2>&1 && echo ✅ Banking API responding || echo ⚠️  Banking API not responding (start backend first)

echo.
echo ========================================
echo Test Summary
echo ========================================
echo.
echo ✅ If all tests passed, restart backend and test UI
echo ⚠️  If any failed, check error messages above
echo.
echo Next Steps:
echo 1. Restart backend: Ctrl+C then START_BANKING.bat
echo 2. Go to: http://localhost:5173/banking/macro-dashboard
echo 3. You should see beautiful banking images!
echo.
pause
