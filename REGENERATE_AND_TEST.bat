@echo off
echo ========================================
echo   REGENERATE DATA AND TEST SYSTEM
echo ========================================
echo.
echo This will:
echo   1. Generate fresh FMB data (78,568 transactions)
echo   2. Add essential churn features (10 features, real data)
echo   3. Run production validation
echo   4. Run complete system test
echo.
echo Press Ctrl+C to cancel, or
pause
echo.

echo ========================================
echo Step 1: Generating FMB Bank Data...
echo ========================================
python generate_fmb_data_unified.py
echo.

echo ========================================
echo Step 2: Running Production Validation...
echo ========================================
python validate_production_readiness.py
echo.

echo ========================================
echo Step 3: Running Complete System Test...
echo ========================================
python test_complete_dynamic_system.py
echo.

echo ========================================
echo  ALL DONE!
echo ========================================
echo.
echo Next steps:
echo   1. Restart backend: python api/main_unified_chromadb.py
echo   2. Go to UI: http://localhost:5173/banking/data-loader
echo   3. Load data and run Agent A
echo.
echo Press any key to exit...
pause > nul
