@echo off
echo ========================================
echo AGENT B BANKING - ACADEMY SPORTS MATCH
echo ========================================
echo.
echo Implementation now EXACTLY matches Academy Sports:
echo.
echo Structure:
echo   - get_similar_products() [transaction history]
echo   - get_segment_recommendations() [segment popular]
echo   - get_all_recommendations() [combines both]
echo.
echo Response Format:
echo   - tailored_recommendations: [...]
echo   - segment_recommendations: [...]
echo   - recommendation_metadata: {...}
echo.
echo Frontend Display:
echo   - Section 1: Tailored For You (persona-aligned)
echo   - Section 2: Popular in Your Segment
echo.
echo Banking-Specific:
echo   - Banking 12-factor scoring
echo   - Banking product pairing rules
echo   - Eligibility checks (credit, income, balance)
echo   - Together AI explanations
echo.
echo Killing existing backend...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul

echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul

echo.
echo Starting backend on port 8002...
echo.
pause

python -m uvicorn api.main_unified_chromadb:app --port 8002 --reload

pause
