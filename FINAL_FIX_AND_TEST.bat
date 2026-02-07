@echo off
echo ====================================================================
echo F&M BANK - FINAL FIX AND TEST
echo ====================================================================
echo.

echo [STEP 1/3] Regenerating data with correct target_segment...
python generate_fmb_data_unified.py
echo.

echo [STEP 2/3] Verifying data...
python -c "import pandas as pd; products = pd.read_csv('data/preloaded/fmb_bank/products.csv'); print('Products target_segment values:'); print(products['target_segment'].value_counts()); print('\nSample products:'); print(products[['product_name', 'category', 'target_segment']].head(10))"
echo.

echo [STEP 3/3] Checking customer variance...
python -c "import pandas as pd; customers = pd.read_csv('data/preloaded/fmb_bank/customers.csv'); print('Customer segments:'); print(customers['customer_segment'].value_counts()); print('\nCross-sell variance:'); stats = customers['cross_sell_receptivity'].describe(); print(f'  Min: {stats[\"min\"]:.3f}, Max: {stats[\"max\"]:.3f}, Std: {stats[\"std\"]:.3f}'); print('\nTransaction variance:'); stats = customers['monthly_transaction_volume'].describe(); print(f'  Min: {stats[\"min\"]:.0f}, Max: {stats[\"max\"]:.0f}, Std: {stats[\"std\"]:.0f}')"
echo.

echo ====================================================================
echo ✅ DATA REGENERATION COMPLETE!
echo ====================================================================
echo.
echo NEXT STEPS:
echo 1. RESTART BACKEND: Press Ctrl+C in terminal, then run:
echo    python api/main_unified_chromadb.py
echo.
echo 2. In UI:
echo    - Load Data (should show 5000 customers)
echo    - Run Agent A (5 personas)
echo    - Should see: "Generating micro-segments" in terminal
echo    - Agent B should now work with proper segment filtering
echo.
echo 3. Verify:
echo    - Macro Dashboard shows DIFFERENT transaction/intent values
echo    - Micro-segments appear when clicking on personas
echo    - Agent B returns 3 products (not 0)
echo ====================================================================
pause
