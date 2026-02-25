"""
Zombie Reaper — Detects and reports idle high-RAM processes.
============================================================
Ported from Zyron's features/zombie_reaper.py.

CHANGES:
- Returns structured data instead of sending Telegram messages
- Caller handles reporting
- Configurable thresholds
"""

import time
import threading
from typing import Any, Callable, Dict, List, Optional


class ZombieReaper:
    """
    Scans for processes using high RAM that haven't been in the foreground recently.

    Usage:
        reaper = ZombieReaper(ram_threshold_mb=500)
        zombies = reaper.scan()  # One-shot scan
        reaper.start_monitoring(callback=handle_zombies)  # Continuous
    """

    def __init__(
        self,
        ram_threshold_mb: int = 500,
        idle_threshold_sec: int = 300,
        scan_interval: int = 120,
    ):
        self.ram_threshold_mb = ram_threshold_mb
        self.idle_threshold_sec = idle_threshold_sec
        self.scan_interval = scan_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._foreground_history: Dict[str, float] = {}
        self._fg_thread: Optional[threading.Thread] = None

    def _track_foreground(self):
        """Track which processes are in the foreground."""
        try:
            import ctypes
            import psutil

            user32 = ctypes.windll.user32

            while self._running:
                try:
                    hwnd = user32.GetForegroundWindow()
                    if hwnd:
                        pid_buf = ctypes.c_ulong()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))
                        pid = pid_buf.value
                        try:
                            proc = psutil.Process(pid)
                            self._foreground_history[proc.name().lower()] = time.time()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except Exception:
                    pass
                time.sleep(5)
        except ImportError:
            pass

    def scan(self) -> List[Dict[str, Any]]:
        """
        One-shot scan for zombie processes.
        Returns list of dicts with: name, pid, ram_mb, idle_seconds.
        """
        try:
            import psutil
        except ImportError:
            return []

        now = time.time()
        zombies = []

        # System processes to never flag
        safe = {
            "system", "svchost.exe", "csrss.exe", "smss.exe", "wininit.exe",
            "services.exe", "lsass.exe", "winlogon.exe", "dwm.exe",
            "explorer.exe", "taskhost.exe", "conhost.exe", "memory compression",
            "registry", "system idle process", "python.exe", "pythonw.exe",
        }

        for proc in psutil.process_iter(["name", "pid", "memory_info"]):
            try:
                info = proc.info
                name = (info["name"] or "").lower()
                if name in safe:
                    continue

                mem = info.get("memory_info")
                if not mem:
                    continue

                ram_mb = mem.rss / (1024 * 1024)
                if ram_mb < self.ram_threshold_mb:
                    continue

                # Check if idle
                last_fg = self._foreground_history.get(name, 0)
                idle_sec = now - last_fg if last_fg > 0 else float("inf")

                if idle_sec >= self.idle_threshold_sec:
                    zombies.append({
                        "name": info["name"],
                        "pid": info["pid"],
                        "ram_mb": round(ram_mb, 1),
                        "idle_seconds": round(idle_sec, 0) if idle_sec != float("inf") else -1,
                    })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by RAM usage descending
        zombies.sort(key=lambda z: z["ram_mb"], reverse=True)
        return zombies

    def kill_process(self, pid: int) -> str:
        """Terminate a process by PID."""
        try:
            import psutil
            proc = psutil.Process(pid)
            name = proc.name()
            proc.terminate()
            return f"💀 Terminated {name} (PID {pid})."
        except Exception as e:
            return f"❌ Failed to kill PID {pid}: {e}"

    def start_monitoring(self, callback: Callable[[List[Dict]], None]):
        """
        Start continuous monitoring. Calls callback(zombies_list) when
        high-RAM idle processes are detected.
        """
        if self._running:
            return

        self._running = True

        # Start foreground tracker
        self._fg_thread = threading.Thread(target=self._track_foreground, daemon=True)
        self._fg_thread.start()

        def _loop():
            while self._running:
                zombies = self.scan()
                if zombies:
                    callback(zombies)
                time.sleep(self.scan_interval)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
