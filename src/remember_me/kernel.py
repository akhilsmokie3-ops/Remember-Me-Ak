#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REMEMBER-ME KERNEL v3.0
=======================
The Orchestration Layer.
Combines:
1. CSNP (Memory & Verification)
2. Engine (Inference)
3. Agent (Tools & execution)
4. Desktop Layer (optional — system automation, voice, clipboard)
"""

import sys
import os
import argparse
import logging
from typing import Optional

# Configure Logging
logging.basicConfig(level=logging.INFO, format='[KERNEL|%(name)s] %(message)s')
logger = logging.getLogger("MAIN")

try:
    from .core.csnp import CSNPManager
    from .integrations.engine import ModelRegistry
    from .integrations.tools import ToolArsenal
    from .integrations.agent import SovereignAgent
except ImportError as e:
    # Fallback for when running as script (absolute imports)
    try:
        from remember_me.core.csnp import CSNPManager
        from remember_me.integrations.engine import ModelRegistry
        from remember_me.integrations.tools import ToolArsenal
        from remember_me.integrations.agent import SovereignAgent
    except ImportError:
        logger.critical(f"CRITICAL: Kernel module missing: {e}")
        # sys.exit(1) # Don't exit here to allow test mocking

class Kernel:
    def __init__(self, model_key: str = "tiny", enable_desktop: bool = True):
        logger.info("Initializing Cognitive Kernel v3.0...")
        
        # 1. BRAIN (Model Registry)
        logger.info("Booting Engine...")
        self.engine = ModelRegistry()
        if model_key:
             success = self.engine.load_model(model_key)
             if not success:
                 logger.warning(f"Failed to load model '{model_key}'. Running in Mock Mode.")
        
        # 2. SHIELD (CSNP)
        logger.info("Booting Shield (CSNP)...")
        self.shield = CSNPManager(context_limit=20)
        
        # 3. SOUL (Tools & Agent)
        logger.info("Booting Agent...")
        self.tools = ToolArsenal()
        self.agent = SovereignAgent(self.engine, self.tools)
        
        # 4. DESKTOP LAYER (optional)
        self.desktop_tools = None
        self._clipboard = None
        self._file_tracker = None
        
        if enable_desktop:
            self._boot_desktop()
        
        logger.info("KERNEL ONLINE.")

    def _boot_desktop(self):
        """Attempt to load desktop actuator layer. Fails gracefully."""
        try:
            from remember_me.desktop.desktop_tools import DesktopToolRegistry
            self.desktop_tools = DesktopToolRegistry()
            logger.info(f"Desktop Layer: {len(self.desktop_tools.get_all_tools())} tools loaded.")
        except ImportError:
            logger.info("Desktop Layer: Not available (missing dependencies).")
            return

        # Start background services
        try:
            from remember_me.desktop.clipboard import ClipboardMonitor
            self._clipboard = ClipboardMonitor()
            self._clipboard.start_monitoring()
            logger.info("Desktop: Clipboard monitor started.")
        except ImportError:
            pass

        try:
            from remember_me.desktop.files.tracker import FileTracker
            self._file_tracker = FileTracker()
            self._file_tracker.start()
            logger.info("Desktop: File tracker started.")
        except ImportError:
            pass

    def run_cycle(self, user_input: str):
        logger.info(f"INPUT: '{user_input}'")
        
        # 1. Retrieve Context (inject desktop tool list if available)
        context = self.shield.retrieve_context()
        if self.desktop_tools:
            context += "\n" + self.desktop_tools.get_tool_descriptions()
        
        # 2. Agent Execution
        result = self.agent.run(user_input, context)
        
        response = result["response"]
        telemetry = result.get("telemetry", {})
        
        # 2b. Desktop tool dispatch (if agent selected one)
        tool_call = result.get("tool_call")
        if tool_call and self.desktop_tools:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool = self.desktop_tools.get_tool(tool_name)
            if tool:
                if tool.requires_confirmation:
                    response += f"\n⚠️ Action '{tool_name}' requires confirmation."
                else:
                    try:
                        tool_result = tool.execute(**tool_args)
                        response = str(tool_result) if tool_result else response
                    except Exception as e:
                        logger.error(f"Desktop tool '{tool_name}' failed: {e}")
        
        # Log Telemetry
        if "signal" in telemetry:
             sig = telemetry["signal"]
             logger.info(f"SIGNAL: Mode={sig.get('mode', 'UNKNOWN')} | Urgency={sig.get('urgency', 0.0):.2f}")

        if "audit" in telemetry:
             aud = telemetry["audit"]
             logger.info(f"AUDIT: Conf={aud.get('confidence', 0.0):.2f}")

        # 3. Update Memory
        if not telemetry.get("veto", False):
            self.shield.update_state(user_input, response)
            logger.info("MEMORY: State Updated.")
            self.shield.consolidate_memory()
        else:
            logger.warning("MEMORY: Update Skipped (Vetoed).")
            
        return response

    def shutdown(self):
        # Stop desktop background services
        if self._clipboard:
            self._clipboard.stop_monitoring()
        if self._file_tracker:
            self._file_tracker.stop()
        self.agent.shutdown()
        logger.info("SYSTEM SHUTDOWN.")

    def execute_desktop_tool(self, tool_name: str, **kwargs):
        """Direct desktop tool execution (for Telegram/API adapters)."""
        if not self.desktop_tools:
            return "Desktop layer not available."
        return self.desktop_tools.execute(tool_name, **kwargs)

def main():
    parser = argparse.ArgumentParser(description="Cognitive Kernel Bootloader")
    parser.add_argument("--model", type=str, default="tiny", help="Model to load (tiny, small, medium)")
    args = parser.parse_args()

    kernel = Kernel(model_key=args.model)

    print("\n--- ENTERING INTERACTIVE MODE (Type 'exit' to quit) ---\n")
    try:
        while True:
            user_input = input("USER > ")
            if user_input.strip().lower() in ["exit", "quit"]:
                break

            response = kernel.run_cycle(user_input)
            print(f"AI   > {response}\n")
            
    except KeyboardInterrupt:
        print("\nForce Quit.")
    finally:
        kernel.shutdown()

if __name__ == "__main__":
    main()
