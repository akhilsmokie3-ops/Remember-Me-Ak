import os
import sys
import time
import cmd
from remember_me.core.csnp import CSNPManager
from remember_me.integrations.engine import ModelRegistry
from remember_me.integrations.tools import ToolArsenal
from remember_me.integrations.agent import SovereignAgent

# ANSI Colors for Matrix Aesthetic
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

class CognitiveInterface(cmd.Cmd):
    intro = f"""
{GREEN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║  REMEMBER ME AI - AUTONOMOUS NEURAL INTERFACE v112.0         ║
║  Core: CSNP | Engine: Transformers | Orchestrator: ACTIVE    ║
║  Mode: ARCHITECT PRIME | Heart: SOUND | OIS: 10/100          ║
╚══════════════════════════════════════════════════════════════╝
{RESET}
System Ready.
Type '/model' to select a brain.
Type '/help' for commands.
    """
    prompt = f"{BLUE}USER > {RESET}"

    def __init__(self):
        super().__init__()
        print(f"{YELLOW}>>> INITIALIZING CSNP KERNEL...{RESET}")
        self.memory = CSNPManager(context_limit=15)
        self.engine = ModelRegistry()
        self.tools = ToolArsenal()
        self.agent = SovereignAgent(self.engine, self.tools)
        self.voice_enabled = False
        print(f"{GREEN}✓ KERNEL ACTIVE{RESET}")
        print(f"{CYAN}ℹ Info: No model loaded. Using Mock Mode until you select one with /model{RESET}")

    def precmd(self, line):
        if line.startswith('/'):
            return line[1:]
        return line

    def default(self, line):
        if not line.strip():
            return

        user_input = line

        # 1. Retrieve Context
        context_str = self.memory.retrieve_context()
        if context_str:
            print(f"{CYAN}[Memory Injected ({len(self.memory.text_buffer)} shards)]{RESET}")

        # 2. Run Orchestrator
        print(f"{YELLOW}[Orchestrating...]{RESET}")

        response = ""
        telemetry = {}

        # Use Agent
        result = self.agent.run(user_input, context_str)
        response = result["response"]
        telemetry = result.get("telemetry", {})

        # Display Telemetry (VNS)
        if "signal" in telemetry:
             sig = telemetry["signal"]
             print(f"{DIM}[SIGNAL: {sig['mode']} | URGENCY: {sig['urgency']:.2f} | THREAT: {sig['threat']:.2f}]{RESET}")

        if telemetry.get("veto", False):
             print(f"{RED}⛔ VETO TRIGGERED: {response}{RESET}")
             return

        # Print Tool Outputs
        for output in result["tool_outputs"]:
            print(f"{MAGENTA}{output.strip()}{RESET}")

        # Artifacts
        for artifact in result["artifacts"]:
            if artifact["type"] == "image":
                print(f"{MAGENTA}[Visual Artifact Created: {artifact['path']}]{RESET}")

        # Final Response
        print(f"{GREEN}AI   > {response}{RESET}")

        # Audit Telemetry
        if "audit" in telemetry:
             aud = telemetry["audit"]
             conf_color = GREEN if aud['confidence'] > 0.7 else (YELLOW if aud['confidence'] > 0.4 else RED)
             print(f"{DIM}[AUDIT: Confidence {conf_color}{aud['confidence']*100:.0f}%{RESET}{DIM} | Risk {aud['hallucination_risk']:.2f}]{RESET}")

        # 3. Voice Output
        if self.voice_enabled:
            self.tools.speak(response)

        # 4. Update Memory
        print(f"{YELLOW}[Consolidating...]{RESET}", end="\r")
        before_count = len(self.memory.text_buffer)

        self.memory.update_state(user_input, response)

        after_count = len(self.memory.text_buffer)

        if after_count == self.memory.context_limit and before_count == self.memory.context_limit:
            print(f"{RED}[⚡ COMPRESSION] Memory Full. Lowest mass evicted.{RESET}")
        else:
            print(f"{YELLOW}[✓ SAVED]{RESET}")

    def do_model(self, arg):
        """List or select a model. Usage: /model [key]"""
        if not arg:
            print(f"\n{BOLD}AVAILABLE MODELS:{RESET}")
            for key, info in self.engine.list_models().items():
                print(f" - {CYAN}{key}{RESET}: {info['name']} ({info['description']})")
            print("Usage: /model tiny")
            return

        key = arg.strip().lower()
        if key in self.engine.list_models():
            success = self.engine.load_model(key)
            if success:
                print(f"{GREEN}>>> SYSTEM UPGRADED: {self.engine.MODELS[key]['name']} ACTIVE{RESET}")
        else:
            print(f"{RED}Unknown model key.{RESET}")

    def do_voice(self, arg):
        """Toggle voice output. Usage: /voice on|off"""
        if arg == "on":
            self.voice_enabled = True
            print(f"{GREEN}Voice Output: ENABLED{RESET}")
        elif arg == "off":
            self.voice_enabled = False
            print(f"{RED}Voice Output: DISABLED{RESET}")
        else:
            print(f"Voice is currently: {'ENABLED' if self.voice_enabled else 'DISABLED'}")

    def do_status(self, arg):
        """Show system status."""
        print(f"\n{BOLD}--- SYSTEM STATUS ---{RESET}")
        print(f"Model: {self.engine.model_id if self.engine.model_id else 'None (Mock)'}")
        print(f"Memories: {len(self.memory.text_buffer)}")
        print(f"Integrity: {self.memory.identity_state.norm().item():.4f}")
        print(f"Context:\n{self.memory.retrieve_context()}")
        print("----------------------\n")

    def do_save(self, arg):
        """Save state. Usage: /save [file]"""
        filename = arg if arg else "brain.pt"
        self.memory.save_state(filename)

    def do_load(self, arg):
        """Load state. Usage: /load [file]"""
        filename = arg if arg else "brain.pt"
        self.memory.load_state(filename)

    def do_reset(self, arg):
        """Reset memory."""
        self.memory = CSNPManager(context_limit=15)
        print("Memory wiped.")

    def do_quit(self, arg):
        """Exit."""
        print("Shutting down.")
        return True

if __name__ == "__main__":
    try:
        CognitiveInterface().cmdloop()
    except KeyboardInterrupt:
        print("\nForce Quit.")
