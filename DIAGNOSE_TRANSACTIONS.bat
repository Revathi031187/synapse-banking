@echo off
echo ============================================================
echo TRANSACTION CALCULATION DIAGNOSTICS
echo ============================================================
echo.
echo This will analyze your transaction data and determine:
echo 1. If 'monthly_transaction_volume' is actually monthly or total
echo 2. What the correct calculation should be
echo 3. Why dashboard values seem incorrect
echo.
pause

python diagnose_transactions.py

echo.
echo ============================================================
echo.
echo Next steps:
echo 1. Review the diagnosis above
echo 2. Read: 🔍_TRANSACTION_CALCULATION_EXPLAINED.md
echo 3. Apply the recommended fix
echo.
pause
