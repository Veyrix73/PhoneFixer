from __future__ import annotations

import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

APP_NAME = "PhoneFixer"
VERSION = "3.0"

BG = "#111820"
PANEL = "#1b2632"
PANEL_ALT = "#243241"
TEXT = "#edf2f7"
MUTED = "#a9b7c6"
ACCENT = "#61a6e8"
AMBER = "#e8bd69"


def app_roots() -> list[Path]:
    roots: list[Path] = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        roots.append(Path(sys._MEIPASS))  # type: ignore[attr-defined]
    roots.extend([Path(__file__).resolve().parent, Path(sys.executable).resolve().parent])
    result: list[Path] = []
    for root in roots:
        if root not in result:
            result.append(root)
    return result


def find_scrcpy() -> Path | None:
    for root in app_roots():
        for candidate in (root / "scrcpy" / "scrcpy.exe", root / "scrcpy.exe"):
            if candidate.is_file():
                return candidate
    found = shutil.which("scrcpy")
    return Path(found).resolve() if found else None


def find_adb(scrcpy_path: Path | None) -> Path | None:
    candidates: list[Path] = []
    if scrcpy_path:
        candidates.extend([
            scrcpy_path.parent / "adb.exe",
            scrcpy_path.parent / "platform-tools" / "adb.exe",
        ])
    for root in app_roots():
        candidates.extend([
            root / "scrcpy" / "adb.exe",
            root / "platform-tools" / "adb.exe",
            root / "adb.exe",
        ])
    for path in candidates:
        if path.is_file():
            return path
    found = shutil.which("adb") or shutil.which("adb.exe")
    return Path(found).resolve() if found else None


class PhoneFixer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("900x650")
        self.minsize(760, 560)
        self.configure(bg=BG)

        self.scrcpy_path = find_scrcpy()
        self.adb_path = find_adb(self.scrcpy_path)
        self.devices: dict[str, dict[str, str]] = {}
        self.device_labels: dict[str, str] = {}
        self.mirror_process: subprocess.Popen[str] | None = None
        self.mirror_log: list[str] = []
        self.refreshing = False

        self.device_var = tk.StringVar(value="Searching for phone…")
        self.status_var = tk.StringVar(value="Connect your Android phone using USB.")
        self.detail_var = tk.StringVar(value="No device selected")
        self.max_size_var = tk.StringVar(value="1600")
        self.fps_var = tk.StringVar(value="60")
        self.bitrate_var = tk.StringVar(value="8M")
        self.stay_awake_var = tk.BooleanVar(value=True)
        self.mirror_state_var = tk.StringVar(value="SCREEN NOT RUNNING")

        self._setup_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(250, self.refresh_devices)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview", background=PANEL, fieldbackground=PANEL,
            foreground=TEXT, rowheight=30, borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.configure(
            "TCombobox", fieldbackground=PANEL_ALT, background=PANEL_ALT,
            foreground=TEXT, arrowcolor=TEXT, padding=7,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", PANEL_ALT)],
            foreground=[("readonly", TEXT)],
        )

    def _button(self, parent: tk.Widget, label: str, command: Any, primary: bool = False) -> tk.Button:
        color = "#286eaa" if primary else PANEL_ALT
        active = "#347fbf" if primary else "#304457"
        return tk.Button(
            parent, text=label, command=command, bg=color, fg=TEXT,
            activebackground=active, activeforeground=TEXT, relief="flat",
            bd=0, padx=15, pady=10, font=("Segoe UI", 9, "bold"), cursor="hand2",
        )

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=24, pady=(22, 16))

        logo = tk.Canvas(header, width=56, height=56, bg=BG, highlightthickness=0)
        logo.pack(side="left", padx=(0, 14))
        logo.create_rectangle(3, 3, 53, 53, fill=PANEL_ALT, outline="#52718d", width=2)
        logo.create_rectangle(18, 8, 38, 46, fill=BG, outline="#91c9f5", width=2)
        logo.create_rectangle(21, 13, 35, 38, fill="#294760", outline="")
        logo.create_oval(26, 40, 30, 44, fill="#91c9f5", outline="")

        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_box, text="PhoneFixer", bg=BG, fg=TEXT,
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box, text="See and control your Android phone from Windows.",
            bg=BG, fg=MUTED, font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))
        self._button(header, "Refresh phone", self.refresh_devices).pack(side="right")

        device_card = tk.Frame(self, bg=PANEL, padx=17, pady=15)
        device_card.pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(
            device_card, text="ANDROID DEVICE", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        row = tk.Frame(device_card, bg=PANEL)
        row.pack(fill="x", pady=(6, 2))
        self.device_combo = ttk.Combobox(
            row, textvariable=self.device_var, state="readonly", width=48,
        )
        self.device_combo.pack(side="left", fill="x", expand=True)
        self.device_combo.bind("<<ComboboxSelected>>", self._device_selected)
        tk.Label(
            row, textvariable=self.mirror_state_var, bg=PANEL, fg=AMBER,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="right", padx=(12, 0))
        tk.Label(
            device_card, textvariable=self.detail_var, bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(5, 0))

        mirror_card = tk.Frame(self, bg=PANEL, padx=18, pady=17)
        mirror_card.pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(
            mirror_card, text="PHONE SCREEN", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")
        tk.Label(
            mirror_card,
            text="Open the live screen in a separate window. Click, scroll and type in that window to control your phone.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=800,
            justify="left",
        ).pack(anchor="w", pady=(5, 13))

        settings = tk.Frame(mirror_card, bg=PANEL)
        settings.pack(fill="x", pady=(0, 14))
        self._setting(settings, "Resolution limit", self.max_size_var, ("Original", "1024", "1280", "1600", "1920"), 0)
        self._setting(settings, "Frame rate", self.fps_var, ("30", "60", "90", "120"), 1)
        self._setting(settings, "Video bitrate", self.bitrate_var, ("4M", "8M", "12M", "16M"), 2)

        tk.Checkbutton(
            mirror_card, text="Keep phone awake while mirroring",
            variable=self.stay_awake_var, bg=PANEL, fg=MUTED,
            activebackground=PANEL, activeforeground=TEXT,
            selectcolor=PANEL_ALT, font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 12))

        buttons = tk.Frame(mirror_card, bg=PANEL)
        buttons.pack(fill="x")
        self.start_button = self._button(buttons, "Start phone screen", self.start_mirror, True)
        self.start_button.pack(side="left")
        self.stop_button = self._button(buttons, "Stop screen", self.stop_mirror)
        self.stop_button.pack(side="left", padx=(8, 0))
        self.stop_button.configure(state="disabled")

        help_card = tk.Frame(self, bg=PANEL, padx=18, pady=15)
        help_card.pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(
            help_card, text="FIRST-TIME SETUP", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        tk.Label(
            help_card,
            text="1. Enable Developer options and USB debugging on your phone.\n"
                 "2. Connect it with a USB data cable and approve the USB debugging prompt.\n"
                 "3. Put the official scrcpy Windows files in the project's scrcpy folder.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9), justify="left",
        ).pack(anchor="w", pady=(6, 8))
        link = tk.Label(
            help_card, text="Open official scrcpy download page",
            bg=PANEL, fg=ACCENT, cursor="hand2",
            font=("Segoe UI", 9, "underline"),
        )
        link.pack(anchor="w")
        link.bind("<Button-1>", lambda _event: self._open_scrcpy_page())

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(
            footer, textvariable=self.status_var, bg=BG, fg=MUTED,
            font=("Segoe UI", 9), anchor="w", wraplength=820, justify="left",
        ).pack(fill="x")

    def _setting(
        self, parent: tk.Widget, label: str, variable: tk.StringVar,
        values: tuple[str, ...], column: int,
    ) -> None:
        cell = tk.Frame(parent, bg=PANEL)
        cell.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 12, 0))
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(
            cell, text=label, bg=PANEL, fg=MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(0, 5))
        ttk.Combobox(
            cell, textvariable=variable, values=values, state="readonly",
        ).pack(fill="x")

    def _open_scrcpy_page(self) -> None:
        import webbrowser
        webbrowser.open("https://github.com/Genymobile/scrcpy/releases/latest")

    def _adb_command(self, args: list[str], serial: str | None = None, timeout: int = 15) -> str:
        if not self.adb_path:
            raise RuntimeError("ADB was not found. Put the official scrcpy files in the scrcpy folder.")
        command = [str(self.adb_path)]
        if serial:
            command.extend(["-s", serial])
        command.extend(args)
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "ADB command failed").strip())
        return result.stdout.strip()

    def refresh_devices(self) -> None:
        if self.refreshing:
            return
        if not self.scrcpy_path or not self.adb_path:
            self.status_var.set(
                "Setup needed: download the official scrcpy Windows ZIP and extract its contents into this project's scrcpy folder."
            )
            self.device_var.set("scrcpy / ADB not installed")
            self.device_combo.configure(values=["scrcpy / ADB not installed"])
            self.detail_var.set("Use the official download link below, then press Refresh phone.")
            return
        self.refreshing = True
        self.status_var.set("Checking USB connection…")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self) -> None:
        try:
            self._adb_command(["start-server"], timeout=20)
            output = self._adb_command(["devices", "-l"], timeout=15)
            found: dict[str, dict[str, str]] = {}
            waiting: list[str] = []
            for line in output.splitlines()[1:]:
                parts = line.split()
                if len(parts) < 2:
                    continue
                serial, state = parts[0], parts[1]
                if state != "device":
                    waiting.append(f"{serial} ({state})")
                    continue
                props: dict[str, str] = {}
                for key in ("ro.product.manufacturer", "ro.product.model", "ro.build.version.release"):
                    try:
                        props[key] = self._adb_command(["shell", "getprop", key], serial, 8).strip()
                    except Exception:
                        props[key] = ""
                try:
                    battery_text = self._adb_command(["shell", "dumpsys", "battery"], serial, 8)
                    match = re.search(r"level:\s*(\d+)", battery_text)
                    battery = f"{match.group(1)}%" if match else "Unknown battery"
                except Exception:
                    battery = "Unknown battery"
                model = " ".join(
                    x for x in (props.get("ro.product.manufacturer"), props.get("ro.product.model")) if x
                )
                found[serial] = {
                    "model": model or "Android device",
                    "android": props.get("ro.build.version.release") or "?",
                    "battery": battery,
                }
            self.after(0, lambda: self._refresh_done(found, waiting, None))
        except Exception as exc:
            self.after(0, lambda error=str(exc): self._refresh_done({}, [], error))

    def _refresh_done(
        self, found: dict[str, dict[str, str]], waiting: list[str], error: str | None,
    ) -> None:
        self.refreshing = False
        self.devices = found
        self.device_labels = {}
        labels: list[str] = []
        for serial, info in found.items():
            label = f"{info['model']}  •  {serial}"
            self.device_labels[label] = serial
            labels.append(label)
        if labels:
            self.device_combo.configure(values=labels)
            self.device_var.set(labels[0])
            self._device_selected()
            self.status_var.set(f"Phone connected. {len(labels)} device(s) ready.")
        else:
            message = "No authorized Android phone found."
            if waiting:
                message += " Waiting for approval: " + ", ".join(waiting)
            if error:
                message = "Connection check failed: " + error
            self.device_combo.configure(values=[message])
            self.device_var.set(message)
            self.detail_var.set("Unlock the phone and approve the USB debugging prompt.")
            self.status_var.set(message)

    def _device_selected(self, _event: Any = None) -> None:
        serial = self.device_labels.get(self.device_var.get())
        if not serial:
            return
        info = self.devices.get(serial, {})
        self.detail_var.set(
            f"Android {info.get('android', '?')}   •   Battery {info.get('battery', '?')}   •   USB debugging"
        )

    def start_mirror(self) -> None:
        if self.mirror_process and self.mirror_process.poll() is None:
            self.status_var.set("The phone screen is already running.")
            return
        serial = self.device_labels.get(self.device_var.get())
        if not serial:
            messagebox.showwarning("No phone selected", "Connect and select an authorized Android phone first.")
            return
        if not self.scrcpy_path or not self.scrcpy_path.is_file():
            messagebox.showerror("scrcpy missing", "Put the official scrcpy files in the project's scrcpy folder.")
            return

        args = [
            str(self.scrcpy_path),
            "--serial", serial,
            "--window-title", f"PhoneFixer - {self.devices.get(serial, {}).get('model', 'Android')}",
            "--video-bit-rate", self.bitrate_var.get(),
        ]
        if self.max_size_var.get() != "Original":
            args.extend(["--max-size", self.max_size_var.get()])
        args.extend(["--max-fps", self.fps_var.get()])
        if self.stay_awake_var.get():
            args.append("--stay-awake")

        try:
            self.mirror_log = []
            self.mirror_process = subprocess.Popen(
                args, cwd=str(self.scrcpy_path.parent),
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as exc:
            messagebox.showerror("Could not start screen", str(exc))
            return

        self.mirror_state_var.set("STARTING SCREEN…")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Starting screen mirror. Use your mouse and keyboard in the phone window.")
        threading.Thread(
            target=self._read_mirror_output, args=(self.mirror_process,), daemon=True,
        ).start()
        self.after(700, self._poll_mirror)

    def _read_mirror_output(self, process: subprocess.Popen[str]) -> None:
        stream = process.stdout
        if stream is None:
            return
        try:
            for line in stream:
                cleaned = line.strip()
                if cleaned:
                    self.mirror_log.append(cleaned)
                    if len(self.mirror_log) > 35:
                        del self.mirror_log[:10]
        except Exception:
            pass

    def _poll_mirror(self) -> None:
        process = self.mirror_process
        if process is None:
            return
        code = process.poll()
        if code is None:
            self.mirror_state_var.set("SCREEN RUNNING")
            self.after(700, self._poll_mirror)
            return
        self.mirror_process = None
        self.mirror_state_var.set("SCREEN NOT RUNNING")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        if code == 0:
            self.status_var.set("Phone screen closed.")
        else:
            detail = " | ".join(self.mirror_log[-4:])
            message = f"scrcpy closed with exit code {code}."
            if detail:
                message += " " + detail
            self.status_var.set(message)
            messagebox.showwarning("Screen mirror stopped", message)

    def stop_mirror(self) -> None:
        process = self.mirror_process
        if not process or process.poll() is not None:
            self.mirror_process = None
            self.mirror_state_var.set("SCREEN NOT RUNNING")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            return
        try:
            process.terminate()
        except Exception:
            pass
        self.status_var.set("Closing phone screen…")
        self.after(500, self._poll_mirror)

    def _on_close(self) -> None:
        process = self.mirror_process
        if process and process.poll() is None:
            try:
                process.terminate()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    PhoneFixer().mainloop()
