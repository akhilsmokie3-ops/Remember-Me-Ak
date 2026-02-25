"""
Tests for desktop/desktop_tools.py — Tool Registry Validation.
===============================================================
Validates that tools register correctly, execute via the registry, and
high-risk tools are flagged with requires_confirmation.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from remember_me.desktop.desktop_tools import DesktopToolRegistry, DesktopTool


class TestToolRegistration:
    """Validates that all expected tools are registered."""

    def setup_method(self):
        self.registry = DesktopToolRegistry()

    def test_registry_has_tools(self):
        tools = self.registry.get_all_tools()
        assert len(tools) > 0, "Registry should have registered tools"

    def test_core_tools_present(self):
        expected = [
            "take_screenshot", "get_battery", "get_system_health",
            "check_storage", "open_browser", "close_app",
        ]
        for name in expected:
            tool = self.registry.get_tool(name)
            assert tool is not None, f"Tool '{name}' should be registered"

    def test_unknown_tool_returns_none(self):
        assert self.registry.get_tool("nonexistent_tool_xyz") is None


class TestHighRiskTools:
    """High-risk tools must have requires_confirmation = True."""

    def setup_method(self):
        self.registry = DesktopToolRegistry()

    def test_shutdown_requires_confirmation(self):
        tool = self.registry.get_tool("shutdown_pc")
        assert tool is not None
        assert tool.requires_confirmation is True

    def test_restart_requires_confirmation(self):
        tool = self.registry.get_tool("restart_pc")
        assert tool is not None
        assert tool.requires_confirmation is True

    def test_system_sleep_requires_confirmation(self):
        tool = self.registry.get_tool("system_sleep")
        assert tool is not None
        assert tool.requires_confirmation is True

    def test_system_panic_requires_confirmation(self):
        tool = self.registry.get_tool("system_panic")
        assert tool is not None
        assert tool.requires_confirmation is True

    def test_clear_recycle_bin_requires_confirmation(self):
        tool = self.registry.get_tool("clear_recycle_bin")
        assert tool is not None
        assert tool.requires_confirmation is True


class TestToolExecution:
    """Validates tool execution through the registry."""

    def setup_method(self):
        self.registry = DesktopToolRegistry()

    def test_execute_unknown_tool_raises(self):
        with pytest.raises(KeyError, match="Unknown tool"):
            self.registry.execute("nonexistent_tool_xyz")

    def test_execute_battery_check(self):
        """Test battery tool executes and returns a string."""
        result = self.registry.execute("get_battery")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_execute_health_check(self):
        """Test health tool executes and returns a string."""
        result = self.registry.execute("get_system_health")
        assert isinstance(result, str)
        assert len(result) > 0


class TestToolDescriptions:
    """Validates the LLM-injectable tool description output."""

    def test_descriptions_format(self):
        registry = DesktopToolRegistry()
        desc = registry.get_tool_descriptions()
        assert "Available Desktop Tools:" in desc
        assert "take_screenshot" in desc

    def test_confirmation_flag_in_descriptions(self):
        registry = DesktopToolRegistry()
        desc = registry.get_tool_descriptions()
        assert "REQUIRES CONFIRMATION" in desc


class TestToolCategories:
    """Validates tool category filtering."""

    def setup_method(self):
        self.registry = DesktopToolRegistry()

    def test_capture_category(self):
        capture_tools = self.registry.get_tools_by_category("capture")
        names = [t.name for t in capture_tools]
        assert "take_screenshot" in names

    def test_power_category(self):
        power_tools = self.registry.get_tools_by_category("power")
        names = [t.name for t in power_tools]
        assert "shutdown_pc" in names

    def test_info_category_has_multiple(self):
        info_tools = self.registry.get_tools_by_category("info")
        assert len(info_tools) >= 3


class TestDesktopToolModel:
    """Unit tests for the DesktopTool class itself."""

    def test_to_dict(self):
        tool = DesktopTool("test_tool", "A test tool", lambda: "ok", category="test")
        d = tool.to_dict()
        assert d["name"] == "test_tool"
        assert d["category"] == "test"
        assert d["requires_confirmation"] is False

    def test_execute(self):
        tool = DesktopTool("test_tool", "A test tool", lambda: "executed")
        assert tool.execute() == "executed"

    def test_execute_with_kwargs(self):
        tool = DesktopTool("test_tool", "A test tool", lambda x=1: x * 10)
        assert tool.execute(x=5) == 50
