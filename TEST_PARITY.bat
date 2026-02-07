@echo off
echo ========================================
echo   BANKING vs ACADEMY SPORTS PARITY TEST
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Running comprehensive parity test...
echo.

python TEST_COMPLETE_PARITY.py

echo.
echo ========================================
echo Test complete!
echo ========================================
pause
