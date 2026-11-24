from __future__ import annotations

import io
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from PIL import Image, ImageTk

APP_NAME = "PhoneFixer"
VERSION = "4.0"
BG = "#111820"
PANEL = "#1b2632"
PANEL_ALT = "#243241"
TEXT = "#edf2f7"
MUTED = "#a9b7c6"
ACCENT = "#61a6e8"
GREEN = "#63c69b"
AMBER = "#e8bd69"


def app_roots() -> list[Path]:
    roots: list[Path] = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        roots.append(Path(sys._MEIPASS))  # type: ignore[attr-defined]
    roots.extend((Path(__file__).resolve().parent, Path(sys.executable).resolve().parent))
    unique: list[Path] = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def find_adb() -> Path | None:
    for root in app_roots():
        candidate = root / "platform-tools" / "adb.exe"
        if candidate.is_file():
            return candidate
    found = shutil.which("adb") or shutil.which("adb.exe")
    return Path(found).resolve() if found else None


class PhoneFixer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("1120x820")
        self.minsize(900, 680)
        self.configure(bg=BG)

        self.adb_path = find_adb()
        self.devices: dict[str, dict[str, str]] = {}
        self.device_labels: dict[str, str] = {}
        self.selected_serial: str | None = None
        self.refreshing = False
        self.preview_running = False
        self.capture_busy = False
        self.last_image: Image.Image | None = None
        self.photo: ImageTk.PhotoImage | None = None
        self.image_bounds = (0, 0, 0, 0)
        self.press_point: tuple[int, int] | None = None
        self.press_time = 0.0
        self.capture_interval_ms = 350

        self.device_var = tk.StringVar(value="Checking for Android phone…")
        self.status_var = tk.StringVar(value="Connect your Android phone with a USB data cable.")
        self.detail_var = tk.StringVar(value="No device selected")
        self.capture_rate_var = tk.StringVar(value="3 FPS")
        self.text_var = tk.StringVar()
        self.preview_state_var = tk.StringVar(value="PREVIEW PAUSED")

        self._setup_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(300, self.refresh_devices)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
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
        hover = "#347fbf" if primary else "#304457"
        return tk.Button(
            parent, text=label, command=command, bg=color, fg=TEXT,
            activebackground=hover, activeforeground=TEXT, relief="flat",
            bd=0, padx=13, pady=9, font=("Segoe UI", 9, "bold"), cursor="hand2",
        )

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=22, pady=(18, 12))

        logo = tk.Canvas(header, width=52, height=52, bg=BG, highlightthickness=0)
        logo.pack(side="left", padx=(0, 12))
        logo.create_rectangle(3, 3, 49, 49, fill=PANEL_ALT, outline="#52718d", width=2)
        logo.create_rectangle(17, 8, 35, 44, fill=BG, outline="#91c9f5", width=2)
        logo.create_rectangle(20, 13, 32, 37, fill="#294760", outline="")
        logo.create_oval(24, 39, 28, 43, fill="#91c9f5", outline="")

        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_box, text="PhoneFixer", bg=BG, fg=TEXT,
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box, text="Android screen + mouse control, built with ADB only.",
            bg=BG, fg=MUTED, font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))
        self._button(header, "Refresh phone", self.refresh_devices).pack(side="right")

        device_card = tk.Frame(self, bg=PANEL, padx=15, pady=12)
        device_card.pack(fill="x", padx=22, pady=(0, 12))
        tk.Label(
            device_card, text="CONNECTED ANDROID DEVICE",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        row = tk.Frame(device_card, bg=PANEL)
        row.pack(fill="x", pady=(5, 2))
        self.device_combo = ttk.Combobox(
            row, textvariable=self.device_var, state="readonly", width=55,
        )
        self.device_combo.pack(side="left", fill="x", expand=True)
        self.device_combo.bind("<<ComboboxSelected>>", self._device_selected)
        tk.Label(
            row, textvariable=self.preview_state_var, bg=PANEL, fg=AMBER,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="right", padx=(10, 0))
        tk.Label(
            device_card, textvariable=self.detail_var, bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 12))

        screen_card = tk.Frame(body, bg=PANEL, padx=12, pady=12)
        screen_card.pack(side="left", fill="both", expand=True)
        screen_header = tk.Frame(screen_card, bg=PANEL)
        screen_header.pack(fill="x", pady=(0, 8))
        tk.Label(
            screen_header, text="PHONE SCREEN", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left")
        tk.Label(
            screen_header, text="Click and drag to touch / swipe",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 8),
        ).pack(side="right")

        self.screen_canvas = tk.Canvas(
            screen_card, bg="#080c10", highlightthickness=1,
            highlightbackground="#334454", cursor="crosshair",
        )
        self.screen_canvas.pack(fill="both", expand=True)
        self.screen_canvas.bind("<ButtonPress-1>", self._screen_press)
        self.screen_canvas.bind("<ButtonRelease-1>", self._screen_release)
        self.screen_canvas.bind("<MouseWheel>", self._mouse_wheel)
        self.screen_canvas.bind("<Configure>", lambda _event: self._render_image())

        controls = tk.Frame(body, bg=PANEL, width=300, padx=14, pady=14)
        controls.pack(side="right", fill="y", padx=(12, 0))
        controls.pack_propagate(False)

        tk.Label(
            controls, text="CONTROLS", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        tk.Label(
            controls,
            text="This preview uses repeated ADB screenshots. It is lighter to set up than a dedicated streaming server, but refreshes more slowly.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 8),
            wraplength=265, justify="left",
        ).pack(anchor="w", pady=(5, 12))

        self.start_button = self._button(controls, "Start live preview", self.start_preview, True)
        self.start_button.pack(fill="x")
        self.stop_button = self._button(controls, "Pause preview", self.pause_preview)
        self.stop_button.pack(fill="x", pady=(7, 13))
        self.stop_button.configure(state="disabled")

        tk.Label(
            controls, text="NAVIGATION", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        nav = tk.Frame(controls, bg=PANEL)
        nav.pack(fill="x")
        self._button(nav, "Back", lambda: self._send_keyevent(4)).pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._button(nav, "Home", lambda: self._send_keyevent(3)).pack(side="left", expand=True, fill="x", padx=4)
        self._button(nav, "Recent", lambda: self._send_keyevent(187)).pack(side="left", expand=True, fill="x", padx=(4, 0))

        volume = tk.Frame(controls, bg=PANEL)
        volume.pack(fill="x", pady=(7, 14))
        self._button(volume, "Vol −", lambda: self._send_keyevent(25)).pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._button(volume, "Vol +", lambda: self._send_keyevent(24)).pack(side="left", expand=True, fill="x", padx=(4, 0))

        tk.Label(
            controls, text="TYPE TEXT", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        text_entry = tk.Entry(
            controls, textvariable=self.text_var, bg=PANEL_ALT, fg=TEXT,
            insertbackground=TEXT, relief="flat", font=("Segoe UI", 9),
        )
        text_entry.pack(fill="x", ipady=8)
        text_entry.bind("<Return>", lambda _event: self.send_text())
        self._button(controls, "Send to phone", self.send_text, True).pack(fill="x", pady=(7, 14))

        tk.Label(
            controls, text="PREVIEW SPEED", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        speed = ttk.Combobox(
            controls, textvariable=self.capture_rate_var,
            values=("1 FPS", "2 FPS", "3 FPS", "4 FPS"),
            state="readonly",
        )
        speed.pack(fill="x")
        speed.bind("<<ComboboxSelected>>", self._speed_changed)

        tk.Label(
            controls,
            text="No screen-mirroring app is installed on the phone. USB debugging must be enabled and approved.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 8),
            wraplength=265, justify="left",
        ).pack(anchor="w", pady=(14, 0))

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=22, pady=(0, 13))
        tk.Label(
            footer, textvariable=self.status_var, bg=BG, fg=MUTED,
            font=("Segoe UI", 9), anchor="w", wraplength=1050, justify="left",
        ).pack(fill="x")

    def _speed_changed(self, _event: Any = None) -> None:
        try:
            fps = int(self.capture_rate_var.get().split()[0])
            self.capture_interval_ms = max(200, int(1000 / fps))
        except (ValueError, IndexError):
            self.capture_interval_ms = 350

    def _adb_command(
        self, args: list[str], serial: str | None = None, timeout: int = 12,
    ) -> bytes:
        if not self.adb_path or not self.adb_path.is_file():
            raise RuntimeError(
                "ADB was not found. Put Google's Platform-Tools in the platform-tools folder."
            )
        command = [str(self.adb_path)]
        if serial:
            command.extend(["-s", serial])
        command.extend(args)
        result = subprocess.run(
            command, capture_output=True, timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or b"ADB command failed").decode(
                "utf-8", errors="replace",
            ).strip()
            raise RuntimeError(message)
        return result.stdout

    def refresh_devices(self) -> None:
        if self.refreshing:
            return
        if not self.adb_path or not self.adb_path.is_file():
            self.status_var.set(
                "ADB missing: download Google's Platform-Tools and extract them into this project's platform-tools folder."
            )
            self.device_var.set("Platform-Tools not installed")
            self.device_combo.configure(values=["Platform-Tools not installed"])
            self.detail_var.set("Use the official Platform-Tools download link in the README.")
            return
        self.refreshing = True
        self.status_var.set("Checking USB connection…")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self) -> None:
        try:
            self._adb_command(["start-server"], timeout=20)
            raw = self._adb_command(["devices", "-l"], timeout=15)
            output = raw.decode("utf-8", errors="replace")
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
                        props[key] = self._adb_command(
                            ["shell", "getprop", key], serial, 8,
                        ).decode("utf-8", errors="replace").strip()
                    except Exception:
                        props[key] = ""
                try:
                    battery_output = self._adb_command(
                        ["shell", "dumpsys", "battery"], serial, 8,
                    ).decode("utf-8", errors="replace")
                    match = re.search(r"level:\s*(\d+)", battery_output)
                    battery = f"{match.group(1)}%" if match else "Unknown"
                except Exception:
                    battery = "Unknown"
                model = " ".join(
                    value for value in (props.get("ro.product.manufacturer"), props.get("ro.product.model"))
                    if value
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
            if self.device_var.get() not in self.device_labels:
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
            self.detail_var.set("Unlock your phone and approve the USB debugging prompt.")
            self.status_var.set(message)

    def _device_selected(self, _event: Any = None) -> None:
        serial = self.device_labels.get(self.device_var.get())
        if not serial:
            return
        changed = serial != self.selected_serial
        self.selected_serial = serial
        info = self.devices.get(serial, {})
        self.detail_var.set(
            f"Android {info.get('android', '?')}   •   Battery {info.get('battery', '?')}   •   USB"
        )
        if changed and self.preview_running:
            self.last_image = None
            self._schedule_capture(50)

    def start_preview(self) -> None:
        if not self.selected_serial:
            messagebox.showwarning("No phone selected", "Connect and select an authorized Android phone first.")
            return
        if not self.adb_path or not self.adb_path.is_file():
            messagebox.showerror("ADB missing", "Install Google's Platform-Tools in the platform-tools folder.")
            return
        self.preview_running = True
        self.preview_state_var.set("LIVE PREVIEW")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Starting ADB screen preview…")
        self._schedule_capture(50)

    def pause_preview(self) -> None:
        self.preview_running = False
        self.preview_state_var.set("PREVIEW PAUSED")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_var.set("Preview paused. USB debugging connection remains available.")

    def _schedule_capture(self, delay: int | None = None) -> None:
        if self.preview_running and not self.capture_busy:
            self.after(self.capture_interval_ms if delay is None else delay, self._capture_frame)

    def _capture_frame(self) -> None:
        if not self.preview_running or self.capture_busy:
            return
        serial = self.selected_serial
        if not serial:
            self.pause_preview()
            return
        self.capture_busy = True
        threading.Thread(target=self._capture_worker, args=(serial,), daemon=True).start()

    def _capture_worker(self, serial: str) -> None:
        try:
            png = self._adb_command(["exec-out", "screencap", "-p"], serial, timeout=10)
            if not png.startswith(b"\x89PNG\r\n\x1a\n"):
                raise RuntimeError("The phone did not return a valid screenshot.")
            self.after(0, lambda data=png: self._frame_received(data, None))
        except Exception as exc:
            self.after(0, lambda error=str(exc): self._frame_received(None, error))

    def _frame_received(self, png: bytes | None, error: str | None) -> None:
        self.capture_busy = False
        if not self.preview_running:
            return
        if error:
            self.status_var.set(f"Screen capture failed: {error}")
            self.after(1200, self._capture_frame)
            return
        try:
            assert png is not None
            image = Image.open(io.BytesIO(png)).convert("RGB")
            self.last_image = image
            self._render_image()
            self.status_var.set(
                f"Live screen: {image.width} × {image.height}. Click or drag on the preview to control the phone."
            )
        except Exception as exc:
            self.status_var.set(f"Could not display screenshot: {exc}")
        self._schedule_capture()

    def _render_image(self) -> None:
        if self.last_image is None:
            self.screen_canvas.delete("all")
            self.image_bounds = (0, 0, 0, 0)
            return
        canvas_w = max(1, self.screen_canvas.winfo_width())
        canvas_h = max(1, self.screen_canvas.winfo_height())
        source = self.last_image
        scale = min(canvas_w / source.width, canvas_h / source.height)
        width = max(1, int(source.width * scale))
        height = max(1, int(source.height * scale))
        resized = source.resize((width, height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized)
        x = (canvas_w - width) // 2
        y = (canvas_h - height) // 2
        self.screen_canvas.delete("all")
        self.screen_canvas.create_image(x, y, image=self.photo, anchor="nw")
        self.image_bounds = (x, y, width, height)

    def _canvas_to_phone(self, event: tk.Event) -> tuple[int, int] | None:
        if self.last_image is None:
            return None
        x0, y0, width, height = self.image_bounds
        if width <= 0 or height <= 0:
            return None
        x, y = event.x - x0, event.y - y0
        if x < 0 or y < 0 or x >= width or y >= height:
            return None
        px = int(x * self.last_image.width / width)
        py = int(y * self.last_image.height / height)
        return (
            min(self.last_image.width - 1, max(0, px)),
            min(self.last_image.height - 1, max(0, py)),
        )

    def _screen_press(self, event: tk.Event) -> None:
        point = self._canvas_to_phone(event)
        self.press_point = point
        self.press_time = time.monotonic()
        self.screen_canvas.focus_set()

    def _screen_release(self, event: tk.Event) -> None:
        start = self.press_point
        self.press_point = None
        end = self._canvas_to_phone(event)
        if start is None or end is None or not self.selected_serial:
            return
        distance = abs(start[0] - end[0]) + abs(start[1] - end[1])
        duration = max(80, min(1200, int((time.monotonic() - self.press_time) * 1000)))
        if distance < 18:
            self._send_input(["tap", str(end[0]), str(end[1])])
        else:
            self._send_input([
                "swipe", str(start[0]), str(start[1]),
                str(end[0]), str(end[1]), str(duration),
            ])

    def _mouse_wheel(self, event: tk.Event) -> None:
        if not self.last_image or not self.selected_serial:
            return
        amount = -1 if event.delta > 0 else 1
        x = self.last_image.width // 2
        y = self.last_image.height // 2
        offset = max(220, self.last_image.height // 5)
        y1 = min(self.last_image.height - 20, max(20, y + amount * offset))
        y2 = min(self.last_image.height - 20, max(20, y - amount * offset))
        self._send_input(["swipe", str(x), str(y1), str(x), str(y2), "220"])

    def _send_input(self, input_args: list[str]) -> None:
        self._send_adb(["shell", "input", *input_args])

    def _send_keyevent(self, keycode: int) -> None:
        self._send_input(["keyevent", str(keycode)])

    def _send_adb(self, args: list[str]) -> None:
        serial = self.selected_serial
        if not serial:
            self.status_var.set("Connect a phone first.")
            return

        def worker() -> None:
            try:
                self._adb_command(args, serial, timeout=8)
            except Exception as exc:
                self.after(0, lambda error=str(exc): self.status_var.set(f"Phone control failed: {error}"))

        threading.Thread(target=worker, daemon=True).start()

    def send_text(self) -> None:
        value = self.text_var.get()
        if not value:
            return
        # Android's input command uses %s as its representation for a space.
        safe_text = value.replace("%", "%25").replace(" ", "%s")
        self._send_input(["text", safe_text])
        self.text_var.set("")

    def _on_close(self) -> None:
        self.preview_running = False
        self.destroy()


if __name__ == "__main__":
    PhoneFixer().mainloop()
