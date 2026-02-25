"""
Browser Bridge — Firefox extension IPC + web research.
======================================================
Ported from Zyron's browser_control.py + researcher.py.

CHANGES:
- Configurable timeout
- Falls back to DuckDuckGo (via ToolArsenal) instead of Google scraping
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class BrowserBridge:
    """
    Communicates with a Firefox browser extension via JSON file IPC.

    Usage:
        bridge = BrowserBridge()
        tabs = bridge.get_tabs()
        bridge.navigate("https://example.com")
    """

    def __init__(
        self,
        command_file: str = "browser_command.json",
        response_file: str = "browser_response.json",
        timeout: float = 10.0,
        poll_interval: float = 0.5,
    ):
        self.command_file = Path(command_file)
        self.response_file = Path(response_file)
        self.timeout = timeout
        self.poll_interval = poll_interval

    def _send_command(self, command: Dict[str, Any]) -> Optional[Dict]:
        """Sends a command and waits for response."""
        # Clear previous response
        if self.response_file.exists():
            self.response_file.unlink()

        # Write command
        with open(self.command_file, "w") as f:
            json.dump(command, f)

        # Poll for response
        start = time.time()
        while time.time() - start < self.timeout:
            if self.response_file.exists():
                try:
                    with open(self.response_file, "r") as f:
                        response = json.load(f)
                    self.response_file.unlink()
                    return response
                except (json.JSONDecodeError, IOError):
                    pass
            time.sleep(self.poll_interval)

        return None

    def get_tabs(self) -> List[Dict[str, str]]:
        """Get list of open browser tabs."""
        response = self._send_command({"action": "get_tabs"})
        if response and "tabs" in response:
            return response["tabs"]
        return []

    def navigate(self, url: str) -> bool:
        """Navigate the active tab to a URL."""
        response = self._send_command({"action": "navigate", "url": url})
        return response is not None and response.get("status") == "ok"

    def close_tab(self, tab_id: int) -> bool:
        """Close a specific tab by ID."""
        response = self._send_command({"action": "close_tab", "tab_id": tab_id})
        return response is not None and response.get("status") == "ok"

    def get_page_content(self) -> Optional[str]:
        """Get text content of the active tab."""
        response = self._send_command({"action": "get_content"})
        if response and "content" in response:
            return response["content"]
        return None

    @property
    def is_available(self) -> bool:
        """Check if the browser extension is responding."""
        response = self._send_command({"action": "ping"})
        return response is not None
