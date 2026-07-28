@echo off
echo ============================================================
echo REGENERATING CSV FILES - FINAL FIX
echo ============================================================
echo.
echo This will fix the CSV file format so pandas can read it properly
echo.

python REGENERATE_CSV_PROPERLY.py

echo.
echo ============================================================
echo.
echo If successful, now run: TEST_SHORT_NAMES.bat
echo.
pause
