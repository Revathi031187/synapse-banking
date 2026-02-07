@echo off
echo ===============================================
echo  RESTARTING WITH NAME EXPLANATION DISPLAY
echo ===============================================
echo.
echo Changes Applied:
echo   1. Backend agents return name_explanation field
echo   2. Frontend displays name explanation in insights
echo   3. Added "Why This Name?" section for both macro and micro
echo.
echo ===============================================
echo  STEP 1: Kill existing processes
echo ===============================================
echo.

taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo ===============================================
echo  STEP 2: Start Backend (Port 8002)
echo ===============================================
echo.

cd /d "%~dp0"
start "FMB Backend" cmd /k "python -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload"

echo Waiting for backend to start...
timeout /t 8 /nobreak >nul

echo ===============================================
echo  STEP 3: Start Frontend (Port 5173)
echo ===============================================
echo.

cd frontend
start "FMB Frontend" cmd /k "npm run dev"

echo.
echo ===============================================
echo  ✅ SERVICES STARTED!
echo ===============================================
echo.
echo   Backend:  http://localhost:8002
echo   Frontend: http://localhost:5173
echo.
echo WHAT TO TEST:
echo   1. Go to Segments View
echo   2. Look for "📝 Why This Name?" section
echo   3. Should appear BEFORE "Key Characteristics"
echo   4. Explains the meaning of segment name
echo.
echo Press any key to exit this window...
pause >nul
