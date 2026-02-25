"""
Desktop Tool Registry — Wires all desktop actuators into the SovereignAgent.
=============================================================================
Each tool has a name, description, function, and confirmation flag.

The SovereignAgent can invoke these tools through its execution pipeline,
routing user intent through the Nervous System and VetoCircuit before execution.
"""

from typing import Any, Callable, Dict, List, Optional


class DesktopTool:
    """Represents a single callable tool for the Agent."""

    __slots__ = ("name", "description", "function", "requires_confirmation", "category")

    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        requires_confirmation: bool = False,
        category: str = "general",
    ):
        self.name = name
        self.description = description
        self.function = function
        self.requires_confirmation = requires_confirmation
        self.category = category

    def execute(self, **kwargs) -> Any:
        return self.function(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requires_confirmation": self.requires_confirmation,
            "category": self.category,
        }


class DesktopToolRegistry:
    """
    Central registry of all desktop tools available to the SovereignAgent.

    Usage:
        registry = DesktopToolRegistry()
        tools = registry.get_all_tools()
        tool = registry.get_tool("take_screenshot")
        result = tool.execute()
    """

    def __init__(self):
        self._tools: Dict[str, DesktopTool] = {}
        self._register_all()

    def _register_all(self):
        """Register all desktop tools. Imports are lazy to handle missing deps."""
        try:
            from remember_me.desktop import system_actions as sa

            self._register(DesktopTool(
                "take_screenshot", "Capture a screenshot of the current screen",
                sa.capture_screen, category="capture",
            ))
            self._register(DesktopTool(
                "capture_webcam", "Take a photo from the webcam",
                sa.capture_webcam, category="capture",
            ))
            self._register(DesktopTool(
                "record_audio", "Record audio from the microphone",
                lambda duration=10: sa.record_audio(duration), category="capture",
            ))
            self._register(DesktopTool(
                "get_battery", "Check battery percentage and charging status",
                sa.get_battery_status, category="info",
            ))
            self._register(DesktopTool(
                "get_system_health", "Check CPU and RAM usage",
                sa.get_system_health, category="info",
            ))
            self._register(DesktopTool(
                "check_storage", "Check storage space on all drives",
                sa.check_storage, category="info",
            ))
            self._register(DesktopTool(
                "get_location", "Get approximate location via IP geolocation",
                sa.get_location, category="info",
            ))
            self._register(DesktopTool(
                "open_browser", "Open a URL in a web browser",
                lambda url, browser="default": sa.open_browser(url, browser),
                category="apps",
            ))
            self._register(DesktopTool(
                "close_app", "Close an application by name",
                lambda app_name: sa.close_application(app_name),
                category="apps",
            ))
            self._register(DesktopTool(
                "open_app", "Launch an application by name",
                lambda app_name: sa.open_application(app_name),
                category="apps",
            ))
            self._register(DesktopTool(
                "open_file", "Open a file or folder in the default handler",
                lambda path: sa.open_file_path(path),
                category="files",
            ))
            self._register(DesktopTool(
                "set_brightness", "Set screen brightness (0-100)",
                lambda level: sa.set_brightness(level),
                category="display",
            ))
            self._register(DesktopTool(
                "media_control", "Control media playback (playpause/next/prev/mute)",
                lambda action: sa.control_media(action),
                category="media",
            ))
            self._register(DesktopTool(
                "set_volume", "Set system volume (0-100)",
                lambda level: sa.set_volume(level),
                category="media",
            ))
            self._register(DesktopTool(
                "toggle_caffeine", "Toggle caffeine mode (prevent/allow sleep)",
                lambda state=True: sa.toggle_caffeine(state),
                category="power",
            ))

            # ── HIGH-RISK TOOLS (require confirmation) ──
            self._register(DesktopTool(
                "system_sleep", "Put the computer to sleep",
                sa.system_sleep, requires_confirmation=True, category="power",
            ))
            self._register(DesktopTool(
                "shutdown_pc", "Shut down the computer immediately",
                sa.shutdown_pc, requires_confirmation=True, category="power",
            ))
            self._register(DesktopTool(
                "restart_pc", "Restart the computer immediately",
                sa.restart_pc, requires_confirmation=True, category="power",
            ))
            self._register(DesktopTool(
                "system_panic", "EMERGENCY: minimize, mute, clear clipboard, lock PC",
                sa.system_panic, requires_confirmation=True, category="security",
            ))
            self._register(DesktopTool(
                "clear_recycle_bin", "Permanently empty the Recycle Bin",
                sa.clear_recycle_bin, requires_confirmation=True, category="system",
            ))

        except ImportError as e:
            print(f"⚠️ Desktop system_actions not available: {e}")

        # ── Activity Monitor ──
        try:
            from remember_me.desktop import activity

            self._register(DesktopTool(
                "get_activities", "Get current system activity (processes, windows, tabs)",
                activity.get_current_activities, category="info",
            ))
            self._register(DesktopTool(
                "get_browser_tabs", "Get recent browser tabs from all browsers",
                lambda limit=5: activity.get_browser_tabs(limit=limit),
                category="info",
            ))
        except ImportError:
            pass

    def _register(self, tool: DesktopTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[DesktopTool]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[DesktopTool]:
        return list(self._tools.values())

    def get_tools_by_category(self, category: str) -> List[DesktopTool]:
        return [t for t in self._tools.values() if t.category == category]

    def get_tool_descriptions(self) -> str:
        """Returns formatted tool list for LLM context injection."""
        lines = ["Available Desktop Tools:"]
        for tool in self._tools.values():
            confirm = " ⚠️ REQUIRES CONFIRMATION" if tool.requires_confirmation else ""
            lines.append(f"  • {tool.name}: {tool.description}{confirm}")
        return "\n".join(lines)

    def execute(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name. Raises KeyError if not found."""
        tool = self._tools.get(tool_name)
        if not tool:
            raise KeyError(f"Unknown tool: {tool_name}")
        return tool.execute(**kwargs)
