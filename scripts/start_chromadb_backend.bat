@echo off
echo ================================================================================
echo NBA PLATFORM - STARTING CHROMADB BACKEND
echo ================================================================================
echo.

REM Kill any existing Python processes
echo Cleaning up any existing Python processes...
taskkill /F /IM python.exe >nul 2>&1

REM Wait a moment
timeout /t 2 /nobreak >nul

echo Starting ChromaDB-powered backend on port 8002...
echo.
echo ================================================================================
echo 🚀 Backend will be available at: http://localhost:8002
echo 📚 API Documentation: http://localhost:8002/docs
echo 📊 ChromaDB Stats: http://localhost:8002/api/chromadb/stats
echo ================================================================================
echo.

py -3.10 api\main_unified_chromadb.py

pause

