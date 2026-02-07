@echo off
echo ====================================
echo F&M BANK DATA GENERATION
echo ====================================

cd /d "%~dp0"

echo.
echo [1/3] Generating F&M Bank Products...
python utils\fmb_products_generator.py
if errorlevel 1 (
    echo ERROR: Product generation failed
    pause
    exit /b 1
)

echo.
echo [2/3] Generating F&M Bank Customers...
python utils\fmb_customer_generator.py
if errorlevel 1 (
    echo ERROR: Customer generation failed
    pause
    exit /b 1
)

echo.
echo [3/3] Generating F&M Bank Transactions...
python utils\fmb_transactions_generator.py
if errorlevel 1 (
    echo ERROR: Transaction generation failed
    pause
    exit /b 1
)

echo.
echo ====================================
echo SUCCESS! F&M Bank data generated
echo ====================================
echo.
echo Location: data\preloaded\fmb_bank\
echo   - customers.csv (5000 rows)
echo   - products.csv (28 rows)
echo   - transactions.csv (~75,000 rows)
echo.
pause
