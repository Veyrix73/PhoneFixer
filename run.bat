@echo off
setlocal
title PhoneFixer
cd /d "%~dp0"

if not exist "scrcpy\scrcpy.exe" (
  echo.
  echo PhoneFixer cannot find scrcpy.
  echo.
  echo 1. Download the official Windows ZIP from:
  echo    https://github.com/Genymobile/scrcpy/releases/latest
  echo 2. Extract the ZIP.
  echo 3. Copy ALL extracted files into this project's scrcpy folder.
  echo    The file scrcpy\scrcpy.exe must exist.
  echo.
  pause
  exit /b 1
)

pushd "%~dp0scrcpy"
echo Starting PhoneFixer...
echo Connect your Android phone and approve USB debugging if prompted.
echo.
scrcpy.exe --window-title="PhoneFixer" --max-size=1600 --max-fps=60 --video-bit-rate=8M --stay-awake --pause-on-exit=if-error
set "SCRCPY_EXIT=%ERRORLEVEL%"
popd

if not "%SCRCPY_EXIT%"=="0" (
  echo.
  echo PhoneFixer / scrcpy exited with code %SCRCPY_EXIT%.
  echo Check that USB debugging is enabled and the phone has approved this PC.
  echo.
  pause
)
exit /b %SCRCPY_EXIT%
