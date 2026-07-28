@echo off
echo ======================================================================
echo Generating REALISTIC V2 Dataset (with overlap and noise)
echo ======================================================================
echo.

cd /d "%~dp0"

echo Running realistic data generator...
py -3.10 utils/generate_v2_realistic.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Data generation failed!
    echo Trying with python command...
    python utils/generate_v2_realistic.py
)

echo.
echo ======================================================================
echo Done! Now test with both datasets to compare accuracy.
echo ======================================================================
pause

