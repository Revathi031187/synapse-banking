@echo off
echo ========================================
echo   RESTART BACKEND WITH DYNAMIC SYSTEM
echo ========================================
echo.
echo This will restart the backend to apply:
echo   - Dynamic segment names
echo   - Real transaction calculations
echo   - Gamma parameter from frontend
echo   - Essential churn features
echo.
echo Press Ctrl+C to cancel, or
pause
echo.
echo Starting backend...
echo.
python api/main_unified_chromadb.py
