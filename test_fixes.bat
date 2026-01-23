@echo off
echo ========================================
echo Testing Micro Segments and Data Loader Fixes
echo ========================================
echo.

echo Checking if backend is running...
curl -s http://localhost:8002/ >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Backend is not running!
    echo Please start the backend first:
    echo   cd api
    echo   python main_unified_chromadb.py
    echo.
    pause
    exit /b 1
)

echo [OK] Backend is running
echo.

echo Running API tests...
echo.
python test_micro_and_loader_fixes.py

echo.
echo ========================================
echo Test complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open browser: http://localhost:5173
echo 2. Go to Academy Sports
echo 3. Click Agent A
echo 4. Try the "Data Loader" tab
echo 5. Run clustering and click on a persona
echo.
pause
