# PhoneFixer

A conservative Windows app manager for a connected POCO / Android phone.

## Features

- Scans installed packages and displays them in a searchable list.
- Shows a friendly name for common apps plus the exact package ID.
- Displays package category and version code when Android reports it.
- Selects multiple third-party apps with checkboxes.
- Bulk-uninstalls selected third-party apps.
- Optionally shows protected system packages as locked, non-selectable rows.
- Shows the connected device model, Android version, MIUI/HyperOS version (when reported), and battery percentage.

## Safety

Only packages reported by Android's `pm list packages -3` are selectable. All other packages are marked as protected system apps and cannot be selected. The uninstall function checks this allow-list again before sending commands.

The app uses `pm uninstall --user 0`. It does not root the phone, unlock the bootloader, flash firmware, or modify partitions. Uninstalling an app can delete its local data. Only remove apps you recognize and no longer need; start with one or two and check that the phone still works normally.

## Requirements

- Windows 10 or 11
- Python 3.10+ (to run from source or build the EXE)
- Google's Android SDK Platform-Tools (ADB)
- USB data cable

Download Platform-Tools from Google's official page:  
https://developer.android.com/tools/releases/platform-tools

## Connect your POCO

1. On the phone, open **Settings → About phone** and tap **OS version** several times to enable Developer options.
2. Open **Settings → Additional settings → Developer options**.
3. Enable **USB debugging**.
4. Connect the phone to the PC and unlock it.
5. Accept the **Allow USB debugging?** prompt on the phone.
6. Extract Google's Platform-Tools into this project folder as `platform-tools` (so `platform-tools/adb.exe` exists), or add the Platform-Tools folder to Windows `PATH`.
7. Run `run_poco_cleaner.bat` or use `python poco_cleaner.py`.

## Build a Windows EXE

Run `build_exe.bat`. It installs PyInstaller and creates `dist\\PhoneFixer.exe`.

For a portable EXE with ADB bundled, put the official Platform-Tools folder in this project as `platform-tools` before running the build script. Otherwise, the EXE will look for ADB on Windows `PATH`.

## App names

Android's basic package-list command provides package IDs, not localized display labels. PhoneFixer maps common package IDs to familiar names and always shows the exact package ID. Unknown package names are shown in a readable form rather than pretending to know the official app title.
