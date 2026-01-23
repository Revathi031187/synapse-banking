@echo off
cd %~dp0
echo ========================================
echo Academy Sports ChromaDB Initialization
echo ========================================
echo.

py -3.10 scripts\initialize_chromadb_academy.py
if %errorlevel% neq 0 (
    echo.
    echo Trying python...
    python scripts\initialize_chromadb_academy.py
)

pause

