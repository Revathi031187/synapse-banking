@echo off
echo ============================================================
echo RESTART BACKEND TO LOAD NEW CODE
echo ============================================================
echo.
echo The backend API is currently running with OLD code.
echo You need to RESTART it to load the new fixes:
echo.
echo 1. Press Ctrl+C in the backend terminal to stop it
echo 2. Run again: py -3.10 api/main_unified_chromadb.py
echo.
echo Then test in UI at http://localhost:5173/banking/agent-a
echo.
echo ============================================================
pause
