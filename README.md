# PhoneFixer

PhoneFixer is a Windows desktop controller for viewing and controlling an Android phone over USB.

**The old app-uninstaller has been removed.** PhoneFixer no longer lists apps or sends uninstall commands.

## What it does

- Detects Android phones connected through ADB.
- Shows the phone model, Android version, and battery level.
- Opens the live Android screen in a dedicated scrcpy window.
- Lets you use your PC mouse, scroll wheel, and keyboard to interact with the phone.
- Offers resolution, frame-rate, and bitrate settings.
- Can stop the screen-mirroring process from the PhoneFixer window.

The screen appears in a separate window opened by scrcpy. PhoneFixer is the connection and settings panel; scrcpy handles live video and input.

## Requirements

- Windows 10 or 11 (64-bit recommended).
- Python 3.10+ to run from source, or use the EXE build.
- The official Windows scrcpy release.
- A USB data cable.

## 1. Download scrcpy

Download the official Windows release from:

https://github.com/Genymobile/scrcpy/releases/latest

Extract the ZIP. Copy the contents of the extracted folder into the **scrcpy** folder beside **main.py**.

The folder should look like this:

    PhoneFixer/
      main.py
      run.bat
      build.bat
      scrcpy/
        scrcpy.exe
        adb.exe
        scrcpy-server
        SDL2.dll
        ...the other files from the release...

Do not download scrcpy from third-party download sites. The official project is maintained by Genymobile.

## 2. Enable USB debugging on Android

1. Open **Settings → About phone**.
2. Tap **OS version** several times to enable Developer options.
3. Open **Settings → Additional settings → Developer options**.
4. Enable **USB debugging**.
5. Connect the phone to the PC with a USB data cable and unlock the phone.
6. Approve the **Allow USB debugging?** prompt. Review the computer's RSA fingerprint before allowing it.

Menu names can vary between Android versions and phone manufacturers.

## 3. Run PhoneFixer

Double-click **run.bat**, or run:

    python main.py

Press **Refresh phone**, select the connected device, then press **Start phone screen**.

Use the scrcpy window to click, scroll, and type. The PhoneFixer window stays open for device selection and mirroring settings.

## Build a Windows EXE

1. Put the complete official scrcpy release contents in the **scrcpy** folder.
2. Run **build.bat**.
3. The executable will be created at **dist/PhoneFixer.exe**.

The build includes the scrcpy folder inside the EXE. The generated EXE can be moved to another Windows PC; the phone still needs USB debugging enabled and must approve that PC.

## Troubleshooting

- **No authorized phone found:** unlock the phone, reconnect the cable, and approve the USB debugging prompt.
- **Phone does not appear:** try another USB data cable or USB port. Some cables only charge.
- **scrcpy / ADB not installed:** check that **scrcpy.exe** and **adb.exe** are inside the project's scrcpy folder.
- **Screen opens and closes:** check the status message in PhoneFixer. Reconnect the phone and press Refresh phone.

## Safety and privacy

PhoneFixer uses Android Debug Bridge (ADB) and scrcpy. It does not root the phone, unlock the bootloader, flash firmware, or install a permanent control app. Android displays a USB debugging approval prompt before this computer can access the device. Disconnect the cable or revoke this computer's USB debugging authorization in Developer options to end that trust relationship.

The phone screen is shown locally on your PC. No PhoneFixer account or cloud service is used.
