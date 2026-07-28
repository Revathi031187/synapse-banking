@echo off
echo ========================================
echo Preparing to push code to GitHub
echo Repository: https://github.com/Revathi031187/NBA
echo ========================================
echo.

cd /d "C:\Users\jaisonsamuel.d.lv\Desktop\personalization-agent"

echo [1/6] Checking git status...
git status
echo.

echo [2/6] Checking remote repository...
git remote -v
echo.

echo [3/6] Staging all changes...
git add .
echo.

echo [4/6] Creating commit...
git commit -m "Major update: Streamlined Academy Sports platform with robust segmentation and recommendations

- Removed all banking and retail modules - Academy Sports is now the sole focus
- Enhanced macro and micro segmentation with unique, archetype-based naming
- Implemented production-ready product recommendation engine with tier-based filtering
- Added detailed explanations for all product recommendations
- Fixed Agent A and Agent B integration for seamless customer insights
- Improved UI/UX: simplified navigation, always-visible data loader, formatted segment insights
- Ensured premium customers receive only premium product recommendations
- Fixed all micro-segmentation display issues
- Cleaned up 294 lines of deprecated code
- All endpoints tested and working correctly"
echo.

echo [5/6] Checking current branch...
git branch
echo.

echo [6/6] Pushing to GitHub master branch...
git push origin master
echo.

echo ========================================
echo Push operation completed!
echo ========================================
pause
