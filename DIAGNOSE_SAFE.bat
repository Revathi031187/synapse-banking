@echo off
echo ============================================================
echo TRANSACTION DIAGNOSTICS - BULLETPROOF VERSION
echo ============================================================
echo.
echo This version will definitely produce output!
echo.
pause

echo.
echo Running diagnostics...
echo.

python diagnose_transactions_safe.py 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo ERROR: Script exited with code %ERRORLEVEL%
    echo ============================================================
)

echo.
echo ============================================================
echo.
echo Next steps:
echo 1. Read: ✅_MICRO_SEGMENTS_FIXED.md (for micro segment fix^)
echo 2. Restart backend: restart_backend.bat
echo 3. Test micro segments in browser
echo.
pause
