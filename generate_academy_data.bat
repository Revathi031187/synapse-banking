@echo off
echo ========================================
echo Academy Sports Data Generator
echo ========================================
echo.

cd %~dp0
py -3.10 utils\academy_sports_data_generator.py

if %errorlevel% neq 0 (
    echo ERROR: Data generation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Data generation complete!
echo Check data/academy_sports/ folder
echo ========================================
pause

