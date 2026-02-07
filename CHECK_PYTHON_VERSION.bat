@echo off
echo ================================================================
echo CHECKING PYTHON VERSION
echo ================================================================
echo.
python --version
echo.
echo ----------------------------------------------------------------
echo Python executable location:
where python
echo.
echo ================================================================
echo.
echo Your Python version is shown above.
echo.
echo [X] Python 3.14.x (alpha) = NOT COMPATIBLE - Must downgrade!
echo [OK] Python 3.11.x = RECOMMENDED
echo [OK] Python 3.12.x = Also good
echo.
echo If you see "3.14", you MUST install Python 3.11 or 3.12
echo Download from: https://www.python.org/downloads/
echo.
pause
