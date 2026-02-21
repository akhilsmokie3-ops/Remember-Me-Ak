#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REMEMBER-ME KERNEL v2.0
=======================
The Orchestration Layer.
Combines:
1. CSNP (Memory & Verification)
2. Engine (Inference)
3. Agent (Tools & execution)
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
    def __init__(self, model_key: str = "tiny"):
        logger.info("Initializing Cognitive Kernel...")
        
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
        
        logger.info("KERNEL ONLINE.")

    def run_cycle(self, user_input: str):
        logger.info(f"INPUT: '{user_input}'")
        
        # 1. Retrieve Context
        context = self.shield.retrieve_context()
        
        # 2. Agent Execution
        result = self.agent.run(user_input, context)
        
        response = result["response"]
        telemetry = result.get("telemetry", {})
        
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
            # Idle Consolidation
            self.shield.consolidate_memory()
        else:
            logger.warning("MEMORY: Update Skipped (Vetoed).")
            
        return response

    def shutdown(self):
        self.agent.shutdown()
        logger.info("SYSTEM SHUTDOWN.")

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
