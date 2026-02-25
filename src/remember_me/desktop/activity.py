"""
Activity Monitor — Unified process and browser tab tracking.
============================================================
Ported from Zyron's features/activity.py.

CHANGES:
- Deduplicated browser functions into single _get_browser_tabs()
- Uses pathlib + environment vars instead of hardcoded paths
- No import-time side effects
"""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _get_browser_db_path(browser: str) -> Optional[Path]:
    """Returns the History database path for a given browser."""
    local = os.environ.get("LOCALAPPDATA", "")
    if not local:
        return None

    browser_paths = {
        "chrome": Path(local) / "Google" / "Chrome" / "User Data" / "Default" / "History",
        "brave": Path(local) / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "History",
        "edge": Path(local) / "Microsoft" / "Edge" / "User Data" / "Default" / "History",
    }

    # Firefox uses a different profile structure
    if browser == "firefox":
        profiles_dir = Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
        if profiles_dir.exists():
            for profile_dir in profiles_dir.iterdir():
                places = profile_dir / "places.sqlite"
                if places.exists():
                    return places
        return None

    return browser_paths.get(browser)


def _get_browser_tabs(browser: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Gets recent browser history entries for any Chromium-based browser.
    Uses a temporary copy of the locked SQLite database.
    """
    db_path = _get_browser_db_path(browser)
    if not db_path or not db_path.exists():
        return []

    # Copy the locked DB to a temp file
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(tmp_fd)

    try:
        shutil.copy2(str(db_path), tmp_path)
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()

        if browser == "firefox":
            cursor.execute("""
                SELECT p.url, p.title, v.visit_date
                FROM moz_places p
                JOIN moz_historyvisits v ON p.id = v.place_id
                ORDER BY v.visit_date DESC
                LIMIT ?
            """, (limit,))
        else:
            # Chromium-based browsers
            cursor.execute("""
                SELECT url, title, last_visit_time
                FROM urls
                ORDER BY last_visit_time DESC
                LIMIT ?
            """, (limit,))

        tabs = []
        for row in cursor.fetchall():
            tabs.append({
                "url": row[0] or "",
                "title": row[1] or "Untitled",
                "browser": browser,
            })

        conn.close()
        return tabs

    except Exception as e:
        print(f"⚠️ Error reading {browser} history: {e}")
        return []
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def get_running_processes(top_n: int = 20) -> List[Dict[str, Any]]:
    """Returns top N processes by memory usage."""
    try:
        import psutil
    except ImportError:
        return []

    procs = []
    for proc in psutil.process_iter(["name", "pid", "memory_info", "cpu_percent"]):
        try:
            info = proc.info
            mem = info.get("memory_info")
            if mem:
                procs.append({
                    "name": info["name"],
                    "pid": info["pid"],
                    "ram_mb": round(mem.rss / (1024 * 1024), 1),
                })
        except Exception:
            continue

    procs.sort(key=lambda p: p["ram_mb"], reverse=True)
    return procs[:top_n]


def get_active_window() -> Optional[Dict[str, str]]:
    """Returns info about the currently active window."""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        # Get window title
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)

        # Get PID
        pid_buf = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))

        return {
            "title": buf.value,
            "pid": pid_buf.value,
        }
    except Exception:
        return None


def get_browser_tabs(browsers: Optional[List[str]] = None, limit: int = 5) -> List[Dict]:
    """Gets recent tabs from specified browsers (defaults to all)."""
    if browsers is None:
        browsers = ["chrome", "brave", "edge", "firefox"]

    all_tabs = []
    for browser in browsers:
        all_tabs.extend(_get_browser_tabs(browser, limit=limit))
    return all_tabs


def get_current_activities() -> str:
    """Returns a formatted summary of current system activity."""
    lines = ["📊 **Current Activity:**\n"]

    # Active window
    window = get_active_window()
    if window:
        lines.append(f"🪟 Active: {window['title']}")

    # Top processes
    procs = get_running_processes(10)
    if procs:
        lines.append("\n🔝 **Top Processes (by RAM):**")
        for p in procs:
            lines.append(f"  • {p['name']} — {p['ram_mb']} MB")

    # Browser tabs
    tabs = get_browser_tabs(limit=3)
    if tabs:
        lines.append("\n🌐 **Recent Browser Activity:**")
        for t in tabs:
            title = t["title"][:60] + "..." if len(t["title"]) > 60 else t["title"]
            lines.append(f"  • [{t['browser']}] {title}")

    return "\n".join(lines)
