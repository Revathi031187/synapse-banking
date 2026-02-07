@echo off
echo ========================================
echo FINAL COMPREHENSIVE TEST
echo ========================================

cd /d "%~dp0"

echo.
echo [1/2] Adding CLV to customer data...
py -3.10 add_clv_to_data.py
if errorlevel 1 (
    echo ERROR: CLV addition failed
    pause
    exit /b 1
)

echo.
echo [2/2] Running comprehensive test...
py -3.10 test_final_complete.py
if errorlevel 1 (
    echo ERROR: Test failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo ALL TESTS COMPLETE!
echo ========================================
pause
