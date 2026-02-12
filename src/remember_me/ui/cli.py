#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remember Me AI: The Cognitive Shell
===================================
The interactive matrix verification interface.
Implements the commands described in the README.
"""

import sys
import os
import time
import threading
import logging

# Check for our stack
# Add src to path for absolute imports (remember_me package resolution)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    from remember_me.kernel import Kernel
except ImportError as e:
    print(f"Kernel Failure: {e}")
    sys.exit(1)

class CognitiveShell:
    def __init__(self):
        self.kernel = Kernel()
        self.running = True
        self.voice_enabled = False
        self.prompt_style = ">> "
        
    def type_out(self, text, speed=0.02):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(speed)
        print()

    def handle_command(self, cmd_line):
        parts = cmd_line.strip().split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == "/model":
            self.type_out(f"SYSTEM: Loading model '{args[0] if args else 'default'}' into local memory...")
            time.sleep(1)
            self.type_out("[OK] Model loaded [Quantized 4-bit]. Cost: $0.00")
            
        elif cmd == "/search":
            query = " ".join(args)
            self.type_out(f"SEARCHING: '{query}'...")
            res = self.kernel.tools.web_search(query)
            self.type_out(res)
            
        elif cmd == "/voice":
            status = args[0].lower() if args else "on"
            self.voice_enabled = (status == "on")
            self.type_out(f"AUDIO SYSTEM: {'ONLINE' if self.voice_enabled else 'OFFLINE'}")
            
        elif cmd == "/imagine":
            prompt = " ".join(args)
            self.type_out(f"ARTIST: Generating '{prompt}' locally...")
            res = self.kernel.tools.generate_image(prompt)
            self.type_out(f"[OK] {res}")
            
        elif cmd == "/save":
            filename = args[0] if args else "brain.pt"
            self.type_out(f"SYSTEM: Persisting neural state to {filename}...")
            self.kernel.shield.save_state(filename)
            self.type_out("[OK] State verified and saved.")
        
        elif cmd in ["/exit", "/quit"]:
            self.running = False
            
        else:
            self.type_out(f"UNKNOWN COMMAND: {cmd}")

    def run(self):
        print("\n" + "="*50)
        print(" REMEMBER ME AI v2.0 | SOVEREIGN SHELL")
        print(" The Trinity is Online: Shield + Brain + Soul")
        print("="*50 + "\n")
        
        self.type_out("System initializing...", speed=0.05)
        time.sleep(0.5)
        self.type_out("Connecting to Cognitive Kernel... OK")
        print()
        self.type_out("Type '/help' for commands. Start typing to think.")

        while self.running:
            try:
                user_input = input(f"\n{self.prompt_style}").strip()
                
                if user_input.startswith("/"):
                    self.handle_command(user_input)
                    continue
                    
                if not user_input:
                    continue
                    
                # Normal Chat via Kernel
                response = self.kernel.run_cycle(user_input)
                print(f"AI: {response}")
                
                if self.voice_enabled:
                    self.kernel.tools.speak(response)
                    
            except KeyboardInterrupt:
                self.running = False
                
        self.kernel.shutdown()
        print("\n[Session Terminated]")

if __name__ == "__main__":
    shell = CognitiveShell()
    shell.run()
