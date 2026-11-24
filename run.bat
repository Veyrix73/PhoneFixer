@echo off
setlocal
cd /d "%~dp0"
python main.py
if errorlevel 1 (
  echo.
  echo PhoneFixer could not start. Make sure Python 3.10+ is installed.
  pause
)
