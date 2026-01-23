@echo off
echo ========================================
echo   SETUP TOGETHER AI API KEY
echo ========================================
echo.
echo To enable AI explanations, set your Together AI API key:
echo.
set /p api_key="Enter your Together AI API key: "
echo.
setx TOGETHER_API_KEY "%api_key%"
echo.
echo ✅ API key saved to environment variables!
echo.
echo Now restart your backend server:
echo   1. Press Ctrl+C in your backend terminal
echo   2. Run: cd api
echo   3. Run: py -3.10 main_unified_chromadb.py
echo.
pause

