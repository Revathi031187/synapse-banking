@echo off
color 0A
echo.
echo ========================================
echo 🚀 BANKING PERSONALIZATION AGENT
echo ========================================
echo.
echo ✅ ChromaDB: Working (no torch needed)
echo ✅ Agent A: Customer Segmentation
echo ✅ Agent B: Product Recommendations
echo ✅ Macro/Micro: Beautiful Dashboards
echo ✅ Data Loader: 5,000 Customers
echo.
echo ========================================
echo QUICK START
echo ========================================
echo.
echo STEP 1: Start Backend
echo   Run this file or: START_BANKING.bat
echo.
echo STEP 2: Start Frontend (in new terminal)
echo   cd frontend
echo   npm run dev
echo.
echo STEP 3: Open Browser
echo   http://localhost:5173/banking/agent-a
echo.
echo ========================================
echo.

pause

echo.
echo Starting Backend Server...
echo.

call venv\Scripts\activate.bat
python api/main_unified_chromadb.py
