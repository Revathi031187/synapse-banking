@echo off
echo ====================================================================
echo Initializing ChromaDB for Academy Sports
echo ====================================================================
echo.
echo This will create embeddings for fast data retrieval...
echo.

python scripts/initialize_chromadb_academy.py

echo.
echo ====================================================================
echo Done! You can now run the Streamlit app with ChromaDB support.
echo ====================================================================
pause

