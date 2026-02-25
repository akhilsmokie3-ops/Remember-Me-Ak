"""
Tests for desktop/system_actions.py — Security Hardening Validation.
====================================================================
Validates that all os.system() calls have been replaced with subprocess.run(),
input validation rejects shell metacharacters, and the process whitelist works.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure the src path is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from remember_me.desktop.system_actions import (
    _validate_process_name,
    _validate_path,
    close_application,
    get_battery_status,
    get_system_health,
    check_storage,
    clear_recycle_bin,
    system_sleep,
    shutdown_pc,
    restart_pc,
    toggle_caffeine,
    open_browser,
    set_volume,
    control_media,
    PROCESS_NAMES,
)


# ─── INPUT VALIDATION ────────────────────────────────────────────────

class TestProcessNameValidation:
    """Validates that the process whitelist and sanitization work."""

    def test_whitelist_resolution(self):
        """Known apps resolve to their correct exe name."""
        assert _validate_process_name("chrome") == "chrome.exe"
        assert _validate_process_name("vscode") == "Code.exe"
        assert _validate_process_name("telegram") == "Telegram.exe"

    def test_whitelist_case_insensitive(self):
        assert _validate_process_name("CHROME") == "chrome.exe"
        assert _validate_process_name("Discord") == "Discord.exe"

    def test_noise_word_stripping(self):
        """'Close the app chrome' → 'chrome' → chrome.exe."""
        assert _validate_process_name("close the app chrome") == "chrome.exe"

    def test_unknown_app_gets_exe_suffix(self):
        """Unknown but safe names get .exe appended."""
        result = _validate_process_name("myapp")
        assert result == "myapp.exe"

    def test_shell_metachar_rejected_semicolon(self):
        with pytest.raises(ValueError, match="Rejected"):
            _validate_process_name("chrome; rm -rf /")

    def test_shell_metachar_rejected_pipe(self):
        with pytest.raises(ValueError, match="Rejected"):
            _validate_process_name("chrome | evil")

    def test_shell_metachar_rejected_backtick(self):
        with pytest.raises(ValueError, match="Rejected"):
            _validate_process_name("chrome`whoami`")

    def test_shell_metachar_rejected_ampersand(self):
        with pytest.raises(ValueError, match="Rejected"):
            _validate_process_name("chrome & malware")

    def test_shell_metachar_rejected_dollar(self):
        with pytest.raises(ValueError, match="Rejected"):
            _validate_process_name("$PATH")

    def test_shell_metachar_rejected_newline(self):
        with pytest.raises(ValueError, match="Rejected"):
            _validate_process_name("chrome\nmalicious")


class TestPathValidation:
    def test_normal_path_passes(self):
        assert _validate_path("C:\\Users\\test\\file.txt") == "C:\\Users\\test\\file.txt"

    def test_shell_metachar_rejected(self):
        with pytest.raises(ValueError, match="Rejected"):
            _validate_path("C:\\Users; rm -rf /")


# ─── SUBPROCESS ISOLATION ────────────────────────────────────────────

class TestSubprocessUsage:
    """Validates that system commands use subprocess.run(), not os.system()."""

    @patch("remember_me.desktop.system_actions.subprocess.run")
    def test_close_application_uses_subprocess(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = close_application("chrome")
        mock_run.assert_called_once()
        args = mock_run.call_args
        assert args[0][0] == ["taskkill", "/f", "/im", "chrome.exe", "/t"]

    @patch("remember_me.desktop.system_actions.subprocess.run")
    def test_clear_recycle_bin_uses_subprocess(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = clear_recycle_bin()
        mock_run.assert_called_once()
        assert "Clear-RecycleBin" in str(mock_run.call_args)

    @patch("remember_me.desktop.system_actions.subprocess.run")
    def test_system_sleep_uses_subprocess(self, mock_run):
        system_sleep()
        mock_run.assert_called_once()

    @patch("remember_me.desktop.system_actions.subprocess.run")
    def test_shutdown_uses_subprocess(self, mock_run):
        shutdown_pc()
        mock_run.assert_called_once()
        assert "shutdown" in str(mock_run.call_args)

    @patch("remember_me.desktop.system_actions.subprocess.run")
    def test_restart_uses_subprocess(self, mock_run):
        restart_pc()
        mock_run.assert_called_once()
        assert "/r" in str(mock_run.call_args)


# ─── VOLUME ──────────────────────────────────────────────────────────

class TestVolumeValidation:
    def test_volume_rejects_negative(self):
        result = set_volume(-1)
        assert "0 and 100" in result

    def test_volume_rejects_over_100(self):
        result = set_volume(200)
        assert "0 and 100" in result

    def test_volume_rejects_non_number(self):
        result = set_volume("loud")
        assert "number" in result


# ─── MEDIA CONTROL ───────────────────────────────────────────────────

class TestMediaControl:
    @patch("remember_me.desktop.system_actions._pyautogui")
    def test_valid_action(self, mock_pa):
        mock_pa.press = MagicMock()
        from remember_me.desktop import system_actions
        system_actions._pyautogui = mock_pa
        result = control_media("playpause")
        assert "playpause" in result

    def test_invalid_action(self):
        result = control_media("destroy")
        assert "Unknown" in result


# ─── CAFFEINE ────────────────────────────────────────────────────────

class TestCaffeine:
    def test_toggle_on_returns_active(self):
        # Reset state
        from remember_me.desktop import system_actions
        system_actions._caffeine_active = False
        with patch("threading.Thread"):
            result = toggle_caffeine(True)
        assert "Active" in result

    def test_double_toggle_on(self):
        from remember_me.desktop import system_actions
        system_actions._caffeine_active = True
        result = toggle_caffeine(True)
        assert "already active" in result.lower()

    def test_toggle_off(self):
        from remember_me.desktop import system_actions
        system_actions._caffeine_active = True
        result = toggle_caffeine(False)
        assert "Disabled" in result


# ─── NO os.system() IN SOURCE ────────────────────────────────────────

class TestNoOsSystem:
    """
    Meta-test: verify the source file contains zero os.system() calls.
    This is the most critical security invariant.
    """

    def test_no_os_system_in_system_actions(self):
        """
        Meta-test: verify executable code contains zero os.system() calls.
        Ignores comments and docstrings (which may reference os.system for documentation).
        """
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "remember_me", "desktop", "system_actions.py"
        )
        with open(src_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Extract only executable lines (not comments, not inside docstrings)
        in_docstring = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Toggle docstring state on triple-quote boundaries
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                    continue
                # One-liner docstring: """text"""
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    continue
                in_docstring = True
                continue
            if in_docstring:
                continue
            # Skip comments
            if stripped.startswith("#"):
                continue
            # This is executable code — must NOT contain os.system(
            assert "os.system(" not in line, (
                f"CRITICAL: os.system() found in executable code at line {i}: {line.strip()}"
            )
