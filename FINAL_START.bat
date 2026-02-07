@echo off
chcp 65001 >nul 2>&1

echo ================================================================
echo FINAL FIX: ONNXRUNTIME MOCK APPLIED
echo ================================================================
echo.
echo What was fixed:
echo  - Mocked onnxruntime module BEFORE importing chromadb
echo  - This prevents DLL errors during module import
echo  - ChromaDB will use our SimpleTextEmbeddingFunction instead
echo.
echo ================================================================
echo [1/2] Stopping old backend...
echo ================================================================
echo.

taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Clean slate

echo.
echo ================================================================
echo [2/2] Starting backend with Python 3.10...
echo ================================================================
echo.
echo Backend: http://127.0.0.1:8002
echo.
echo Wait for "Application startup complete"
echo Then run: TEST_API_DIRECT.bat
echo.

py -3.10 -m uvicorn api.main_unified_chromadb:app --reload --host 0.0.0.0 --port 8002

pause
