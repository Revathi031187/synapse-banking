@echo off
echo ========================================
echo Generating 5000 Banking Customers
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Running data generator...
python utils/banking_data_generator_5000.py

echo.
echo ========================================
echo Generation Complete!
echo ========================================
echo.
echo Output: data/preloaded/banking_nba/
echo.
echo Files created:
dir /b data\preloaded\banking_nba\*.csv 2>nul || echo No files yet - check for errors above

echo.
echo Verifying customer count...
python -c "import pandas as pd; df = pd.read_csv('data/preloaded/banking_nba/customers.csv'); print(f'Customers generated: {len(df)}')" 2>nul || echo Could not read customers.csv

echo.
echo Next step: Reload dataset in the UI
echo   1. Go to /banking/data-loader
echo   2. Click "Load Dataset"
echo   3. Run Agent A
echo.
pause
