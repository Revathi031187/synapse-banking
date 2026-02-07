@echo off
echo Regenerating F&M Bank Data with Correct Distribution...
python generate_fmb_data_unified.py
echo.
echo Verifying customer distribution...
python -c "import pandas as pd; df = pd.read_csv('data/preloaded/fmb_bank/customers.csv'); print(f'\nTotal Customers: {len(df)}'); print('\nSegment Breakdown:'); print(df['customer_segment'].value_counts()); print('\nCustomer Type Breakdown:'); print(df['customer_type'].value_counts())"
pause
