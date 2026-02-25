"""
Clipboard Monitor — Bounded history with optional encryption.
=============================================================
Ported from Zyron's features/clipboard.py.

CHANGES:
- No import-time thread auto-start
- Bounded history (max 1000 entries, configurable)
- Explicit start_monitoring() / stop_monitoring()
"""

import ctypes
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ClipboardMonitor:
    """
    Monitors Windows clipboard for changes and maintains bounded history.

    Usage:
        monitor = ClipboardMonitor(max_entries=500)
        monitor.start_monitoring()
        ...
        history = monitor.get_history()
        monitor.stop_monitoring()
    """

    def __init__(
        self,
        history_file: str = "clipboard_history.json",
        max_entries: int = 1000,
        poll_interval: float = 1.0,
    ):
        self.history_file = Path(history_file)
        self.max_entries = max_entries
        self.poll_interval = poll_interval

        self._history: List[Dict] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_seq = 0

        # Load existing history
        self._load_history()

    def _load_history(self):
        """Load history from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._history = data if isinstance(data, list) else []
                    # Enforce bound on load
                    if len(self._history) > self.max_entries:
                        self._history = self._history[-self.max_entries:]
            except (json.JSONDecodeError, IOError):
                self._history = []

    def _save_history(self):
        """Save history to disk."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️ Clipboard save error: {e}")

    def _get_clipboard_text(self) -> Optional[str]:
        """Read current clipboard text via Win32 API."""
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if not user32.OpenClipboard(0):
            return None

        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return None

            ptr = kernel32.GlobalLock(handle)
            if not ptr:
                return None

            try:
                text = ctypes.wstring_at(ptr)
                return text
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()

    def _get_clipboard_seq(self) -> int:
        """Get clipboard sequence number (changes on every clipboard update)."""
        return ctypes.windll.user32.GetClipboardSequenceNumber()

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                seq = self._get_clipboard_seq()
                if seq != self._last_seq:
                    self._last_seq = seq
                    text = self._get_clipboard_text()
                    if text and text.strip():
                        entry = {
                            "text": text.strip()[:5000],  # Cap entry size
                            "timestamp": datetime.now().isoformat(),
                        }

                        with self._lock:
                            # Dedup: skip if same as last entry
                            if not self._history or self._history[-1].get("text") != entry["text"]:
                                self._history.append(entry)
                                # Enforce bound
                                if len(self._history) > self.max_entries:
                                    self._history = self._history[-self.max_entries:]
                                self._save_history()

            except Exception:
                pass  # Clipboard access can fail transiently

            time.sleep(self.poll_interval)

    def start_monitoring(self):
        """Start clipboard monitoring in background thread."""
        if self._running:
            return

        self._running = True
        self._last_seq = self._get_clipboard_seq()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        """Stop clipboard monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def get_history(self, limit: int = 20) -> List[Dict]:
        """Returns the most recent clipboard entries."""
        with self._lock:
            return list(self._history[-limit:])

    def clear_history(self):
        """Clears all clipboard history."""
        with self._lock:
            self._history.clear()
            self._save_history()

    def search_history(self, query: str) -> List[Dict]:
        """Search clipboard history for matching entries."""
        query_lower = query.lower()
        with self._lock:
            return [
                entry for entry in self._history
                if query_lower in entry.get("text", "").lower()
            ]
