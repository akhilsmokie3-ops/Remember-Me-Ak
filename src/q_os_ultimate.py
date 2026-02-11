#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q-OS ULTIMATE v112.0: The Sovereign Trinity
===========================================
1. The Shield (CSNP): Mathematical Truth Validator
2. The Brain (QDMA): Model Registry & Inference
3. The Soul (Yggdrasil): Tool Arsenal & Agent

"Where Truth meets Meaning, Life emerges."
"""

import sys
import os
import argparse
import logging
from typing import Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Logging
logging.basicConfig(level=logging.INFO, format='[Q-OS|%(name)s] %(message)s')
logger = logging.getLogger("KERNEL")

try:
    from remember_me.core.csnp import CSNPManager
    from remember_me.integrations.engine import ModelRegistry
    from remember_me.integrations.tools import ToolArsenal
    from remember_me.integrations.agent import SovereignAgent
except ImportError as e:
    logger.critical(f"CRITICAL: Kernel module missing: {e}")
    sys.exit(1)

class Q_OS_Trinity:
    def __init__(self, model_key: str = "tiny"):
        logger.info("Initializing Sovereign Trinity v112.0...")
        
        # 1. BRAIN (Model Registry)
        logger.info("Booting Brain (Engine)...")
        self.engine = ModelRegistry()
        if model_key:
             success = self.engine.load_model(model_key)
             if not success:
                 logger.warning(f"Failed to load model '{model_key}'. Running in Mock Mode.")
        
        # 2. SHIELD (CSNP)
        logger.info("Booting Shield (CSNP)...")
        self.shield = CSNPManager(context_limit=20)
        
        # 3. SOUL (Tools & Agent)
        logger.info("Booting Soul (Agent)...")
        self.tools = ToolArsenal()
        self.agent = SovereignAgent(self.engine, self.tools)
        
        logger.info("SYSTEM ONLINE. TRINARY READY.")

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
             logger.info(f"SIGNAL: Mode={sig['mode']} | Urgency={sig['urgency']:.2f}")

        if "audit" in telemetry:
             aud = telemetry["audit"]
             logger.info(f"AUDIT: Conf={aud['confidence']:.2f} | Risk={aud['hallucination_risk']:.2f}")

        # 3. Update Memory
        if not telemetry.get("veto", False):
            self.shield.update_state(user_input, response)
            logger.info("MEMORY: State Updated.")
        else:
            logger.warning("MEMORY: Update Skipped (Vetoed).")
            
        return response

    def shutdown(self):
        self.agent.shutdown()
        logger.info("SYSTEM SHUTDOWN.")

def main():
    parser = argparse.ArgumentParser(description="Q-OS Ultimate Bootloader")
    parser.add_argument("--model", type=str, default="tiny", help="Model to load (tiny, small, medium)")
    args = parser.parse_args()

    qos = Q_OS_Trinity(model_key=args.model)

    print("\n--- ENTERING INTERACTIVE MODE (Type 'exit' to quit) ---\n")
    try:
        while True:
            user_input = input("USER > ")
            if user_input.strip().lower() in ["exit", "quit"]:
                break

            response = qos.run_cycle(user_input)
            print(f"AI   > {response}\n")
            
    except KeyboardInterrupt:
        print("\nForce Quit.")
    finally:
        qos.shutdown()

if __name__ == "__main__":
    main()
