@echo off
echo ================================================================
echo CLEAR CACHE AND TEST COMPLETE SYSTEM
echo ================================================================

cd /d "%~dp0"

echo.
echo [1/3] Clearing any cached data...
echo.

echo [2/3] Testing with fresh Agent A and Agent Micro...
py -3.10 test_ultra_final.py

echo.
echo [3/3] Instructions:
echo ================================================================
echo.
echo NOW DO THIS IN YOUR BACKEND:
echo.
echo 1. Stop backend (Ctrl+C)
echo 2. Delete chroma_db folder if it exists: rmdir /s /q chroma_db
echo 3. Restart: py -3.10 api/main_unified_chromadb.py
echo 4. In UI: Clear browser cache (Ctrl+Shift+Delete)
echo 5. Reload UI and run Agent A fresh
echo.
echo ================================================================
pause
