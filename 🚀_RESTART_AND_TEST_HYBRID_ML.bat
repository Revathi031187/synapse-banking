@echo off
echo ================================================================================
echo   RESTART BACKEND WITH HYBRID ML FIXES
echo ================================================================================
echo.
echo Fixed Issues:
echo   - ML Predictions now realistic (30-80%%, not 0%%)
echo   - No more NaN%% in UI
echo   - All values display correctly
echo   - Hybrid scoring works (50%% ML + 50%% Rules)
echo.
echo Press any key to restart backend...
pause > nul

echo.
echo Stopping any running backend...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq api/main_unified_chromadb.py*" 2>nul

echo.
echo Starting backend...
echo.

py -3.10 api/main_unified_chromadb.py

pause
