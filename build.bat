@echo off
setlocal
cd /d "%~dp0"

if not exist "scrcpy\scrcpy.exe" (
  echo.
  echo Missing scrcpy\scrcpy.exe
  echo Download the official Windows ZIP from:
  echo https://github.com/Genymobile/scrcpy/releases/latest
  echo Extract the ZIP contents into the project's scrcpy folder, then run build.bat again.
  echo.
  pause
  exit /b 1
)

python -m pip install --upgrade pyinstaller
if errorlevel 1 goto failed

python -m PyInstaller --noconfirm --clean --onefile --windowed --name PhoneFixer --add-data "scrcpy;scrcpy" main.py
if errorlevel 1 goto failed

echo.
echo Build complete: dist\PhoneFixer.exe
echo.
pause
exit /b 0

:failed
echo.
echo Build failed. Check Python and internet access, then try again.
pause
exit /b 1
