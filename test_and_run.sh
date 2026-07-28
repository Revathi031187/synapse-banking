#!/bin/bash
# Test and run Streamlit app

echo "============================================================"
echo "Testing Streamlit App Components"
echo "============================================================"
echo

python test_streamlit_agents.py

echo
echo "============================================================"
echo
read -p "Press Enter to start Streamlit app..."

echo
echo "Starting Streamlit app..."
streamlit run streamlit_app/app.py

