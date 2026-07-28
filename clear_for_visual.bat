@echo off
echo ===============================================================================
echo CLEARING CACHE FOR VISUAL DASHBOARD
echo ===============================================================================

if exist agents\__pycache__ (
    rmdir /S /Q agents\__pycache__
    echo [OK] Cleared agents\__pycache__
) else (
    echo [SKIP] agents\__pycache__ does not exist
)

if exist utils\__pycache__ (
    rmdir /S /Q utils\__pycache__
    echo [OK] Cleared utils\__pycache__
) else (
    echo [SKIP] utils\__pycache__ does not exist
)

echo.
echo ===============================================================================
echo CACHE CLEARED!
echo ===============================================================================
echo.
echo NEXT STEPS:
echo 1. Stop backend (Ctrl+C in terminal 2)
echo 2. Restart: py -3.10 api/main_unified_chromadb.py
echo 3. In browser:
echo    - Go to Agent A
echo    - Load dataset + Run clustering
echo    - Click "Visual Macro Dashboard (NEW!)" button
echo 4. You'll see lifestyle images for each persona!
echo ===============================================================================

