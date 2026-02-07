@echo off
echo ============================================================
echo COMPREHENSIVE DATA FIX - ALL ISSUES
echo ============================================================
echo.
echo This will fix:
echo   1. monthly_transaction_volume (303x inflation)
echo   2. Out-of-range income values
echo   3. annual_transaction_value recalculation
echo.
echo Backup will be created automatically!
echo.
pause

echo.
echo Running data fixes...
echo.

python fix_all_data_issues.py 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo ERROR: Fix script failed with code %ERRORLEVEL%
    echo ============================================================
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ============================================================
echo SUCCESS! All data issues fixed!
echo ============================================================
echo.
echo IMPORTANT: You must restart the backend for changes to take effect
echo.
echo Run: restart_backend.bat
echo.
pause
