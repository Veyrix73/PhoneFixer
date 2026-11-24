@echo off
setlocal
cd /d "%~dp0"

python -m pip install --upgrade pyinstaller
if errorlevel 1 goto failed

if exist "platform-tools\adb.exe" (
  python -m PyInstaller --noconfirm --clean --onefile --windowed --name PhoneFixer --add-binary "platform-tools\adb.exe;platform-tools" --add-binary "platform-tools\AdbWinApi.dll;platform-tools" --add-binary "platform-tools\AdbWinUsbApi.dll;platform-tools" poco_cleaner.py
) else (
  python -m PyInstaller --noconfirm --clean --onefile --windowed --name PhoneFixer poco_cleaner.py
)
if errorlevel 1 goto failed

echo.
echo Build complete: dist\PhoneFixer.exe
echo.
pause
exit /b 0

:failed
echo.
echo Build failed. Check that Python 3.10+ is installed and available as python.
pause
exit /b 1
