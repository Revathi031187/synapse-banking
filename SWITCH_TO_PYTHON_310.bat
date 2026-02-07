@echo off
cls
echo ================================================================
echo FINDING PYTHON 3.10
echo ================================================================
echo.
echo Checking all Python installations...
echo.

where python

echo.
echo ----------------------------------------------------------------
echo.
echo Looking for Python 3.10 specifically...
echo.

:: Check common Python 3.10 locations
set PYTHON310_PATH=

if exist "C:\Python310\python.exe" (
    echo [FOUND] C:\Python310\python.exe
    set PYTHON310_PATH=C:\Python310\python.exe
)

if exist "C:\Program Files\Python310\python.exe" (
    echo [FOUND] C:\Program Files\Python310\python.exe
    set PYTHON310_PATH=C:\Program Files\Python310\python.exe
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe" (
    echo [FOUND] C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe
    set PYTHON310_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe
)

echo.
echo ----------------------------------------------------------------
echo.

if defined PYTHON310_PATH (
    echo ✓ Python 3.10 found at: %PYTHON310_PATH%
    echo.
    echo Testing Python 3.10:
    "%PYTHON310_PATH%" --version
    echo.
    echo ================================================================
    echo CREATING VIRTUAL ENVIRONMENT WITH PYTHON 3.10
    echo ================================================================
    echo.
    echo This will create a virtual environment that uses Python 3.10
    echo and keeps it isolated from Python 3.14 alpha.
    echo.
    pause
    echo.
    echo Creating virtual environment...
    "%PYTHON310_PATH%" -m venv venv310
    echo.
    if exist "venv310\Scripts\activate.bat" (
        echo ✓ Virtual environment created successfully!
        echo.
        echo ================================================================
        echo ACTIVATING AND INSTALLING PACKAGES
        echo ================================================================
        echo.
        call venv310\Scripts\activate.bat
        echo.
        echo Upgrading pip...
        python -m pip install --upgrade pip
        echo.
        echo Installing requirements...
        pip install -r requirements.txt
        echo.
        echo ================================================================
        echo SUCCESS! Python 3.10 environment ready!
        echo ================================================================
        echo.
        echo To use this environment in the future:
        echo 1. Run: venv310\Scripts\activate.bat
        echo 2. Then run your backend normally
        echo.
        echo Or use: START_WITH_PYTHON_310.bat
        echo.
        pause
    ) else (
        echo [X] Failed to create virtual environment
        pause
    )
) else (
    echo [X] Could not find Python 3.10 installation
    echo.
    echo Please run this command manually to find it:
    echo.
    echo py -3.10 --version
    echo.
    echo Or check these locations:
    echo - C:\Python310\
    echo - C:\Program Files\Python310\
    echo - %LOCALAPPDATA%\Programs\Python\Python310\
    echo.
    pause
)
