@echo off
echo ========================================
echo Testing Banking API Endpoints
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Testing ChromaDB...
python -c "import chromadb; print('✅ ChromaDB works!')"

echo.
echo Testing backend API endpoints...
echo.
echo 1. Testing /api/banking/status...
curl -s http://localhost:8002/api/banking/status | python -m json.tool

echo.
echo 2. Testing /api/banking/datasets...
curl -s http://localhost:8002/api/banking/datasets | python -m json.tool

echo.
echo ========================================
echo Test complete!
echo.
echo If you see JSON responses above, the API is working! ✅
echo.
echo Next steps:
echo 1. Make sure backend is running: START_BANKING.bat
echo 2. Start frontend: cd frontend ^&^& npm run dev
echo 3. Open: http://localhost:5173/banking/agent-a
echo ========================================
pause
