@echo off
echo ================================================================================
echo   RESTART WITH BANKING-SPECIFIC METRICS
echo ================================================================================
echo.
echo NEW METRICS ADDED:
echo   1. Match Quality (avg + top) - Shows quality range
echo   2. Annual Cost (total + free count) - Total financial commitment  
echo   3. Earning Potential (est + APY) - Income opportunity
echo   4. Easy Access (no-minimum count) - Immediate accessibility
echo.
echo REMOVED METRICS:
echo   - "Products Considered" (not useful)
echo   - "Avg Annual Fee" (replaced with total cost)
echo   - "Fee Range" (replaced with free count)
echo.
echo BENEFITS:
echo   - More personalized understanding
echo   - Clear financial impact
echo   - Actionable information
echo   - Better customer decisions
echo.
echo Press any key to restart backend...
pause > nul

echo.
echo Starting backend with enhanced metrics...
echo.

py -3.10 api/main_unified_chromadb.py

pause
