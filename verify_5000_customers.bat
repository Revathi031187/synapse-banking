@echo off
echo ========================================
echo Verifying 5000 Customer Data
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Checking customer count...
python -c "import pandas as pd; df = pd.read_csv('data/preloaded/banking_nba/customers.csv'); print(f'\nTotal customers: {len(df)}'); print(f'Expected: 5000'); print(f'Match: {\"YES\" if len(df) == 5000 else \"NO - Run GENERATE_5000_CUSTOMERS.bat\"}')"

echo.
echo Checking products...
python -c "import pandas as pd; df = pd.read_csv('data/preloaded/banking_nba/products.csv'); print(f'Total products: {len(df)}')"

echo.
echo Checking transactions...
python -c "import pandas as pd; df = pd.read_csv('data/preloaded/banking_nba/transactions.csv'); print(f'Total transactions: {len(df)}')"

echo.
echo ========================================
pause
