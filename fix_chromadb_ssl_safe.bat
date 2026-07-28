@echo off
echo ========================================
echo ChromaDB Fix - SSL-Safe Installation
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Uninstalling current torch (if any)...
pip uninstall -y torch torchvision torchaudio

echo Installing compatible torch version (skipping SSL verification)...
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org torch==2.1.2

echo.
echo Testing ChromaDB...
python -c "import chromadb; print('✅ ChromaDB works!')"

echo.
echo Testing torch...
python -c "import torch; print('✅ Torch version:', torch.__version__)"

echo.
echo ========================================
echo Done! Run: python api/main_unified_chromadb.py
echo ========================================
pause
