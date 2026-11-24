@echo off
cd /d "%~dp0"
python poco_cleaner.py
if errorlevel 1 pause
