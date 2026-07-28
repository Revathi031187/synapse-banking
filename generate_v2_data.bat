@echo off
echo Generating Academy Sports V2 Dataset...
py -3.10 utils/generate_v2_data_simple.py
echo.
echo Done! Press any key to exit...
pause > nul

