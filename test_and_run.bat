@echo off
REM Test and run Streamlit app

echo ============================================================
echo Testing Streamlit App Components
echo ============================================================
echo.

python test_streamlit_agents.py

echo.
echo ============================================================
echo.
echo Press any key to start Streamlit app...
pause >nul

echo.
echo Starting Streamlit app...
streamlit run streamlit_app/app.py

