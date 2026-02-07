@echo off
echo ================================================================================
echo   AGENT B VALUE VERIFICATION TEST
echo ================================================================================
echo.
echo This will test:
echo   - Annual fee calculation (including $0 fees)
echo   - Average fee calculation (must include ALL products)
echo   - Fee ranges
echo   - All product attributes
echo   - Both Rule-Based and Hybrid ML agents
echo.
echo Expected Results:
echo   - Personal products: Avg Fee = $0.00
echo   - Business products: Avg Fee = ~$10.56 (if Business Credit Cards included)
echo   - Mixed products: Correct average based on all fees
echo.
echo Press any key to start testing...
pause > nul

echo.
echo Starting test...
echo.

py -3.10 test_agent_b_values.py

echo.
echo ================================================================================
echo   TEST COMPLETE
echo ================================================================================
echo.
echo Review the output above to see:
echo   - Which tests passed/failed
echo   - Average fee calculations
echo   - Expected vs actual values
echo.
pause
