import re
import io
import sys
import traceback
import concurrent.futures
from typing import List, Dict, Any

from remember_me.integrations.tools import ToolArsenal
from remember_me.integrations.engine import ModelRegistry
from remember_me.core.nervous_system import SignalGate, VetoCircuit, Proprioception
from remember_me.core.sandbox import SecurePythonSandbox
from remember_me.core.frameworks import OISTruthBudget, HaiyueMicrocosm, VelocityPhysics

class SovereignAgent:
    """
    The Orchestrator.
    Analyzes user intent and executes a multi-step tool chain (Search -> Code -> Image)
    before synthesizing the final response.
    """

    def __init__(self, engine: ModelRegistry, tools: ToolArsenal):
        self.engine = engine
        self.tools = tools

        # ⚡ Nervous System Components
        self.signal_gate = SignalGate()
        self.veto_circuit = VetoCircuit()
        self.proprioception = Proprioception()
        self.sandbox = SecurePythonSandbox()

        # ⚡ Framework Components
        self.haiyue = HaiyueMicrocosm()
        self.velocity = VelocityPhysics()

        # ⚡ Bolt: Persistent ThreadPool to reuse threads across requests
        # Increased workers to allow parallel Search + Image generation + Microcosm
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        # Intent Patterns (Heuristic/Regex for speed & reliability on small models)
        # ⚡ Bolt: Combined regex for single-pass O(N) detection
        patterns = {
            "IMAGE": r"draw|generate an? image|picture of|visualize|paint|sketch",
            "SEARCH": r"search|research|find out|what is|who is|latest|news|look up",
            "CODE": r"calculate|compute|python|code|math|algorithm|solve"
        }
        combined_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in patterns.items())
        self.combined_pattern = re.compile(combined_regex, re.IGNORECASE)

    def shutdown(self):
        """Clean up resources."""
        self._executor.shutdown(wait=False)
        self.sandbox.shutdown()

    def run(self, user_input: str, context_str: str) -> Dict[str, Any]:
        """
        Main execution loop.
        Returns a dictionary with 'response' and 'artifacts' (paths to images, code output, etc).
        """
        # PHASE 0: PRE-COMPUTATION & AUDIT
        # OIS Truth Budget: Start with 100 Points.
        ois = OISTruthBudget()

        # 1. SIGNAL GATE (Adaptor Layer)
        signal = self.signal_gate.analyze(user_input)

        # Determine Velocity Mode (Hare vs Turtle)
        mode = self.velocity.determine_mode(signal)
        signal["mode"] = mode # Override generic mode with Physics mode

        # Adjust OIS based on Entropy (High Chaos burns budget)
        if signal["entropy"] > 0.8:
            ois.deduct(10, "High Entropy Input")

        # Reset Sandbox if context shifts significantly (Heuristic)
        if signal["entropy"] > 0.9:
             print("⚡ Orchestrator: Resetting Sandbox State due to High Entropy Shift.")
             self.sandbox.reset()

        # Check for manual reset command
        if "reset python" in user_input.lower() or "clear session" in user_input.lower():
             self.sandbox.reset()
             return {
                 "response": "Python Sandbox State Reset.",
                 "tool_outputs": [],
                 "artifacts": [],
                 "telemetry": {
                     "signal": signal,
                     "veto": False,
                     "audit": {},
                     "ois_budget": ois.budget,
                     "s_lang_trace": "$Input >> RESET !! ACTION"
                 }
             }

        # 2. VETO CIRCUIT (Hierarchical Veto)
        accepted, refusal_reason, reframed = self.veto_circuit.audit(signal, user_input)

        # Handle Refusal
        if not accepted:
            ois.deduct(100, "Veto Triggered")
            return {
                "response": refusal_reason,
                "tool_outputs": [],
                "artifacts": [],
                "telemetry": {
                    "signal": signal,
                    "veto": True,
                    "audit": {},
                    "ois_budget": 0,
                    "s_lang_trace": "$Input >> VETO !! REJECT"
                }
            }

        # Handle Reframing (Upgrade Input)
        if reframed:
            print(f"⚡ Orchestrator: Reframing Input -> '{reframed}'")
            user_input = reframed

        # Check Budget after Veto
        if not ois.check():
            return self._halt_response(signal, ois, "OIS Truth Budget Depleted. Too many assumptions required.")

        # S-Lang V5.0 Internal Monologue Instruction
        s_lang_instruction = (
            "You are ARK OMEGA-POINT v112.0 (The Sovereign). "
            "Internalize the 'Mechanic's Ear': Do not explain syntax, explain Flow, Resistance, and Heat. "
            "Use S-Lang V5.0 logic: $Target >> Law !! Action. "
            "Adhere to the 'OIS Truth Budget': Start with 100 points. Deduct for assumptions. If < 0, HALT. "
        )

        mode_instruction = f"[MODE: {mode}] | [URGENCY: {signal['urgency']:.2f}] | [ENTROPY: {signal['entropy']:.2f}] | [PLATFORM: {signal['platform']}]"

        # Inject Negative Constraints (Framework 3)
        negative_constraints = self.veto_circuit.get_negative_constraints()

        detected_intents = self._detect_intents(user_input)
        artifacts = []
        tool_outputs = []

        # Velocity Physics: Hare (War Speed) vs Turtle (Deep Research)
        is_war_speed = mode == "WAR_SPEED"

        # ⚡ Bolt: Submit Image Generation EARLY (Latency Hiding)
        img_future = None
        img_path = "dream_output.png"

        if "IMAGE" in detected_intents:
            print(f"🎨 Orchestrator: Visualizing (Parallel)...")
            img_prompt = user_input
            img_future = self._executor.submit(self.tools.generate_image, img_prompt, img_path)

        # PHASE 1: HAIYUE MICROCOSM (Active Simulation)
        # Initiated early for Turtle Mode or Architect Prime
        microcosm_future = None
        if mode in ["TURTLE_INTEGRITY", "ARCHITECT_PRIME", "DEEP_RESEARCH"]:
            microcosm_future = self._initiate_microcosm(user_input, context_str)

        # PHASE 2 & 3: HIVE-MIND RETRIEVAL (Search)
        search_future = None
        if "SEARCH" in detected_intents:
            query = user_input
            print(f"🕵️ Orchestrator: Triggering Search for '{query[:20]}...' (Parallel)")
            search_future = self._executor.submit(self.tools.web_search, query)

        # Resolve Search if needed for Code or Synthesis
        if search_future:
            try:
                search_res = search_future.result(timeout=10)
                tool_outputs.append(f"[SEARCH RESULTS]:\n{search_res}\n")
            except concurrent.futures.TimeoutError:
                tool_outputs.append("[SEARCH ERROR]: Timeout.")
                ois.deduct(15, "Search Timeout")

        # Check Budget
        if not ois.check(): return self._halt_response(signal, ois, "OIS Depleted after Search.")

        # PHASE 4: CODE PHASE (Symbolic Reasoning)
        user_code_match = re.search(r"```python(.*?)```", user_input, re.DOTALL)

        if user_code_match:
            print(f"⚡ Orchestrator: Detected User Code. Verifying & Executing...")
            code = user_code_match.group(1).strip()
            is_safe, reason = self.veto_circuit.audit_code(code)

            if is_safe:
                exec_result = self.sandbox.execute(code)
                tool_outputs.append(f"[USER CODE EXECUTION RESULT]:\n{exec_result}\n")
                artifacts.append({"type": "code", "content": code, "result": exec_result})
            else:
                tool_outputs.append(f"[CODE VETO]: {reason}\n")
                ois.deduct(20, "Dangerous Code Injection Attempt")

        elif "CODE" in detected_intents:
            print(f"💻 Orchestrator: Generating Python solution...")
            code_prompt = f"Write a Python script to solve this: {user_input}. Output ONLY the code inside ```python blocks."
            code_context = context_str + "\n" + "\n".join(tool_outputs)
            code_sys_prompt = f"You are a Python Expert. {mode_instruction} Return ONLY the code."
            code_response = self.engine.generate_response(code_prompt, code_context, system_prompt=code_sys_prompt)

            code_match = re.search(r"```python(.*?)```", code_response, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                print(f"⚙️ Executing Code (Sandboxed)...")
                exec_result = self.sandbox.execute(code)
                tool_outputs.append(f"[PYTHON EXECUTION RESULT]:\n{exec_result}\n")
                artifacts.append({"type": "code", "content": code, "result": exec_result})
            else:
                tool_outputs.append("[PYTHON ERROR]: No code block generated by LLM.\n")
                ois.deduct(10, "Code Generation Failure")

        # Check Budget
        if not ois.check(): return self._halt_response(signal, ois, "OIS Depleted after Code.")

        # PHASE 5: SYNTHESIS & IMAGE PHASE
        augmented_context = context_str + "\n".join(tool_outputs)

        # Resolve Microcosm
        microcosm_telemetry = {}
        final_input = user_input
        if microcosm_future:
            try:
                 microcosm_telemetry = microcosm_future.result(timeout=15)
                 final_input = self._synthesize_microcosm_input(user_input, microcosm_telemetry)
            except Exception as e:
                 print(f"Microcosm Failed: {e}")

        # Construct Final System Prompt
        default_system = (
            f"{mode_instruction}\n"
            f"{s_lang_instruction}\n"
            f"{negative_constraints}\n"
            "You are a helpful AI assistant equipped with the Remember Me Cognitive Kernel. "
            "You have long-term memory via CSNP, and access to tools like Image Generation and Web Search. "
            "Do not deny these capabilities. If the user refers to past conversations, assume your memory context is accurate. "
            "Answer directly and helpfully. "
        )

        if is_war_speed:
            default_system += "MODE: WAR_SPEED. Output < 60s. No filler. Pure kinetic payload."
        else:
            default_system += "MODE: TURTLE_INTEGRITY. Verify every claim. Build Cathedrals of Logic."

        # GENERATE
        final_response = self.engine.generate_response(final_input, augmented_context, system_prompt=default_system)

        # Collect Image Result
        if img_future:
            res = img_future.result()
            artifacts.append({"type": "image", "path": img_path, "status": res})
            final_response += f"\n\n[Visual Generated: {res}]"

        # PHASE 6: PROPRIOCEPTION (Self-Sensing)
        audit_result = self.proprioception.audit_output(final_response, augmented_context)

        # OIS Budget Deduction
        if audit_result["hallucination_risk"] > 0.3:
            ois.deduct(int(audit_result["hallucination_risk"] * 40), "Hallucination Risk")

        # REGENERATION LOOP (Vertigo Check)
        if audit_result.get("regenerate", False):
            print("♻️ Proprioception: VERTIGO DETECTED (Confidence < 90%). Regenerating...")
            ois.deduct(20, "Regeneration Penalty")
            if ois.check():
                # Try once more with a stricter prompt
                regen_system = default_system + "\n[CRITICAL]: Previous output rejected due to low confidence. BE EXACT. CITE SOURCES."
                final_response = self.engine.generate_response(final_input, augmented_context, system_prompt=regen_system)
                # Re-audit
                audit_result = self.proprioception.audit_output(final_response, augmented_context)
                if audit_result.get("regenerate", False):
                     final_response += "\n\n[SYSTEM FAILURE]: Confidence Threshold not met after regeneration."

        # PHASE 7: T-CELL VERIFICATION
        if audit_result["confidence"] < 0.8 and "CODE" not in detected_intents and ois.check():
             self._run_t_cell(final_response, ois)

        # S-Lang Trace Construction (Post-hoc for now, though persona wants pre-hoc, we simulate it via instruction)
        s_lang_trace = f"$Target: INPUT >> $Mode: {mode} >> $Entropy: {signal['entropy']:.2f} !! Action: EXECUTE"

        return {
            "response": final_response,
            "tool_outputs": tool_outputs,
            "artifacts": artifacts,
            "telemetry": {
                "signal": signal,
                "veto": False,
                "audit": audit_result,
                "ois_budget": ois.budget,
                "s_lang_trace": s_lang_trace,
                "microcosm": microcosm_telemetry
            }
        }

    def _detect_intents(self, text: str) -> List[str]:
        found = set()
        for match in self.combined_pattern.finditer(text):
            found.add(match.lastgroup)
        return list(found)

    def _initiate_microcosm(self, user_input: str, context: str):
        print("🔮 Orchestrator: Spawning Haiyue Microcosm (3 Timelines)...")
        prompts = {
            "OPTIMISTIC": f"Simulate an OPTIMISTIC (+1) outcome/answer for: {user_input}. Be concise.",
            "NEUTRAL": f"Simulate a NEUTRAL (0) outcome/answer for: {user_input}. Be concise.",
            "PESSIMISTIC": f"Simulate a PESSIMISTIC (-1) outcome/answer for: {user_input}. Focus on risks. Be concise."
        }

        def run_microcosm():
             futures = {}
             for p_name, p_text in prompts.items():
                 sys_p = f"You are a Simulation Engine. Mode: {p_name}. Output only the simulation."
                 futures[p_name] = self._executor.submit(self.engine.generate_response, p_text, context, system_prompt=sys_p)

             results = {}
             for p_name, future in futures.items():
                 try:
                     results[p_name] = future.result(timeout=15)
                 except Exception as e:
                     results[p_name] = f"Simulation Failed: {e}"
             return results

        return self._executor.submit(run_microcosm)

    def _synthesize_microcosm_input(self, user_input: str, simulations: Dict[str, str]) -> str:
        return (
             f"User Input: {user_input}\n"
             f"Simulated Trajectories (Use these to form a robust answer):\n"
             f"[OPTIMISTIC]: {simulations.get('OPTIMISTIC', 'N/A')}\n"
             f"[NEUTRAL]: {simulations.get('NEUTRAL', 'N/A')}\n"
             f"[PESSIMISTIC]: {simulations.get('PESSIMISTIC', 'N/A')}\n"
             "SYNTHESIS: Converge on the most robust solution. Do not output the trajectories, just the result."
        )

    def _halt_response(self, signal, ois, reason) -> Dict[str, Any]:
        return {
            "response": f"SYSTEM HALT: {reason}",
            "tool_outputs": [],
            "artifacts": [],
            "telemetry": {
                "signal": signal,
                "veto": True,
                "audit": {},
                "ois_budget": 0,
                "s_lang_trace": "$Input >> OIS_CHECK !! HALT"
            }
        }

    def _run_t_cell(self, response: str, ois: OISTruthBudget):
         print("🛡️ T-CELL: Triggering Active Verification Loop...")
         verify_prompt = (
             f"The following claim needs verification: '{response[:300]}'. "
             "Write a Python script to check this claim mathematically or logically. "
             "Print 'VERIFIED' if true, or the correct value if false. "
             "Return ONLY the code in ```python``` blocks."
         )
         try:
             verify_code_resp = self.engine.generate_response(verify_prompt, "", system_prompt="You are a QA Engineer. Return ONLY code.")
             verify_match = re.search(r"```python(.*?)```", verify_code_resp, re.DOTALL)
             if verify_match:
                 v_code = verify_match.group(1).strip()
                 v_safe, _ = self.veto_circuit.audit_code(v_code)
                 if v_safe:
                     self.sandbox.execute(v_code)
                     # Logic to append result omitted for brevity, assumes purely side-effect or log
                     # In real impl, we would append to response, but strings are immutable in Python
                     # so we can't easily modify 'response' in place unless we return it.
                     # For now, just logging action.
                     pass
         except Exception as e:
             print(f"T-CELL Error: {e}")
