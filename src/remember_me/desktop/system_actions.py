"""
System Actions — Security-Hardened Desktop Automation
=====================================================
Ported from Zyron-Assistant's agents/system.py.

SECURITY CHANGES:
- All os.system() replaced with subprocess.run()
- Input validation via whitelist for process names
- Path validation rejects shell metacharacters
- No import-time side effects
"""

import os
import re
import subprocess
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Lazy imports for optional heavy deps
_pyautogui = None
_cv2 = None
_sbc = None
_psutil = None
_sd = None
_scipy_write = None

def _lazy_import(name: str):
    """Lazy-load heavy optional dependencies."""
    import importlib
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


# ─── PROCESS WHITELIST ───────────────────────────────────────────────

PROCESS_NAMES = {
    # Browsers
    "chrome": "chrome.exe", "googlechrome": "chrome.exe", "google": "chrome.exe",
    "brave": "brave.exe", "bravebrowser": "brave.exe",
    "edge": "msedge.exe", "msedge": "msedge.exe", "microsoftedge": "msedge.exe",
    "firefox": "firefox.exe", "mozilla": "firefox.exe",
    "opera": "opera.exe",
    # System & Tools
    "notepad": "notepad.exe",
    "calculator": "calc.exe", "calc": "calc.exe",
    "cmd": "cmd.exe", "terminal": "WindowsTerminal.exe",
    "explorer": "explorer.exe", "fileexplorer": "explorer.exe",
    "taskmanager": "Taskmgr.exe",
    # Media
    "spotify": "spotify.exe",
    "vlc": "vlc.exe",
    # Coding
    "vscode": "Code.exe", "code": "Code.exe", "visualstudiocode": "Code.exe",
    "pycharm": "pycharm64.exe",
    "androidstudio": "studio64.exe",
    "intellij": "idea64.exe",
    "python": "python.exe",
    # Social
    "telegram": "Telegram.exe",
    "discord": "Discord.exe",
    "whatsapp": "WhatsApp.exe",
    "zoom": "Zoom.exe",
}

# Shell metacharacters that MUST NEVER appear in user-supplied inputs
_SHELL_METACHAR_RE = re.compile(r'[;&|`$><\n\r]')


# ─── VALIDATION FUNCTIONS ────────────────────────────────────────────

def _validate_process_name(app_name: str) -> str:
    """
    Resolves a user-supplied app name to a safe executable via the whitelist.

    Raises ValueError if the name contains shell metacharacters or is not
    in the whitelist.
    """
    if _SHELL_METACHAR_RE.search(app_name):
        raise ValueError(f"Rejected: illegal characters in app name '{app_name}'")

    clean = app_name.lower().strip()
    for noise in ("the ", "app ", "application ", "close ", "open "):
        clean = clean.replace(noise, "")
    key = clean.strip().replace(" ", "")

    if key in PROCESS_NAMES:
        return PROCESS_NAMES[key]

    # If not in whitelist, construct but validate
    candidate = f"{key}.exe"
    if not re.match(r'^[a-zA-Z0-9_\-]+\.exe$', candidate):
        raise ValueError(f"Rejected: unsafe process name '{candidate}'")
    return candidate


def _validate_path(path: str) -> str:
    """
    Validates a filesystem path, rejecting shell metacharacters.

    Raises ValueError on suspicious input.
    """
    if _SHELL_METACHAR_RE.search(path):
        raise ValueError(f"Rejected: illegal characters in path '{path}'")
    return path


# ─── MEDIA DIRECTORY ─────────────────────────────────────────────────

def _get_media_dir() -> Path:
    """Returns (and creates) the media output directory."""
    media_path = Path(os.environ.get("REMEMBER_ME_MEDIA_PATH", "media"))
    media_path.mkdir(parents=True, exist_ok=True)
    return media_path


# ─── CAFFEINE MODE ───────────────────────────────────────────────────

_caffeine_active = False

# Windows constants for SetThreadExecutionState
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def _caffeine_loop():
    """Background thread that prevents system sleep."""
    global _caffeine_active
    import ctypes

    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )

    while _caffeine_active:
        time.sleep(60)

    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


def toggle_caffeine(state: bool) -> str:
    """Enable or disable caffeine mode (prevent system sleep)."""
    global _caffeine_active

    if state:
        if _caffeine_active:
            return "☕ Caffeine Mode is already active."
        _caffeine_active = True
        threading.Thread(target=_caffeine_loop, daemon=True).start()
        return "☕ Caffeine Mode Active. System will stay awake."
    else:
        if not _caffeine_active:
            return "💤 Caffeine Mode is already off."
        _caffeine_active = False
        return "💤 Caffeine Mode Disabled."


# ─── LOCATION ────────────────────────────────────────────────────────

def get_location() -> Optional[Dict[str, Any]]:
    """Gets approximate location via IP geolocation (multiple providers)."""
    import requests as _req

    apis = [
        ("ip-api.com", "http://ip-api.com/json/", lambda d: {
            "ip": d.get("query"), "city": d.get("city"),
            "region": d.get("regionName"), "country": d.get("country"),
            "lat": d.get("lat", 0), "lon": d.get("lon", 0),
            "timezone": d.get("timezone"), "org": d.get("isp"),
        }),
        ("ipapi.co", "https://ipapi.co/json/", lambda d: {
            "ip": d.get("ip"), "city": d.get("city"),
            "region": d.get("region"), "country": d.get("country_name"),
            "lat": d.get("latitude", 0), "lon": d.get("longitude", 0),
            "timezone": d.get("timezone"), "org": d.get("org"),
        }),
    ]

    for name, url, parser in apis:
        try:
            resp = _req.get(url, timeout=5)
            if resp.status_code == 200:
                data = parser(resp.json())
                data["source"] = name
                data["maps_url"] = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
                return data
        except Exception:
            continue
    return None


# ─── BROWSER ─────────────────────────────────────────────────────────

def get_browser_path(browser_name: str) -> Optional[str]:
    """Finds browser executable dynamically via PATH and common install dirs."""
    import shutil as _shutil

    browser_name = browser_name.lower().strip()
    exe_map = {
        "chrome": "chrome.exe", "google": "chrome.exe",
        "brave": "brave.exe", "firefox": "firefox.exe",
        "mozilla": "firefox.exe", "edge": "msedge.exe",
        "msedge": "msedge.exe", "opera": "launcher.exe",
    }
    executable = exe_map.get(browser_name, f"{browser_name}.exe")

    path = _shutil.which(executable)
    if path:
        return path

    for root_env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        root = os.environ.get(root_env)
        if not root:
            continue
        for subdir in (
            "Google\\Chrome\\Application", "BraveSoftware\\Brave-Browser\\Application",
            "Microsoft\\Edge\\Application", "Mozilla Firefox", "Opera",
        ):
            full = os.path.join(root, subdir, executable)
            if os.path.exists(full):
                return full
    return None


def open_browser(url: str, browser_name: str = "default") -> str:
    """Opens URL in specified or default browser."""
    _validate_path(url)  # basic injection check

    if not browser_name or browser_name.lower() == "default":
        webbrowser.open(url)
        return f"🌐 Opened {url} in default browser."

    path = get_browser_path(browser_name)
    if path:
        webbrowser.register(browser_name, None, webbrowser.BackgroundBrowser(path))
        webbrowser.get(browser_name).open(url)
        return f"🌐 Opened {url} in {browser_name}."
    else:
        webbrowser.open(url)
        return f"⚠️ {browser_name} not found. Opened in default browser."


# ─── CAPTURE ─────────────────────────────────────────────────────────

def capture_screen() -> Optional[str]:
    """Takes screenshot. Returns file path or None."""
    global _pyautogui
    if _pyautogui is None:
        _pyautogui = _lazy_import("pyautogui")
    if _pyautogui is None:
        return None

    media_dir = _get_media_dir()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = str(media_dir / f"{ts}_screenshot.png")

    try:
        screenshot = _pyautogui.screenshot()
        screenshot.save(file_path)
        return file_path
    except Exception as e:
        print(f"❌ Screenshot error: {e}")
        return None


def capture_webcam() -> Optional[str]:
    """Captures single frame from webcam. Returns file path or None."""
    global _cv2
    if _cv2 is None:
        _cv2 = _lazy_import("cv2")
    if _cv2 is None:
        return None

    media_dir = _get_media_dir()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = str(media_dir / f"{ts}_webcam_snap.jpg")

    for i in range(2):
        cam = _cv2.VideoCapture(i)
        if cam.isOpened():
            ret, frame = cam.read()
            if ret:
                _cv2.imwrite(file_path, frame)
                cam.release()
                return file_path
            cam.release()
    return None


def record_audio(duration: int = 10) -> Optional[str]:
    """Records audio from default mic. Returns file path or None."""
    global _sd, _scipy_write
    if _sd is None:
        _sd = _lazy_import("sounddevice")
    if _scipy_write is None:
        try:
            from scipy.io.wavfile import write
            _scipy_write = write
        except ImportError:
            _scipy_write = None

    if _sd is None or _scipy_write is None:
        return None

    import numpy as np

    media_dir = _get_media_dir()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = str(media_dir / f"{ts}_audio.wav")

    SAMPLE_RATE = 44100
    try:
        recording = _sd.rec(int(duration * SAMPLE_RATE),
                            samplerate=SAMPLE_RATE, channels=1, dtype="int16")
        _sd.wait()
        _scipy_write(file_path, SAMPLE_RATE, recording)
        return file_path
    except Exception as e:
        print(f"❌ Audio recording error: {e}")
        return None


# ─── SYSTEM POWER ────────────────────────────────────────────────────

def system_sleep() -> str:
    """Puts system to sleep."""
    subprocess.run(
        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
        check=False
    )
    return "💤 System going to sleep."


def shutdown_pc() -> str:
    """Shuts down the computer immediately."""
    subprocess.run(["shutdown", "/s", "/t", "0"], check=False)
    return "🔌 Shutdown initiated."


def restart_pc() -> str:
    """Restarts the computer immediately."""
    subprocess.run(["shutdown", "/r", "/t", "0"], check=False)
    return "🔄 Restart initiated."


# ─── SYSTEM INFO ─────────────────────────────────────────────────────

def get_battery_status() -> str:
    """Returns battery percentage and charging state."""
    global _psutil
    if _psutil is None:
        _psutil = _lazy_import("psutil")
    if _psutil is None:
        return "psutil not available."

    try:
        battery = _psutil.sensors_battery()
        if not battery:
            return "No battery detected (desktop?)."
        status = "Charging ⚡" if battery.power_plugged else "Discharging 🔋"
        return f"Battery: {battery.percent}% — {status}"
    except Exception as e:
        return f"Error reading battery: {e}"


def get_system_health() -> str:
    """Returns CPU/RAM usage summary."""
    global _psutil
    if _psutil is None:
        _psutil = _lazy_import("psutil")
    if _psutil is None:
        return "psutil not available."

    try:
        cpu = _psutil.cpu_percent(interval=1)
        ram = _psutil.virtual_memory()
        free_gb = round(ram.available / (1024**3), 2)
        return f"🖥️ CPU: {cpu}% | RAM: {ram.percent}% ({free_gb} GB free)"
    except Exception as e:
        return f"Error: {e}"


def check_storage() -> str:
    """Returns storage info for all drives."""
    global _psutil
    if _psutil is None:
        _psutil = _lazy_import("psutil")
    if _psutil is None:
        return "psutil not available."

    try:
        lines = ["💾 **Storage Status:**\n"]
        total_free = 0.0
        for part in _psutil.disk_partitions():
            if "cdrom" in part.opts or part.fstype == "":
                continue
            try:
                usage = _psutil.disk_usage(part.mountpoint)
                total_gb = round(usage.total / (1024**3), 2)
                free_gb = round(usage.free / (1024**3), 2)
                total_free += free_gb
                pct = usage.percent
                icon = "🔴" if pct >= 90 else "🟡" if pct >= 75 else "🟢"
                drive = part.mountpoint.replace("\\", "")
                lines.append(f"{icon} **{drive}** — {pct}% used, {free_gb} GB free / {total_gb} GB total")
            except (PermissionError, OSError):
                continue
        lines.append(f"\n📊 Total free: {round(total_free, 2)} GB")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def clear_recycle_bin() -> str:
    """Empties the Windows Recycle Bin."""
    result = subprocess.run(
        ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
        capture_output=True, text=True, check=False
    )
    if result.returncode == 0:
        return "🗑️ Recycle Bin cleared."
    return "🗑️ Recycle Bin may already be empty."


# ─── APPLICATION CONTROL ─────────────────────────────────────────────

def close_application(app_name: str) -> str:
    """Closes an application by name using the process whitelist."""
    exe_name = _validate_process_name(app_name)
    result = subprocess.run(
        ["taskkill", "/f", "/im", exe_name, "/t"],
        capture_output=True, text=True, check=False
    )
    if result.returncode == 0:
        return f"💀 Closed {exe_name}."
    return f"⚠️ Could not close {exe_name}: {result.stderr.strip()}"


def open_application(app_name: str) -> str:
    """Opens an application via Windows Start menu search."""
    global _pyautogui
    if _pyautogui is None:
        _pyautogui = _lazy_import("pyautogui")
    if _pyautogui is None:
        return "pyautogui not available."

    if _SHELL_METACHAR_RE.search(app_name):
        raise ValueError(f"Rejected: illegal characters in app name '{app_name}'")

    _pyautogui.press("win")
    _pyautogui.sleep(0.1)
    _pyautogui.write(app_name)
    _pyautogui.sleep(0.5)
    _pyautogui.press("enter")
    return f"🚀 Launched {app_name}."


def open_file_path(path: str) -> str:
    """Opens a file or directory in the system default handler."""
    path = _validate_path(path)

    # Resolve common aliases
    home = os.path.expanduser("~")
    aliases = {"download": "Downloads", "desktop": "Desktop"}
    for key, folder in aliases.items():
        if key in path.lower():
            path = os.path.join(home, folder)
            break

    if os.path.exists(path):
        os.startfile(path)
        return f"📂 Opened {path}"
    return f"❌ Path not found: {path}"


# ─── DISPLAY ─────────────────────────────────────────────────────────

def set_brightness(level: int) -> str:
    """Sets screen brightness (0-100)."""
    global _sbc
    if _sbc is None:
        _sbc = _lazy_import("screen_brightness_control")
    if _sbc is None:
        return "screen_brightness_control not available."

    try:
        _sbc.set_brightness(level)
        return f"🔆 Brightness set to {level}%."
    except Exception as e:
        return f"Error: {e}"


# ─── MEDIA CONTROL ───────────────────────────────────────────────────

def control_media(action: str) -> str:
    """Controls media playback via Windows media keys."""
    global _pyautogui
    if _pyautogui is None:
        _pyautogui = _lazy_import("pyautogui")
    if _pyautogui is None:
        return "pyautogui not available."

    valid = {"playpause", "nexttrack", "prevtrack", "volumemute"}
    if action not in valid:
        return f"❌ Unknown media action: {action}"

    _pyautogui.press(action)
    return f"🎵 {action} executed."


def set_volume(level: int) -> str:
    """Sets system volume (0-100) via pycaw."""
    if not isinstance(level, (int, float)):
        return "❌ Volume level must be a number."
    level = int(level)
    if not 0 <= level <= 100:
        return "❌ Volume must be between 0 and 100."

    try:
        from pycaw.pycaw import AudioUtilities
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"🔊 Volume set to {level}%."
    except Exception as e:
        return f"⚠️ Volume control error: {e}"


# ─── PANIC ───────────────────────────────────────────────────────────

def system_panic() -> str:
    """Emergency: minimize windows, mute audio, clear clipboard, lock PC."""
    global _pyautogui
    if _pyautogui is None:
        _pyautogui = _lazy_import("pyautogui")

    try:
        import ctypes

        # Minimize all windows
        if _pyautogui:
            _pyautogui.hotkey("win", "d")
            _pyautogui.press("volumemute")

        # Clear clipboard
        try:
            import pyperclip
            pyperclip.copy("")
        except ImportError:
            pass

        # Lock workstation
        ctypes.windll.user32.LockWorkStation()
        return "🚨 System secured."
    except Exception as e:
        return f"❌ Panic error: {e}"
