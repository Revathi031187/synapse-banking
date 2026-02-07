@echo off
echo ================================================================================
echo   AGENT B COMPREHENSIVE TEST SUITE
echo ================================================================================
echo.
echo This will test:
echo   - Weight validation (13 factors = 100%%)
echo   - Data loading
echo   - Agent A (persona creation)
echo   - Rule-Based Agent B
echo   - Hybrid ML Agent B
echo   - 13-Factor scorer
echo   - Product differentiation
echo.
echo Press any key to start testing...
pause > nul

echo.
echo Starting test...
echo.

py -3.10 test_agent_b_complete.py

echo.
echo ================================================================================
echo   TEST COMPLETE
echo ================================================================================
echo.
echo Results saved to: test_agent_b_results.json
echo.
echo Review the output above to see:
echo   - Which tests passed/failed
echo   - Score differentiation analysis
echo   - Product Value factor validation
echo.
pause
