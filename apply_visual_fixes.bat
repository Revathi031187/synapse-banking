@echo off
echo ===============================================================================
echo APPLYING VISUAL DASHBOARD FIXES
echo ===============================================================================
echo.
echo Clearing Python cache...

if exist agents\__pycache__ (
    rmdir /S /Q agents\__pycache__
    echo [OK] Cleared agents cache
) else (
    echo [SKIP] agents cache does not exist
)

if exist utils\__pycache__ (
    rmdir /S /Q utils\__pycache__
    echo [OK] Cleared utils cache
) else (
    echo [SKIP] utils cache does not exist
)

echo.
echo ===============================================================================
echo FIXES APPLIED!
echo ===============================================================================
echo.
echo What was fixed:
echo   1. More diverse images (11 categories, 3-4 images each - NO REPEATS!)
echo   2. Search functionality (fixed parameter name)
echo   3. Better error handling and logging
echo.
echo NEXT STEPS:
echo   1. Restart backend: py -3.10 api/main_unified_chromadb.py
echo   2. Refresh browser (F5)
echo   3. Re-run Agent A clustering (if needed)
echo   4. Click "Visual Macro Dashboard" button
echo   5. Try searching: "tent", "backpack", "shoes"
echo ===============================================================================
pause

