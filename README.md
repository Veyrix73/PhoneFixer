# PhoneFixer

PhoneFixer is a Windows desktop controller for viewing and interacting with an Android phone over USB. It uses **ADB only**: no scrcpy, no screen-mirroring APK, and no permanent app installed on the phone.

## Features

- Detects connected Android phones and shows model, Android version, and battery level.
- Shows the phone screen inside the PhoneFixer window using repeated ADB screenshots.
- Click the preview to tap the phone; click and drag to swipe.
- Use the mouse wheel to scroll.
- Send text from the PC keyboard using the text field.
- Back, Home, Recent Apps, and volume controls.
- Selectable preview refresh rate.

## Important performance note

This is a simple ADB screenshot preview, not a low-latency video stream. Expect a few screen updates per second, depending on the phone and USB connection. It does not stream phone audio. For smoother video and lower latency, a dedicated screen-streaming implementation is needed.

## Requirements

- Windows 10 or 11.
- Python 3.10+ to run from source, or use the EXE build.
- Google's official Android SDK Platform-Tools (ADB).
- A USB data cable.
- Pillow (installed by the setup/build scripts).

## 1. Download ADB Platform-Tools

Download Google's official Platform-Tools:

https://developer.android.com/tools/releases/platform-tools

Extract the ZIP. Copy the extracted **platform-tools** folder into this project, next to **main.py**. Check that this file exists:

    PhoneFixer/
      main.py
      run.bat
      build.bat
      requirements.txt
      platform-tools/
        adb.exe
        AdbWinApi.dll
        AdbWinUsbApi.dll
        ...

Do not rename adb.exe. Keep the DLL files and other Platform-Tools files together.

## 2. Enable USB debugging

1. On the phone, open **Settings → About phone**.
2. Tap **OS version** several times to enable Developer options.
3. Open **Settings → Additional settings → Developer options**.
4. Enable **USB debugging**.
5. Connect the phone to the PC with a USB data cable and unlock it.
6. Approve the **Allow USB debugging?** prompt on the phone.

The exact menu names can vary by Android version and phone manufacturer. Only approve a computer you trust.

## 3. Run PhoneFixer

Double-click **run.bat**. On first run it installs the Pillow image library if needed.

Or run these commands from the project folder:

    python -m pip install -r requirements.txt
    python main.py

Press **Refresh phone**, select the device, and click **Start live preview**. Click or drag on the displayed phone screen to tap or swipe. Use the text field to send text.

## Build a Windows EXE

1. Put Google's complete Platform-Tools folder beside main.py as **platform-tools**.
2. Run **build.bat**.
3. The EXE will be created at **dist/PhoneFixer.exe**.

The EXE bundles ADB and the required Platform-Tools files. You do not need to install scrcpy.

## Troubleshooting

- **No authorized phone found:** unlock the phone and approve the USB debugging prompt.
- **Phone does not appear:** try a different USB data cable or port. Some cables only charge.
- **ADB missing:** check that **platform-tools/adb.exe** exists.
- **Preview is slow:** lower the preview rate in the controls. Screenshot-based preview is intentionally simpler but less fluid than a video stream.
- **Controls do not work:** keep the phone unlocked and check that USB debugging authorization is still active.

## Privacy and safety

PhoneFixer communicates with the phone over the locally connected ADB interface. It does not root the phone, unlock its bootloader, flash firmware, install an APK, or use a cloud relay. The first USB debugging connection requires approval on the phone. You can revoke this computer's authorization in Android Developer options.
