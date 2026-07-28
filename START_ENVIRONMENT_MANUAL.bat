@echo off
echo ========================================
echo   MANUAL START INSTRUCTIONS
echo ========================================
echo.
echo Option 1: Using Virtual Environment (venv)
echo ------------------------------------------
echo.
echo Step 1: Activate virtual environment:
echo    venv\Scripts\activate
echo.
echo Step 2: Start backend:
echo    python api/main_unified_chromadb.py
echo.
echo.
echo Option 2: Using System Python 3.10
echo ------------------------------------------
echo.
echo If you have Python 3.10 installed:
echo    py -3.10 api/main_unified_chromadb.py
echo.
echo.
echo Option 3: Check Python Version
echo ------------------------------------------
echo.
echo Run this to check your Python version:
echo    python --version
echo.
echo NOTE: You need Python 3.10 or 3.11 (NOT 3.14)
echo       Python 3.14 has compatibility issues with FastAPI
echo.
echo ========================================
echo.
pause
