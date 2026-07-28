@echo off
echo ========================================
echo RESTARTING BACKEND WITH BUG FIXES
echo ========================================
echo.
echo Fixes applied:
echo   1. Fixed system_state None assignment error
echo   2. Fixed frontend API request format
echo   3. Fixed customer dropdown display
echo   4. Fixed response data structure handling
echo   5. Fixed AI explanation customer_id
echo.
echo Killing existing backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul

echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul

echo.
echo Starting backend on port 8002...
echo.
echo Test steps:
echo   1. Execute Agent A (Banking - Agent A: Personas)
echo   2. Go to Agent B: Products
echo   3. Switch to "Customer Level"
echo   4. Select a customer
echo   5. Click "Get Customer Recommendations"
echo   6. Click "Get AI Explanation" on any product
echo.
pause

python -m uvicorn api.main_unified_chromadb:app --port 8002 --reload

pause
