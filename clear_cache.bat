@echo off
echo Clearing Python cache folders...
echo.

if exist agents\__pycache__ (
    rmdir /s /q agents\__pycache__
    echo [✓] Deleted agents\__pycache__
) else (
    echo [ ] agents\__pycache__ not found
)

if exist api\__pycache__ (
    rmdir /s /q api\__pycache__
    echo [✓] Deleted api\__pycache__
) else (
    echo [ ] api\__pycache__ not found
)

if exist utils\__pycache__ (
    rmdir /s /q utils\__pycache__
    echo [✓] Deleted utils\__pycache__
) else (
    echo [ ] utils\__pycache__ not found
)

echo.
echo ================================================================================
echo Cache cleared! Now restart your backend:
echo py -3.10 api/main_unified_chromadb.py
echo ================================================================================
pause

