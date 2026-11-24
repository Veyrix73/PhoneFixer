@echo off
setlocal
cd /d "%~dp0"

if not exist "platform-tools\adb.exe" (
  echo.
  echo Missing platform-tools\adb.exe
  echo Download Google's Platform-Tools from:
  echo https://developer.android.com/tools/releases/platform-tools
  echo Extract the platform-tools folder beside main.py.
  echo.
  pause
  exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 goto failed

python main.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo PhoneFixer could not start. Check Python 3.10+ and the error above.
pause
exit /b 1
