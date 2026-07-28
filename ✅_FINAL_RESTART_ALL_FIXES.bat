@echo off
echo ================================================================================
echo   RESTART BACKEND - ALL FIXES APPLIED
echo ================================================================================
echo.
echo FIXES APPLIED:
echo   1. Annual fee values display correctly
echo   2. Free products show "Free" instead of $0.00/year
echo   3. All numeric fields properly converted (pandas to Python types)
echo   4. Min balance display added
echo   5. Interest rate display fixed
echo   6. Both Rule-Based and Hybrid ML working
echo   7. Works for both Persona and Customer modes
echo.
echo EXPECTED BEHAVIOR:
echo   - Personal products: Will show "Free" (correct - they are free!)
echo   - Business Credit Cards: Will show "$95.00/year"  
echo   - All other values: Properly displayed
echo.
echo Press any key to restart backend...
pause > nul

echo.
echo Starting backend...
echo.

py -3.10 api/main_unified_chromadb.py

pause
