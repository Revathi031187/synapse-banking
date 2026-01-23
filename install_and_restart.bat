@echo off
echo ========================================
echo   INSTALLING DEPENDENCIES
echo ========================================
echo.
echo Installing python-dotenv...
pip install python-dotenv
echo.
echo ========================================
echo   STARTING BACKEND SERVER
echo ========================================
echo.
cd api
py -3.10 main_unified_chromadb.py


