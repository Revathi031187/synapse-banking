@echo off
cd %~dp0
py -3.10 utils\feature_scorer.py
if %errorlevel% neq 0 (
    python utils\feature_scorer.py
)
pause

