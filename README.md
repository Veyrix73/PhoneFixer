# PhoneFixer

PhoneFixer is a lightweight Windows launcher for **scrcpy**. It opens your Android phone screen on your PC so you can control it with your mouse and keyboard.

There is no Python requirement, no APK to install on the phone, and no root access required.

## Features

- Live Android screen mirrored in a desktop window.
- Mouse clicks and drags control taps and swipes.
- PC keyboard input.
- Scroll with the mouse wheel.
- Uses USB debugging over a USB cable.
- Keeps the phone awake while connected.
- Uses scrcpy UHID mode for mouse and keyboard, simulating physical input devices instead of Android API-level input injection.

## 1. Download PhoneFixer

Download this repository using **Code → Download ZIP**, then extract it.

## 2. Download the official scrcpy Windows release

Download the latest Windows 64-bit ZIP from the official scrcpy project:

https://github.com/Genymobile/scrcpy/releases/latest

The official Windows instructions and release files are maintained by Genymobile. Do not download scrcpy from unofficial websites.

Extract the ZIP. Copy the contents of the extracted release folder into the **scrcpy** folder inside PhoneFixer.

Your folder should look like this:

    PhoneFixer/
      README.md
      run.bat
      scrcpy/
        scrcpy.exe
        adb.exe
        scrcpy-server
        SDL2.dll
        ...other files from the official ZIP...

Keep the files from the official ZIP together. Do not copy only scrcpy.exe.

## 3. Enable USB debugging on Android

1. Open **Settings → About phone**.
2. Tap **OS version** several times to enable Developer options.
3. Open **Settings → Additional settings → Developer options**.
4. Enable **USB debugging**.
5. Connect the phone to your PC using a USB data cable and unlock it.
6. Approve the **Allow USB debugging?** prompt on the phone. Only approve a computer you trust.

Menu names can vary depending on your Android version and phone manufacturer.

## 4. Start PhoneFixer

Double-click **run.bat**.

The phone screen will open in its own window. The launcher enables scrcpy UHID mode to simulate a physical mouse and keyboard, which may work on some Xiaomi/POCO devices where ordinary input injection is blocked. Use your mouse to tap, drag, and scroll; type with your PC keyboard. If UHID is unsupported by your phone firmware, the terminal will show an error.

If Windows asks whether to allow the connection, check that the program is the official scrcpy download you installed.

## Troubleshooting

- **Phone not detected:** unlock it, reconnect the cable, and approve the USB debugging prompt.
- **Only charging:** use a USB data cable and try another USB port.
- **Window closes with an error:** run **run.bat** again and read the message in the terminal.
- **Mouse or keyboard input is blocked:** on some Xiaomi/POCO devices, Android may require enabling the additional **USB debugging (Security settings)** option in Developer options. Only change this setting if you understand and trust the PC connection.

## About scrcpy

scrcpy is the screen mirroring and control engine. It streams the phone display to your PC and forwards mouse and keyboard input. It does not require root or a permanently installed Android app.

Official project: https://github.com/Genymobile/scrcpy
