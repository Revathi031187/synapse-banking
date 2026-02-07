@echo off
echo ====================================================================
echo           F&M BANK PERSONALIZATION PLATFORM
echo    Farmers ^& Merchants Bank of Central California
echo    "Where Banking Is Easy - Since 1916"
echo ====================================================================
echo.
echo Starting F&M Bank platform...
echo.

cd /d "%~dp0"

echo [Backend] Starting API server...
start "F&M Bank API" cmd /k "python api\main_unified_chromadb.py"

timeout /t 3 /nobreak > nul

echo [Frontend] Starting React app...
cd frontend
start "F&M Bank Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ====================================================================
echo ✅ F&M Bank Platform Started!
echo ====================================================================
echo.
echo 📡 Backend API: http://localhost:8000
echo 🌐 Frontend:    http://localhost:5173
echo.
echo 📊 Data Location: data/preloaded/fmb_bank/
echo    - Products: 28 (Personal/Business/Agricultural)
echo    - Customers: 5000
echo    - Transactions: ~85,000
echo.
echo 🏦 F&M Bank Features:
echo    • Personal Banking (3000 customers)
echo    • Business Banking (1500 customers)
echo    • Agricultural Banking (500 customers)
echo    • Segment-based product recommendations
echo    • AI-powered customer personas
echo.
echo Press any key to stop both servers...
pause > nul

echo Stopping servers...
taskkill /FI "WindowTitle eq F&M Bank API*" /T /F 2>nul
taskkill /FI "WindowTitle eq F&M Bank Frontend*" /T /F 2>nul

echo.
echo F&M Bank Platform stopped.
pause
