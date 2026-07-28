@echo off
echo ========================================
echo ChromaDB Fix - Using Older Stable Versions
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Uninstalling problematic packages...
pip uninstall -y torch sentence-transformers chromadb onnxruntime

echo Installing older, more compatible versions...
pip install torch==1.13.1
pip install onnxruntime==1.14.1
pip install sentence-transformers==2.2.2
pip install chromadb==0.4.15

echo.
echo Testing ChromaDB...
python -c "import chromadb; print('✅ ChromaDB works!')"

echo.
echo ========================================
echo Done! Try running the backend now.
echo ========================================
pause
