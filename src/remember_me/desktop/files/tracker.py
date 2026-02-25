"""
File Tracker — Monitors file access activity.
==============================================
Ported from Zyron's features/files/tracker.py.

CHANGES:
- No auto-start on import
- Bounded activity log (max 10,000 entries)
- Uses pathlib throughout
"""

import json
import os
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileTracker:
    """
    Tracks file access activity on the system.

    Usage:
        tracker = FileTracker()
        tracker.start()
        ...
        recent = tracker.get_recent_files()
        tracker.stop()
    """

    def __init__(
        self,
        log_file: str = "file_activity.json",
        max_entries: int = 10_000,
        scan_interval: int = 30,
        watch_dirs: Optional[List[str]] = None,
    ):
        self.log_file = Path(log_file)
        self.max_entries = max_entries
        self.scan_interval = scan_interval

        # Default watch directories
        home = Path.home()
        self.watch_dirs = watch_dirs or [
            str(home / "Desktop"),
            str(home / "Documents"),
            str(home / "Downloads"),
        ]

        self._activity_log: List[Dict[str, Any]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._known_files: Dict[str, float] = {}  # path -> last_modified
        self._lock = threading.Lock()

        self._load_log()

    def _load_log(self):
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._activity_log = data if isinstance(data, list) else []
                    if len(self._activity_log) > self.max_entries:
                        self._activity_log = self._activity_log[-self.max_entries:]
            except (json.JSONDecodeError, IOError):
                self._activity_log = []

    def _save_log(self):
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(self._activity_log, f, indent=2, default=str)
        except IOError:
            pass

    def _scan_directories(self):
        """Scan watched directories for new/modified files."""
        # Common file extensions to track
        trackable = {
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".txt", ".py", ".js", ".ts", ".html", ".css", ".json",
            ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3",
            ".zip", ".rar", ".7z", ".csv", ".md",
        }

        for watch_dir in self.watch_dirs:
            if not os.path.isdir(watch_dir):
                continue

            try:
                for root, dirs, files in os.walk(watch_dir):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith(".")]

                    for filename in files:
                        ext = Path(filename).suffix.lower()
                        if ext not in trackable:
                            continue

                        filepath = os.path.join(root, filename)
                        try:
                            mtime = os.path.getmtime(filepath)
                            prev_mtime = self._known_files.get(filepath)

                            if prev_mtime is None or mtime > prev_mtime:
                                self._known_files[filepath] = mtime
                                if prev_mtime is not None:
                                    # File was modified (not just discovered)
                                    self._record_activity(filepath, "modified")
                        except OSError:
                            continue
            except Exception:
                continue

    def _record_activity(self, filepath: str, action: str):
        entry = {
            "file_path": filepath,
            "file_name": os.path.basename(filepath),
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "size_bytes": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
        }

        with self._lock:
            self._activity_log.append(entry)
            if len(self._activity_log) > self.max_entries:
                self._activity_log = self._activity_log[-self.max_entries:]
            self._save_log()

    def _monitor_loop(self):
        while self._running:
            self._scan_directories()
            time.sleep(self.scan_interval)

    def start(self):
        """Start file monitoring."""
        if self._running:
            return
        self._running = True
        # Initial scan to populate known files
        self._scan_directories()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop file monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.scan_interval + 1)

    def get_recent_files(self, limit: int = 20) -> List[Dict]:
        """Returns the most recently tracked files."""
        with self._lock:
            return list(self._activity_log[-limit:])

    def search(self, query: str) -> List[Dict]:
        """Simple text search over activity log."""
        q = query.lower()
        with self._lock:
            return [
                entry for entry in self._activity_log
                if q in entry.get("file_name", "").lower()
                or q in entry.get("file_path", "").lower()
            ]
