@echo off
REM ============================================================================
REM Quick Commit and Push Script for Windows
REM ============================================================================

echo.
echo ========================================
echo Git Commit and Push Tool
echo ========================================
echo.

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed or not in PATH
    pause
    exit /b 1
)

REM Show current status
echo Current status:
echo ----------------------------------------
git status
echo.

REM Get commit message from user
set /p commit_msg="Enter commit message: "

if "%commit_msg%"=="" (
    echo ERROR: Commit message cannot be empty
    pause
    exit /b 1
)

echo.
echo ========================================
echo Committing changes...
echo ========================================

REM Add all changes
git add .

REM Commit with message
git commit -m "%commit_msg%"

if %errorlevel% neq 0 (
    echo.
    echo WARNING: No changes to commit or commit failed
    echo.
)

echo.
echo ========================================
echo Pushing to GitHub...
echo ========================================

REM Push to main branch
git push origin main

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Push failed! Check your credentials and network connection.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ SUCCESS! Changes pushed to GitHub
echo ========================================
echo.
echo Next steps:
echo 1. SSH to production server: ssh aipenpaladm@54.160.147.118
echo 2. Run deployment script: ./deploy_update.sh
echo.
echo Or see CONTINUOUS_DEPLOYMENT_GUIDE.md for full instructions.
echo.

pause
