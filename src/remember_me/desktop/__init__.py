"""
Remember-Me Desktop Agent Layer
================================
Provides physical-world actuators (system control, voice I/O, clipboard,
file management, browser, Telegram) that connect to the Sovereign Kernel.

All dependencies are optional — the core brain works without this package.
"""

__all__ = [
    "system_actions",
    "voice",
    "clipboard",
    "focus_mode",
    "zombie_reaper",
    "activity",
    "browser_bridge",
    "desktop_tools",
]
