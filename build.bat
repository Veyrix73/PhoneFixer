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

python -m pip install --upgrade pip
if errorlevel 1 goto failed
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed

python -m PyInstaller --noconfirm --clean --onefile --windowed --name PhoneFixer --add-data "platform-tools;platform-tools" main.py
if errorlevel 1 goto failed

echo.
echo Build complete: dist\PhoneFixer.exe
echo.
pause
exit /b 0

:failed
echo.
echo Build failed. Check Python 3.10+, internet access, and the error above.
pause
exit /b 1
