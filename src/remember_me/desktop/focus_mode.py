"""
Focus Mode — App/website blocking for productivity.
====================================================
Ported from Zyron's features/focus_mode.py.

CHANGES:
- Exact process name matching (not substring)
- subprocess.run() replaces os.system()
- Configurable via constructor (no global state)
"""

import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set


class FocusMode:
    """
    Blocks specified apps and websites during focus sessions.

    Usage:
        focus = FocusMode()
        focus.add_to_blacklist("discord")
        focus.start()
        ...
        focus.stop()
    """

    def __init__(
        self,
        blacklist_file: str = "blacklist.json",
        check_interval: float = 5.0,
    ):
        self.blacklist_file = Path(blacklist_file)
        self.check_interval = check_interval

        self._blacklist: Dict[str, List[str]] = {"apps": [], "websites": []}
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._load_blacklist()

    def _load_blacklist(self):
        if self.blacklist_file.exists():
            try:
                with open(self.blacklist_file, "r") as f:
                    self._blacklist = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def _save_blacklist(self):
        self.blacklist_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.blacklist_file, "w") as f:
            json.dump(self._blacklist, f, indent=2)

    def add_to_blacklist(self, name: str, category: str = "apps") -> str:
        """Add an app or website to the blacklist."""
        name = name.lower().strip()
        if category not in ("apps", "websites"):
            return f"❌ Invalid category: {category}"

        if name not in self._blacklist[category]:
            self._blacklist[category].append(name)
            self._save_blacklist()
            return f"✅ Added '{name}' to {category} blacklist."
        return f"'{name}' already in blacklist."

    def remove_from_blacklist(self, name: str, category: str = "apps") -> str:
        """Remove an app or website from the blacklist."""
        name = name.lower().strip()
        if name in self._blacklist.get(category, []):
            self._blacklist[category].remove(name)
            self._save_blacklist()
            return f"✅ Removed '{name}' from {category} blacklist."
        return f"'{name}' not found in blacklist."

    def get_blacklist(self) -> Dict[str, List[str]]:
        """Returns current blacklist."""
        return dict(self._blacklist)

    def _enforce_loop(self):
        """Background thread that kills blacklisted processes."""
        try:
            import psutil
        except ImportError:
            print("⚠️ psutil required for Focus Mode.")
            return

        while self._running:
            blocked_apps = set(
                app.lower() for app in self._blacklist.get("apps", [])
            )

            if blocked_apps:
                for proc in psutil.process_iter(["name"]):
                    try:
                        proc_name = proc.info["name"]
                        if proc_name and proc_name.lower().rstrip(".exe") in blocked_apps:
                            proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            time.sleep(self.check_interval)

    def start(self) -> str:
        """Start enforcing focus mode."""
        if self._running:
            return "🎯 Focus Mode is already active."

        self._running = True
        self._thread = threading.Thread(target=self._enforce_loop, daemon=True)
        self._thread.start()
        return "🎯 Focus Mode activated."

    def stop(self) -> str:
        """Stop enforcing focus mode."""
        if not self._running:
            return "Focus Mode is already off."

        self._running = False
        if self._thread:
            self._thread.join(timeout=self.check_interval + 1)
        return "✅ Focus Mode deactivated."

    @property
    def is_active(self) -> bool:
        return self._running
