# PhoneFixer / POCO Cleaner

A conservative Windows app manager for connected Android phones. It lists installed packages, shows third-party apps separately from protected system packages, supports search and bulk selection, and only allows bulk uninstall of third-party apps.

## Current app

- Windows desktop GUI built with Python and Tkinter.
- Connects over USB using Google's Android Debug Bridge (ADB).
- Displays app name, package ID, package category, and version code when available.
- System packages are locked and cannot be selected.
- Bulk uninstall uses `pm uninstall --user 0`; no root or bootloader unlock is required.

See the source and setup instructions in `poco_cleaner.py` and `README.md` as the project develops. Download Android Platform-Tools only from Google's official page: https://developer.android.com/tools/releases/platform-tools

**Safety:** Uninstalling apps can delete local app data. Only remove apps you recognize and no longer need. Start with one or two apps and check that the phone still works normally.