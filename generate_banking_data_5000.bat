@echo off
echo ========================================
echo Banking Data Generator - 5000 Customers
echo ========================================
echo.
echo This will generate:
echo - 5,000 banking customers
echo - 20 banking products
echo - Transaction history
echo.
echo Output: data/preloaded/banking/
echo.

python utils/banking_data_generator_5000.py

echo.
echo ========================================
echo Generation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Start the backend server: python api/main_unified_chromadb.py
echo 2. Go to /banking/data-loader in the UI
echo 3. Click "Load Dataset into System"
echo 4. Run Agent A for segmentation
echo.
pause
