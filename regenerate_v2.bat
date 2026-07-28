@echo off
echo ======================================================================
echo Regenerating Academy Sports V2 Dataset
echo ======================================================================
echo.

cd /d "%~dp0"

echo Running data generator...
python utils/generate_v2_data_simple.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Data generation failed!
    echo Trying with py -3.10...
    py -3.10 utils/generate_v2_data_simple.py
)

echo.
echo ======================================================================
echo Done! Check output above for any errors.
echo ======================================================================
pause

