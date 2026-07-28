@echo off
echo ========================================
echo AGENT B BANKING - QUICK START
echo ========================================
echo.
echo This will start the backend with the new Agent B Banking implementation.
echo.
echo Changes:
echo   - Banking-specific 12-factor scoring (NOT retail!)
echo   - Persona-aligned recommendations
echo   - Together AI explanations (on-demand)
echo   - Rule-based + hybrid approach
echo.
echo Press Ctrl+C to stop the server when done.
echo.
pause

echo.
echo Starting backend on port 8002...
echo.

python -m uvicorn api.main_unified_chromadb:app --port 8002 --reload

pause
