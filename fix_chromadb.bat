@echo off
echo ========================================
echo ChromaDB Fix - Installing CPU-Only Torch
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Uninstalling current torch...
pip uninstall -y torch

echo Installing CPU-only torch (smaller, fewer DLLs)...
pip install torch==2.1.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

echo.
echo Testing ChromaDB...
python -c "import chromadb; print('✅ ChromaDB works!')"

echo.
echo ========================================
echo Done! Try running the backend now.
echo ========================================
pause
