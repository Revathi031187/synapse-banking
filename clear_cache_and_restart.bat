@echo off
echo ===============================================================================
echo CLEARING PYTHON CACHE
echo ===============================================================================

if exist agents\__pycache__ (
    rmdir /S /Q agents\__pycache__
    echo [OK] Cleared agents\__pycache__
) else (
    echo [SKIP] agents\__pycache__ does not exist
)

if exist api\__pycache__ (
    rmdir /S /Q api\__pycache__
    echo [OK] Cleared api\__pycache__
) else (
    echo [SKIP] api\__pycache__ does not exist
)

if exist utils\__pycache__ (
    rmdir /S /Q utils\__pycache__
    echo [OK] Cleared utils\__pycache__
) else (
    echo [SKIP] utils\__pycache__ does not exist
)

echo.
echo ===============================================================================
echo CACHE CLEARED! Now:
echo 1. Stop the backend (Ctrl+C in terminal 2)
echo 2. Restart: py -3.10 api/main_unified_chromadb.py
echo 3. In browser: Go to Agent A, run clustering again
echo 4. Then go to Segmentation Overview and click a macro segment
echo ===============================================================================
pause

