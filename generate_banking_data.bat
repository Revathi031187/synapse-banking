@echo off
echo.
echo ============================================================
echo  BANKING PLATFORM - DATA GENERATION
echo ============================================================
echo.
echo Generating synthetic banking data for demo...
echo.

echo [1/3] Generating customer profiles...
python utils/banking_data_generator.py
if errorlevel 1 (
    echo ERROR: Customer generation failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Generating product catalog...
python utils/banking_products_generator.py
if errorlevel 1 (
    echo ERROR: Product generation failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Generating transaction history...
python utils/banking_transactions_generator.py
if errorlevel 1 (
    echo ERROR: Transaction generation failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  DATA GENERATION COMPLETE!
echo ============================================================
echo.
echo Generated files:
echo   - data/preloaded/banking/customers.csv (5,000 customers)
echo   - data/preloaded/banking/products.csv (60 products)
echo   - data/preloaded/banking/transactions.csv (transactions)
echo.
echo Next steps:
echo   1. Start backend: uvicorn api.main_unified_chromadb:app --port 8002
echo   2. Start frontend: cd frontend && npm run dev
echo   3. Access: http://localhost:3000/banking
echo.
pause
