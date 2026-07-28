@echo off
echo ========================================
echo Starting Banking Personalization Agent
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Starting backend server...
echo.
echo Backend will be available at: http://localhost:8002
echo Frontend should be running separately on: http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo.

python api/main_unified_chromadb.py
