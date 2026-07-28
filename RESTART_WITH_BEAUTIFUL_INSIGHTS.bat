@echo off
echo ========================================================================
echo  RESTART WITH BEAUTIFUL SEGMENT INSIGHTS + UNIQUE EXPLANATIONS
echo ========================================================================
echo.
echo Changes Applied:
echo   ✓ Macro segments: FULL name uniqueness (not just first word)
echo   ✓ Macro segments: Beautiful gradient card styling
echo   ✓ Micro segments: Beautiful gradient card styling  
echo   ✓ Segment definitions: Emoji formatting + structured layout
echo   ✓ Name explanations: Blue/purple gradient boxes
echo   ✓ Key behaviors: Purple/blue gradient with checkmarks
echo   ✓ Marketing: Amber gradient with arrows
echo.
echo ========================================================================
echo  STEP 1: Kill existing processes
echo ========================================================================
echo.

taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo ========================================================================
echo  STEP 2: Start Backend (Port 8002)
echo ========================================================================
echo.

cd /d "%~dp0"
start "FMB Backend" cmd /k "python -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload"

echo Waiting for backend to initialize...
timeout /t 10 /nobreak >nul

echo ========================================================================
echo  STEP 3: Start Frontend (Port 5173)
echo ========================================================================
echo.

cd frontend
start "FMB Frontend" cmd /k "npm run dev"

echo.
echo ========================================================================
echo  ✓ ALL SERVICES STARTED!
echo ========================================================================
echo.
echo   Backend:  http://localhost:8002
echo   Frontend: http://localhost:5173
echo.
echo WHAT'S NEW:
echo   1. Each segment has UNIQUE explanations (no more duplicates!)
echo   2. Beautiful gradient cards for all insights
echo   3. Emoji icons for visual clarity
echo   4. Structured, easy-to-read formatting
echo   5. Name explanations in colored boxes
echo.
echo Navigate to Segments View to see the improvements!
echo.
pause
