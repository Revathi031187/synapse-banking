@echo off
cls
echo ================================================================
echo FIXING ONNXRUNTIME AND RESTARTING BACKEND
echo ================================================================
echo.

echo [1/3] Installing onnxruntime with Python 3.10...
echo.
py -3.10 -m pip install onnxruntime --force-reinstall
echo.

echo [2/3] Installing Microsoft Visual C++ Redistributable (if needed)...
echo.
echo If onnxruntime still fails, you need:
echo Microsoft Visual C++ Redistributable 2019 or later
echo Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
pause

echo.
echo [3/3] Killing old backend and restarting...
echo.
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting backend with Python 3.10...
echo.
py -3.10 -m uvicorn api.main_unified_chromadb:app --port 8002 --reload
