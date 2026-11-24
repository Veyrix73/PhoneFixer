from __future__ import annotations

import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk

APP_NAME = "POCO Cleaner"
VERSION = "2.0"

KNOWN_NAMES = {
    "com.whatsapp": "WhatsApp",
    "com.facebook.katana": "Facebook",
    "com.instagram.android": "Instagram",
    "com.zhiliaoapp.musically": "TikTok",
    "com.spotify.music": "Spotify",
    "com.google.android.youtube": "YouTube",
    "com.google.android.apps.youtube.music": "YouTube Music",
    "com.google.android.apps.photos": "Google Photos",
    "com.google.android.gm": "Gmail",
    "com.google.android.apps.maps": "Google Maps",
    "com.google.android.googlequicksearchbox": "Google app",
    "com.android.chrome": "Google Chrome",
    "com.android.vending": "Google Play Store",
    "com.google.android.gms": "Google Play services",
    "com.google.android.gsf": "Google Services Framework",
    "com.google.android.apps.messaging": "Google Messages",
    "com.miui.gallery": "Gallery",
    "com.miui.securitycenter": "Security",
    "com.miui.cleanmaster": "Cleaner",
    "com.miui.player": "Mi Music",
    "com.miui.videoplayer": "Mi Video",
    "com.mi.globalbrowser": "Mi Browser",
    "com.xiaomi.mipicks": "GetApps",
    "com.xiaomi.midrop": "ShareMe",
    "com.xiaomi.scanner": "Scanner",
    "com.android.settings": "Settings",
    "com.android.phone": "Phone services",
    "com.android.contacts": "Contacts",
    "com.android.systemui": "System UI",
    "com.android.camera": "Camera",
    "com.android.deskclock": "Clock",
    "com.android.calculator2": "Calculator",
    "com.android.permissioncontroller": "Permission controller",
}

def resource_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

def find_adb() -> str | None:
    paths = [
        resource_dir() / "platform-tools" / "adb.exe",
        Path(sys.executable).resolve().parent / "platform-tools" / "adb.exe",
        resource_dir() / "adb.exe",
        Path(sys.executable).resolve().parent / "adb.exe",
    ]
    for path in paths:
        if path.is_file():
            return str(path)
    return shutil.which("adb") or shutil.which("adb.exe")

def friendly_name(package: str) -> str:
    if package in KNOWN_NAMES:
        return KNOWN_NAMES[package]
    tail = package.rsplit(".", 1)[-1]
    tail = re.sub(r"([a-z])([A-Z])", r"\1 \2", tail).replace("_", " ").replace("-", " ")
    return tail[:1].upper() + tail[1:] if tail else package

@dataclass
class AppRecord:
    package: str
    name: str
    app_type: str
    version_code: str = "—"

    @property
    def removable(self) -> bool:
        return self.app_type == "User app"

class Adb:
    def __init__(self, path: str):
        self.path = path

    def run(self, args: list[str], serial: str | None = None, timeout: int = 30) -> str:
        cmd = [self.path]
        if serial:
            cmd += ["-s", serial]
        cmd += args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("ADB timed out. Unlock the phone and check the USB cable.") from exc
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout or "ADB command failed").strip())
        return result.stdout.strip()

    def devices(self) -> tuple[list[str], list[str]]:
        self.run(["start-server"], timeout=15)
        output = self.run(["devices"])
        ready, waiting = [], []
        for line in output.splitlines()[1:]:
            fields = line.split()
            if len(fields) >= 2:
                if fields[1] == "device":
                    ready.append(fields[0])
                elif fields[1] in {"unauthorized", "offline"}:
                    waiting.append(f"{fields[0]} ({fields[1]})")
        return ready, waiting

    def device_details(self, serial: str) -> dict[str, str]:
        def prop(key: str) -> str:
            try:
                return self.run(["shell", "getprop", key], serial, 12)
            except RuntimeError:
                return ""
        details = {
            "model": (prop("ro.product.manufacturer") + " " + prop("ro.product.model")).strip(),
            "android": prop("ro.build.version.release"),
            "os": prop("ro.miui.ui.version.name") or prop("ro.mi.os.version.name"),
        }
        try:
            battery = self.run(["shell", "dumpsys", "battery"], serial, 12)
            match = re.search(r"level:\s*(\d+)", battery)
            details["battery"] = f"{match.group(1)}%" if match else "Not available"
        except RuntimeError:
            details["battery"] = "Not available"
        return details

    def installed_apps(self, serial: str) -> list[AppRecord]:
        all_apps = self.run(
            ["shell", "pm", "list", "packages", "--show-versioncode"],
            serial, 40
        )
        user_apps = self.run(["shell", "pm", "list", "packages", "-3"], serial, 30)
        user_ids = {
            line.split(":",  1)[1].strip()
            for line in user_apps.splitlines() if line.startswith("package:")
        }
        records = []
        for line in all_apps.splitlines():
            if not line.startswith("package:"):
                continue
            payload = line[len("package:"):].strip()
            bits = payload.split()
            if not bits:
                continue
            package = bits[0]
            version = re.search(r"versionCode:(\S+)", payload)
            is_user = package in user_ids
            records.append(AppRecord(
                package, friendly_name(package),
                "User app" if is_user else "Protected system app",
                version.group(1) if version else "—"
            ))
        return sorted(records, key=lambda app: (not app.removable, app.name.casefold(), app.package))

    def uninstall(self, serial: str, package: str) -> str:
        return self.run(["shell", "pm", "uninstall", "--user", "0", package], serial, 35)

class PhoneFixer(tk.Tk):
    BG, PANEL, PANEL2 = "#10151d", "#192230", "#202c3b"
    FG, MUTED, ACCENT, AMBER = "#edf2f7", "#a6b2c2", "#66a6ff", "#f2c66d"

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("1120x720")
        self.minsize(900, 600)
        self.configure(bg=self.BG)
        self.adb_path = find_adb()
        self.adb = Adb(self.adb_path) if self.adb_path else None
        self.serial: str | None = None
        self.records: list[AppRecord] = []
        self.checked: set[str] = set()
        self.show_system = tk.BooleanVar(value=False)
        self.search = tk.StringVar()
        self.status = tk.StringVar(value="Connect your POCO to begin.")
        self.device = tk.StringVar(value="No device connected")
        self.count = tk.StringVar(value="0 apps")
        self._styles()
        self._ui()
        if not self.adb:
            self.after(300, self._adb_help)

    def _styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=self.PANEL, fieldbackground=self.PANEL,
                        foreground=self.FG, rowheight=34, borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=self.PANEL2, foreground=self.FG,
                        font=("Segoe UI", 9, "bold"), relief="flat", padding=9)
        style.map("Treeview", background=[("selected", "#29496d")],
                  foreground=[("selected", "#ffffff")])

    def button(self, parent, text, command, primary=False):
        bg = "#2c6fbd" if primary else self.PANEL2
        active = "#3c83d6" if primary else "#2a394b"
        return tk.Button(parent, text=text, command=command, bg=bg, fg=self.FG,
                         activebackground=active, activeforeground=self.FG,
                         relief="flat", bd=0, padx=14, pady=9,
                         font=("Segoe UI", 9, "bold"), cursor="hand2")

    def _ui(self):
        head = tk.Frame(self, bg=self.BG)
        head.pack(fill="x", padx=22, pady=(18, 12))
        title = tk.Frame(head, bg=self.BG)
        title.pack(side="left", fill="x", expand=True)
        tk.Label(title, text="PhoneFixer", bg=self.BG, fg=self.FG,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(title, text="See what's installed. Choose what you actually want to remove.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))
        self.button(head, "Connect / Refresh", self.connect, True).pack(side="right")

        card = tk.Frame(self, bg=self.PANEL, padx=16, pady=12)
        card.pack(fill="x", padx=22, pady=(0, 14))
        tk.Label(card, text="CONNECTED DEVICE", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(card, textvariable=self.device, bg=self.PANEL, fg=self.FG,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(3, 0))
        self.device_meta = tk.Label(card, text="USB debugging connection not established",
                                    bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 9))
        self.device_meta.pack(anchor="w", pady=(3, 0))

        toolbar = tk.Frame(self, bg=self.BG)
        toolbar.pack(fill="x", padx=22, pady=(0, 10))
        search_box = tk.Frame(toolbar, bg=self.PANEL2, padx=10, pady=2)
        search_box.pack(side="left", fill="x", expand=True)
        tk.Label(search_box, text="⌕", bg=self.PANEL2, fg=self.MUTED,
                 font=("Segoe UI", 15)).pack(side="left", padx=(0, 6))
        entry = tk.Entry(search_box, textvariable=self.search, bg=self.PANEL2,
                         fg=self.FG, insertbackground=self.FG, relief="flat",
                         font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True, ipady=8)
        entry.bind("<KeyRelease>", lambda _e: self.render())
        tk.Checkbutton(toolbar, text="Show protected system apps",
                       variable=self.show_system, command=self.render, bg=self.BG,
                       fg=self.MUTED, activebackground=self.BG, activeforeground=self.FG,
                       selectcolor=self.PANEL2, font=("Segoe UI", 9)).pack(side="left", padx=14)

        box = tk.Frame(self, bg=self.PANEL, padx=1, pady=1)
        box.pack(fill="both", expand=True, padx=22, pady=(0, 10))
        bar = tk.Frame(box, bg=self.PANEL, padx=14, pady=10)
        bar.pack(fill="x")
        tk.Label(bar, text="Installed apps", bg=self.PANEL, fg=self.FG,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(bar, textvariable=self.count, bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="right")

        cols = ("check", "app", "type", "package", "version")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        for key, label in (("check", "SELECT"), ("app", "APP"), ("type", "CATEGORY"),
                           ("package", "PACKAGE ID"), ("version", "VERSION CODE")):
            self.tree.heading(key, text=label)
        self.tree.column("check", width=66, minwidth=66, anchor="center", stretch=False)
        self.tree.column("app", width=210, minwidth=140)
        self.tree.column("type", width=165, minwidth=140, stretch=False)
        self.tree.column("package", width=390, minwidth=210)
        self.tree.column("version", width=100, minwidth=90, anchor="center", stretch=False)
        self.tree.tag_configure("user", foreground=self.FG)
        self.tree.tag_configure("system", foreground="#93a0b0")
        self.tree.bind("<Button-1>", self._click)
        self.tree.bind("<<TreeviewSelect>>", self._selection)
        area = tk.Frame(box, bg=self.PANEL)
        area.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.tree.pack(in_=area, side="left", fill="both", expand=True)
        ybar = ttk.Scrollbar(area, orient="vertical", command=self.tree.yview)
        ybar.pack(side="right", fill="y")
        xbar = ttk.Scrollbar(box, orient="horizontal", command=self.tree.xview)
        xbar.pack(fill="x", padx=10, pady=(0, 8))
        self.tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)

        footer = tk.Frame(self, bg=self.BG)
        footer.pack(fill="x", padx=22, pady=(0, 10))
        left = tk.Frame(footer, bg=self.BG)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, textvariable=self.status, bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9), anchor="w").pack(anchor="w")
        self.selected_label = tk.Label(left, text="0 selected", bg=self.BG, fg=self.ACCENT,
                                       font=("Segoe UI", 9, "bold"))
        self.selected_label.pack(anchor="w", pady=(3, 0))
        actions = tk.Frame(footer, bg=self.BG)
        actions.pack(side="right")
        self.button(actions, "Select visible user apps", self.select_visible).pack(side="left", padx=(0, 7))
        self.button(actions, "Clear selection", self.clear).pack(side="left", padx=(0, 7))
        self.button(actions, "Uninstall selected", self.uninstall_selected, True).pack(side="left")
        tk.Label(self, text="SYSTEM APPS ARE LOCKED. Only third-party/user-installed apps can be selected.",
                 bg=self.BG, fg=self.AMBER, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=23, pady=(0, 10))

    def _adb_help(self):
        messagebox.showinfo("ADB required",
            "Install Google's Android Platform-Tools. Extract the folder next to this app as "
            "'platform-tools' (containing adb.exe), or add its folder to Windows PATH. "
            "Then restart PhoneFixer.")

    def connect(self):
        if not self.adb:
            self._adb_help()
            return
        self.status.set("Looking for an authorized Android device…")
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self):
        try:
            ready, waiting = self.adb.devices()
            if not ready:
                error = "No authorized phone found. Unlock the POCO and accept the USB debugging prompt."
                if waiting:
                    error += " Waiting device(s): " + ", ".join(waiting)
                raise RuntimeError(error)
            serial = ready[0]
            details = self.adb.device_details(serial)
            apps = self.adb.installed_apps(serial)
            self.after(0, lambda: self._connected(serial, details, apps, len(ready)))
        except Exception as exc:
            self.after(0, lambda: self._failed(str(exc)))

    def _connected(self, serial, details, apps, device_count):
        self.serial, self.records = serial, apps
        self.checked.clear()
        self.device.set(details.get("model") or "Android device")
        meta = [f"Android {details.get('android') or '—'}",
                details.get("os") or "", f"Battery {details.get('battery') or '—'}"]
        self.device_meta.configure(text="  •  ".join(x for x in meta if x))
        self.render()
        self.status.set(f"Connected. {len(apps)} installed packages detected.")
        if device_count > 1:
            self.status.set("Multiple phones found; using the first authorized device. Disconnect extras for clarity.")

    def _failed(self, error):
        self.status.set(error)
        messagebox.showerror("Could not connect", error)

    def visible_records(self):
        query = self.search.get().strip().casefold()
        result = []
        for app in self.records:
            if not self.show_system.get() and not app.removable:
                continue
            if query and query not in app.name.casefold() and query not in app.package.casefold():
                continue
            result.append(app)
        return result

    def render(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        visible = self.visible_records()
        for app in visible:
            mark = "☑" if app.package in self.checked else ("☐" if app.removable else "🔒")
            self.tree.insert("", "end", iid=app.package,
                values=(mark, app.name, "USER APP" if app.removable else "PROTECTED SYSTEM",
                        app.package, app.version_code),
                tags=("user" if app.removable else "system",))
        user_count = sum(app.removable for app in self.records)
        self.count.set(f"{len(visible)} shown  •  {user_count} removable user apps")
        self.selected_label.configure(text=f"{len(self.checked)} selected")

    def _click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        row = self.tree.identify_row(event.y)
        if not row or self.tree.identify_column(event.x) != "#1":
            return
        app = next((a for a in self.records if a.package == row), None)
        if not app or not app.removable:
            return
        if row in self.checked:
            self.checked.remove(row)
        else:
            self.checked.add(row)
        self.render()
        return "break"

    def _selection(self, _event):
        rows = self.tree.selection()
        if not rows:
            return
        app = next((a for a in self.records if a.package == rows[0]), None)
        if app:
            self.status.set(f"{app.name}  •  {app.package}  •  {app.app_type}")

    def select_visible(self):
        self.checked.update(app.package for app in self.visible_records() if app.removable)
        self.render()

    def clear(self):
        self.checked.clear()
        self.render()

    def uninstall_selected(self):
        if not self.serial or not self.adb:
            messagebox.showwarning("No phone connected", "Connect your POCO first.")
            return
        allow_list = {app.package for app in self.records if app.removable}
        selected = sorted(self.checked.intersection(allow_list))
        if not selected:
            messagebox.showinfo("Nothing selected", "Select one or more user apps. System apps are locked.")
            return
        preview = "\n".join(selected[:10])
        if len(selected) > 10:
            preview += f"\n…and {len(selected) - 10} more"
        ok = messagebox.askyesno("Confirm bulk uninstall",
            f"Uninstall {len(selected)} selected app(s) for the current Android user?\n\n{preview}\n\n"
            "This can delete local app data. Continue?")
        if not ok:
            return
        self.status.set(f"Uninstalling {len(selected)} app(s)…")
        threading.Thread(target=self._uninstall_worker, args=(self.serial, selected), daemon=True).start()

    def _uninstall_worker(self, serial, packages):
        success, failed = [], []
        for package in packages:
            try:
                result = self.adb.uninstall(serial, package)
                if "success" in result.casefold():
                    success.append(package)
                else:
                    failed.append((package, result or "No success response"))
            except Exception as exc:
                failed.append((package, str(exc)))
        self.after(0, lambda: self._finished(success, failed))

    def _finished(self, success, failed):
        removed = set(success)
        self.records = [app for app in self.records if app.package not in removed]
        self.checked.difference_update(removed)
        self.render()
        self.status.set(f"Finished. Removed {len(success)} app(s); {len(failed)} failed. Refresh to rescan.")
        report = f"Successfully uninstalled: {len(success)}\nFailed: {len(failed)}"
        if failed:
            report += "\n\n" + "\n".join(f"{pkg}: {err}" for pkg, err in failed[:5])
        messagebox.showinfo("Uninstall results", report)

if __name__ == "__main__":
    PhoneFixer().mainloop()
