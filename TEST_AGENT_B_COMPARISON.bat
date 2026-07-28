@echo off
echo ========================================
echo AGENT B IMPLEMENTATION COMPARISON TEST
echo ========================================
echo.
echo This test will:
echo   1. Test Academy Sports Agent B
echo   2. Test Banking Agent B
echo   3. Compare response structures
echo   4. Validate all required fields
echo   5. Check banking-specific features
echo   6. Test AI explanation endpoint
echo.
echo Prerequisites:
echo   - Backend must be running (port 8002)
echo   - Agent A must have been executed for both domains
echo.
echo ----------------------------------------
echo.

REM Install colorama if needed
pip install colorama requests pandas >nul 2>&1

echo Running comparison test...
echo.

python test_agent_b_comparison.py

echo.
echo ========================================
echo Test complete!
echo ========================================
echo.
echo Review the output above to see:
echo   - Structure comparison (Academy vs Banking)
echo   - Field comparison (all required fields present?)
echo   - Recommendation counts
echo   - Banking-specific features (12-factor scoring)
echo   - AI explanation functionality
echo.

pause
