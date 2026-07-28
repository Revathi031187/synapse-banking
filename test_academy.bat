@echo off
cd %~dp0
echo ========================================
echo Academy Sports Implementation Test
echo ========================================
echo.

py -3.10 test_academy_sports.py
if %errorlevel% neq 0 (
    python test_academy_sports.py
)

pause

