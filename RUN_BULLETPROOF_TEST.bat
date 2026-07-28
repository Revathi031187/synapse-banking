@echo off
echo ============================================================
echo BULLETPROOF TEST (Writes to log file)
echo ============================================================
echo.
echo Running test and logging to test_output.log...
echo.

python test_bulletproof.py 2>&1

if exist test_output.log (
    echo.
    echo ============================================================
    echo TEST LOG CONTENTS:
    echo ============================================================
    type test_output.log
    echo.
    echo ============================================================
    echo Log file: test_output.log
    echo ============================================================
) else (
    echo.
    echo ERROR: Log file was not created!
    echo Python may have crashed immediately.
)

echo.
pause
