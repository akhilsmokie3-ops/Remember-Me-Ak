import os
import threading
import customtkinter as ctk
from PIL import Image
import torch

from remember_me.core.csnp import CSNPManager
from remember_me.integrations.engine import ModelRegistry
from remember_me.integrations.tools import ToolArsenal
from remember_me.integrations.agent import SovereignAgent

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class RememberMeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Backend Initialization ---
        self.memory = CSNPManager(context_limit=15)
        self.engine = ModelRegistry()
        self.tools = ToolArsenal()
        self.agent = SovereignAgent(self.engine, self.tools)
        self.is_generating = False

        # --- Window Setup ---
        self.title("Remember Me AI - Sovereign Cognitive Interface v112.0")
        self.geometry("1100x700")

        # --- Grid Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Left) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Logo / Title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="REMEMBER ME", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Model Selector
        self.model_label = ctk.CTkLabel(self.sidebar_frame, text="Neural Engine:", anchor="w")
        self.model_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.model_option = ctk.CTkOptionMenu(self.sidebar_frame, values=list(self.engine.MODELS.keys()), command=self.change_model)
        self.model_option.grid(row=2, column=0, padx=20, pady=10)
        self.model_option.set("Select Model")

        # Capabilities Toggles
        self.voice_var = ctk.BooleanVar(value=False)
        self.voice_switch = ctk.CTkSwitch(self.sidebar_frame, text="Voice Output", variable=self.voice_var)
        self.voice_switch.grid(row=3, column=0, padx=20, pady=10)

        # Telemetry Visuals
        self.telemetry_label = ctk.CTkLabel(self.sidebar_frame, text="Nervous System:", anchor="w")
        self.telemetry_label.grid(row=4, column=0, padx=20, pady=(20, 0))

        self.signal_label = ctk.CTkLabel(self.sidebar_frame, text="Signal: IDLE", text_color="gray")
        self.signal_label.grid(row=5, column=0, padx=20, pady=5)

        self.confidence_label = ctk.CTkLabel(self.sidebar_frame, text="Confidence: --%", text_color="gray")
        self.confidence_label.grid(row=6, column=0, padx=20, pady=5)

        # Memory Status Visualizer
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Memory Integrity: 100%", text_color="#00ff00")
        self.status_label.grid(row=7, column=0, padx=20, pady=(20,0))

        self.progress_bar = ctk.CTkProgressBar(self.sidebar_frame)
        self.progress_bar.grid(row=8, column=0, padx=20, pady=10)
        self.progress_bar.set(0) # Usage

        # Persistence Buttons
        self.save_btn = ctk.CTkButton(self.sidebar_frame, text="Save Brain", command=self.save_brain)
        self.save_btn.grid(row=9, column=0, padx=20, pady=10)

        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="Load Brain", command=self.load_brain)
        self.load_btn.grid(row=10, column=0, padx=20, pady=(0, 20))

        # --- Main Chat Area (Right) ---
        self.chat_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.chat_frame.grid(row=0, column=1, sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Chat Log
        self.chat_box = ctk.CTkTextbox(self.chat_frame, width=250, font=ctk.CTkFont(size=14))
        self.chat_box.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        self.chat_box.configure(state="disabled") # Read only mostly

        # Input Area
        self.entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Type your message... (Try 'Calculate X' or 'Draw Y')")
        self.entry.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.entry.bind("<Return>", self.send_message_event)

        self.send_btn = ctk.CTkButton(self.chat_frame, text="Send", command=self.send_message)
        self.send_btn.grid(row=1, column=1, padx=(0, 20), pady=(0, 20))

        # --- Internal State ---
        self.print_system("System Initialized. Please select a Neural Engine from the sidebar.")

    def print_system(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"\n[SYSTEM]: {text}\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def print_user(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"\nUSER: {text}\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def print_ai(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"\nAI: {text}\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def change_model(self, choice):
        if choice == "Select Model": return

        def _load():
            self.print_system(f"Loading {choice}... This may take a moment.")
            success = self.engine.load_model(choice)
            if success:
                self.print_system(f"Engine Active: {choice}")
            else:
                self.print_system("Failed to load model.")

        threading.Thread(target=_load).start()

    def save_brain(self):
        self.memory.save_state("brain.pt")
        self.print_system("Cognitive State Saved to brain.pt")

    def load_brain(self):
        try:
            self.memory.load_state("brain.pt")
            self.print_system("Cognitive State Loaded.")
            self._update_status()
        except:
            self.print_system("No brain file found.")

    def send_message_event(self, event):
        self.send_message()

    def send_message(self):
        if self.is_generating: return
        user_input = self.entry.get()
        if not user_input.strip(): return

        self.entry.delete(0, "end")
        self.print_user(user_input)

        threading.Thread(target=self._process_input, args=(user_input,)).start()

    def _process_input(self, user_input):
        self.is_generating = True

        # 1. Retrieve Memory
        context = self.memory.retrieve_context()

        # 2. Run Orchestrator
        self.print_system("Orchestrating tools...")

        if self.engine.current_model:
            # Use the Agent to run the loop
            result = self.agent.run(user_input, context)

            telemetry = result.get("telemetry", {})
            response_text = result["response"]

            # Update Visuals
            self.after(0, self._update_telemetry, telemetry)

            if telemetry.get("veto", False):
                 self.print_system("VETO: Request Rejected.")
                 self.print_ai(response_text)
            else:
                # Display Tool Outputs
                for output in result["tool_outputs"]:
                    self.print_system(output.strip())

                # Display Final Response
                self.print_ai(response_text)
        else:
            time.sleep(0.5)
            response_text = "[MOCK AI]: Please load a model to chat."
            self.print_ai(response_text)

        # 3. Voice
        if self.voice_var.get():
            self.tools.speak(response_text)

        # 4. Update Memory
        if not telemetry.get("veto", False):
            self.memory.update_state(user_input, response_text)

        self.after(0, self._update_status)
        self.is_generating = False

    def _update_telemetry(self, telemetry):
        if "signal" in telemetry:
             sig = telemetry["signal"]
             self.signal_label.configure(text=f"Signal: {sig['mode']}", text_color="#00ffff")

        if "audit" in telemetry:
             aud = telemetry["audit"]
             conf = aud["confidence"] * 100
             color = "#00ff00" if conf > 70 else ("#ffff00" if conf > 40 else "#ff0000")
             self.confidence_label.configure(text=f"Confidence: {conf:.0f}%", text_color=color)

    def _update_status(self):
        # Update progress bar based on memory usage
        usage = len(self.memory.text_buffer) / self.memory.context_limit
        self.progress_bar.set(usage)

        # Update integrity label
        integrity = self.memory.identity_state.norm().item()
        self.status_label.configure(text=f"Integrity: {integrity:.2f}")

if __name__ == "__main__":
    app = RememberMeApp()
    app.mainloop()
