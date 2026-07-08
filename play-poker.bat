@echo off
cd /d "%~dp0"
python run_poker.py
if errorlevel 1 (
  echo.
  echo Python was not found. Install Python 3 from https://www.python.org/downloads/
  pause
)
