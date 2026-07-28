@echo off
echo ================================================================================
echo Installing ChromaDB with Python 3.10
echo This will take 5-10 minutes - please wait...
echo ================================================================================
echo.

py -3.10 -m pip install --upgrade pip
echo Installing ChromaDB and sentence-transformers...
py -3.10 -m pip install chromadb sentence-transformers
echo.
echo Installing PyTorch (CPU version)...
py -3.10 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo.
echo ================================================================================
echo Installation complete!
echo Testing ChromaDB...
echo ================================================================================
py -3.10 -c "import chromadb; print('✅ ChromaDB is working!')"

pause

