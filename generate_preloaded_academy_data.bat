@echo off
echo ========================================
echo Academy Sports - Generating Preloaded Data
echo ========================================
echo.

cd %~dp0
python utils\academy_sports_data_generator_fast.py

if %errorlevel% neq 0 (
    echo.
    echo Trying with py -3.10...
    py -3.10 utils\academy_sports_data_generator_fast.py
)

if %errorlevel% neq 0 (
    echo ERROR: Data generation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Preloaded data ready!
echo Check data/preloaded/academy_sports/
echo ========================================
pause

