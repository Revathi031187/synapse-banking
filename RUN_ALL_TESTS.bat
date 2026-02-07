@echo off
echo ============================================================
echo COMPREHENSIVE TEST SUITE
echo ============================================================
echo.
echo Select a test to run:
echo.
echo 1. VERIFY_FIX          - Quick CSV verification (5 sec) [WORKING]
echo 2. TEST_IMPORT         - Agent import test only (2 sec)
echo 3. RUN_ULTRA_SAFE_TEST - Full test with max error handling (60 sec)
echo 4. RUN_TEST_FIXED      - Production validation test (60 sec)
echo.
echo Q. Quit
echo.
choice /c 1234Q /n /m "Enter your choice: "

if errorlevel 5 goto :eof
if errorlevel 4 goto test4
if errorlevel 3 goto test3
if errorlevel 2 goto test2
if errorlevel 1 goto test1

:test1
echo.
call VERIFY_FIX.bat
goto :eof

:test2
echo.
call TEST_IMPORT.bat
goto :eof

:test3
echo.
call RUN_ULTRA_SAFE_TEST.bat
goto :eof

:test4
echo.
call RUN_TEST_FIXED.bat
goto :eof
