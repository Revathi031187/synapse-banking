@echo off
echo ================================================================================
echo   RESTART WITH ENHANCED AI EXPLANATIONS
echo ================================================================================
echo.
echo ENHANCEMENTS ADDED:
echo   1. Data-driven explanations (actual factor scores)
echo   2. Persona-specific reasoning
echo   3. Position-specific context (#1 vs #2 vs #3)
echo   4. Multi-section formatting
echo   5. Product-specific benefits
echo   6. Comparison context (why this rank)
echo   7. Beautiful gradient formatting
echo.
echo EXAMPLE OUTPUT:
echo   "🥇 #1 Recommended | 69.8% compatibility
echo    Exceptional alignment with Household Savers
echo.
echo    Why for Household Savers:
echo    ✅ Eligibility 88%%: Strongly qualify
echo    🎯 Need Match 75%%: Perfect alignment  
echo    💎 Value 11.4%%: No fee, 5.75%% APY
echo.
echo    Key Benefits:
echo    💰 Earns 5.75%% APY
echo    🔓 No minimum balance
echo.
echo    Why #1? Scores 0.8%% higher than #2"
echo.
echo Press any key to restart backend...
pause > nul

echo.
echo Starting backend with enhanced explanations...
echo.

py -3.10 api/main_unified_chromadb.py

pause
