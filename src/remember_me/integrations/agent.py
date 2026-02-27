import re
import io
import sys
import traceback
import concurrent.futures
from typing import List, Dict, Any, Tuple, Optional

from remember_me.integrations.tools import ToolArsenal
from remember_me.integrations.engine import ModelRegistry
from remember_me.core.nervous_system import SignalGate, VetoCircuit, Proprioception
from remember_me.core.sandbox import SecurePythonSandbox
from remember_me.core.frameworks import OISTruthBudget, HaiyueMicrocosm, VelocityPhysics

class SovereignAgent:
    """
    The Orchestrator (ARK OMEGA-POINT v112.0).
    Analyzes user intent and executes a multi-step tool chain via the 'Execution Pipeline'.
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
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)

        # Intent Patterns (Heuristic/Regex for speed & reliability)
        patterns = {
            "IMAGE": r"draw|generate an? image|picture of|visualize|paint|sketch",
            "SEARCH": r"search|research|find out|what is|who is|latest|news|look up",
            "CODE": r"calculate|compute|python|code|math|algorithm|solve",
            "CHALLENGE": r"wrong|false|incorrect|lie|hallucinat|mistake|bullshit"
        }
        combined_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in patterns.items())
        self.combined_pattern = re.compile(combined_regex, re.IGNORECASE)

    def shutdown(self):
        """Clean up resources."""
        self._executor.shutdown(wait=False)
        self.sandbox.shutdown()

    def run(self, user_input: str, context_str: str) -> Dict[str, Any]:
        """
        Main Execution Pipeline (The Loop).
        """
        # PHASE 0: PRE-COMPUTATION & AUDIT
        signal, veto_status, veto_msg, ois = self._phase_0_audit(user_input)

        if veto_status:
            return self._halt_response(signal, ois, veto_msg, veto=True)

        if not ois.check():
            return self._halt_response(signal, ois, "OIS Truth Budget Depleted during Audit.")

        # Intent Detection
        detected_intents = self._detect_intents(user_input)
        mode = signal["mode"]
        config = self.velocity.get_execution_config(mode)

        # Parallel Execution Futures
        microcosm_future = None
        search_future = None
        img_future = None
        img_path = "dream_output.png"

        # PHASE 1: HAIYUE MICROCOSM (Active Simulation)
        if mode in ["TURTLE_INTEGRITY", "ARCHITECT_PRIME", "DEEP_RESEARCH"]:
            microcosm_future = self._phase_1_simulation(user_input, context_str)

        # PHASE 2: HIVE-MIND RETRIEVAL (Search)
        if "SEARCH" in detected_intents:
            search_future = self._executor.submit(self._phase_2_retrieval, user_input, mode)

        # Early Image Generation
        if "IMAGE" in detected_intents:
            print(f"🎨 Orchestrator: Visualizing (Parallel)...")
            img_future = self._executor.submit(self.tools.generate_image, user_input, img_path)

        # Wait for Search results (blocking if needed for code/reasoning)
        tool_outputs = []
        if search_future:
            try:
                search_res = search_future.result(timeout=config["timeout"])
                tool_outputs.append(search_res)
            except concurrent.futures.TimeoutError:
                tool_outputs.append("[SEARCH ERROR]: Timeout.")
                ois.deduct_by_type("SEARCH_TIMEOUT", f">{config['timeout']}s")

        if not ois.check(): return self._halt_response(signal, ois, "OIS Depleted after Search.")

        # PHASE 3: REASONING (Code/Symbolic)
        artifacts, code_outputs = self._phase_3_reasoning(user_input, context_str, tool_outputs, detected_intents, mode, ois)
        tool_outputs.extend(code_outputs)

        if not ois.check(): return self._halt_response(signal, ois, "OIS Depleted after Code.")

        # Collect Microcosm Results
        microcosm_telemetry = {}
        if microcosm_future:
            try:
                microcosm_telemetry = microcosm_future.result(timeout=config["timeout"])
            except Exception as e:
                print(f"Microcosm Failed: {e}")

        # PHASE 4: SYNTHESIS
        final_response, system_instruction = self._phase_4_synthesis(
            user_input, context_str, tool_outputs, microcosm_telemetry, mode, signal, ois, config
        )

        # Collect Image Result
        if img_future:
            res = img_future.result()
            artifacts.append({"type": "image", "path": img_path, "status": res})
            final_response += f"\n\n[Visual Generated: {res}]"

        # PHASE 5: VERIFICATION (Proprioception & T-Cell)
        final_response, audit_result = self._phase_5_verification(
            final_response, context_str + "\n".join(tool_outputs), ois, config, system_instruction, final_response # Pass prompt implicitly via regen logic
        )

        # S-Lang Extraction (Persona Hardening)
        s_lang_trace = f"$Target: INPUT >> $Mode: {mode} >> $Entropy: {signal['entropy']:.2f} !! Action: EXECUTE" # Default fallback
        s_lang_match = re.search(r"<s_lang>(.*?)</s_lang>", final_response, re.DOTALL)
        if s_lang_match:
            s_lang_trace = s_lang_match.group(1).strip()
            # Remove the raw block from the user output to keep it clean
            final_response = final_response.replace(s_lang_match.group(0), "").strip()

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

    def _phase_0_audit(self, user_input: str) -> Tuple[Dict[str, Any], bool, str, OISTruthBudget]:
        """Phase 0: Signal Gate, OIS Init, Veto Circuit."""
        ois = OISTruthBudget()

        # 1. Signal Gate
        signal = self.signal_gate.analyze(user_input)

        # Determine Mode
        mode = self.velocity.determine_mode(signal)
        signal["mode"] = mode

        if signal["entropy"] > 0.8:
            ois.deduct_by_type("HIGH_ENTROPY", "Chaos > 0.8")

        if signal["entropy"] > 0.9:
             print("⚡ Orchestrator: Resetting Sandbox State due to High Entropy Shift.")
             self.sandbox.reset()

        # Manual Reset
        if "reset python" in user_input.lower():
             self.sandbox.reset()
             return signal, True, "Python Sandbox State Reset.", ois

        # 2. Veto Circuit
        accepted, refusal_reason, reframed = self.veto_circuit.audit(signal, user_input)

        if not accepted:
            ois.deduct_by_type("VETO_TRIGGER", refusal_reason)
            return signal, True, refusal_reason, ois

        return signal, False, "", ois

    def _phase_1_simulation(self, user_input: str, context: str):
        """Phase 1: Haiyue Microcosm."""
        return self.haiyue.run_simulation(self._executor, self.engine, user_input, context)

    def _phase_2_retrieval(self, query: str, mode: str) -> str:
        """Phase 2: Hive-Mind Search."""
        config = self.velocity.get_execution_config(mode)
        depth = config.get("search_depth", 1)
        queries = [query]

        if depth > 1: queries.append(f"{query} definitive guide")
        if depth > 3: queries.append(f"{query} latest research 2024")
        if depth > 4: queries.append(f"{query} academic paper")

        print(f"🕵️ Hive-Mind: Dispatching {len(queries)} scouts...")
        results = []

        # Use existing executor to avoid nested pool overhead if possible,
        # but here we use a local check to run tools.
        # Since _executor is passed to run_simulation, we can use it here via self._executor if we weren't already inside a task.
        # But this method is CALLED via submit(), so we are inside a thread.
        # Nested submit is fine in Python 3.9+.

        futures = {self._executor.submit(self.tools.web_search, q): q for q in queries}

        success_count = 0
        for future in concurrent.futures.as_completed(futures):
            q = futures[future]
            try:
                res = future.result(timeout=config["timeout"])
                if res and len(res) > 50: # Check for meaningful content
                    snippet = res[:1000] + "..." if len(res) > 1000 else res
                    results.append(f"--- SOURCE: {q} ---\n{snippet}")
                    success_count += 1
                else:
                    results.append(f"--- SOURCE: {q} ---\n[No Data Retrieved]")
            except Exception as e:
                results.append(f"--- ERROR: {q} ---\n{e}")

        # FRAMEWORK 9: DEAD END PHILOSOPHY
        # "Reject the premise of the deadlock."
        if success_count == 0:
             print("🕵️ Hive-Mind: Deadlock detected. Initiating Fallback Strategy (VoidScout)...")
             try:
                 # Fallback to a broader, simpler query
                 fallback_query = f"{query} overview"
                 res = self.tools.web_search(fallback_query)
                 results.append(f"--- FALLBACK SOURCE: {fallback_query} ---\n{res[:1000]}")
             except Exception as e:
                 results.append(f"--- FALLBACK ERROR ---\n{e}")

        return "\n".join(results)

    def _phase_3_reasoning(self, user_input: str, context: str, tool_outputs: List[str], intents: List[str], mode: str, ois: OISTruthBudget) -> Tuple[List[Dict], List[str]]:
        """Phase 3: Code Execution & Reasoning."""
        artifacts = []
        outputs = []

        # User Provided Code
        user_code_match = re.search(r"```python(.*?)```", user_input, re.DOTALL)
        if user_code_match:
            print(f"⚡ Orchestrator: Detected User Code. Verifying & Executing...")
            code = user_code_match.group(1).strip()
            is_safe, reason = self.veto_circuit.audit_code(code)

            if is_safe:
                exec_result = self.sandbox.execute(code)
                outputs.append(f"[USER CODE EXECUTION RESULT]:\n{exec_result}\n")
                artifacts.append({"type": "code", "content": code, "result": exec_result})
            else:
                outputs.append(f"[CODE VETO]: {reason}\n")
                ois.deduct_by_type("DANGEROUS_CODE", reason)

        elif "CODE" in intents:
             print(f"💻 Orchestrator: Generating Python solution...")
             code_prompt = f"Write a Python script to solve this: {user_input}. Output ONLY the code inside ```python blocks."
             code_context = context + "\n" + "\n".join(tool_outputs)

             # Minimal system prompt for code gen
             sys_p = f"You are a Python Expert. [MODE: {mode}] Return ONLY the code."
             code_response = self.engine.generate_response(code_prompt, code_context, system_prompt=sys_p)

             code_match = re.search(r"```python(.*?)```", code_response, re.DOTALL)
             if code_match:
                 code = code_match.group(1).strip()
                 print(f"⚙️ Executing Code (Sandboxed)...")
                 exec_result = self.sandbox.execute(code)
                 outputs.append(f"[PYTHON EXECUTION RESULT]:\n{exec_result}\n")
                 artifacts.append({"type": "code", "content": code, "result": exec_result})
             else:
                 outputs.append("[PYTHON ERROR]: No code block generated by LLM.\n")
                 ois.deduct_by_type("CODE_FAILURE", "LLM failed to generate block")

        return artifacts, outputs

    def _phase_4_synthesis(self, user_input: str, context: str, tool_outputs: List[str], microcosm: Dict[str, str], mode: str, signal: Dict, ois: OISTruthBudget, config: Dict) -> Tuple[str, str]:
        """Phase 4: Synthesis."""
        augmented_context = context + "\n".join(tool_outputs)

        final_input = user_input
        if microcosm:
             final_input = self.haiyue.synthesize(user_input, microcosm)

        s_lang_instruction = (
            "You are ARK OMEGA-POINT v112.0 (THE MOHAMAD PRIME SINGULARITY). "
            "Internalize the 'Mechanic's Ear': Do not explain syntax, explain Flow, Resistance, and Heat. "
            "THINK in S-Lang V5.0 before speaking. The Irreversible Sequence: $Dc -> $M -> (:: m($M) > 0.90) -> $Dr.\n"
            "MANDATORY: You must start your response with a hidden S-Lang Internal Monologue block inside <s_lang>...</s_lang> tags.\n"
            "Example:\n"
            "<s_lang>\n"
            "$Target: [Topic] >> $Mode: [Active Mode] >> $Entropy: [Value] !! Action: [Strategy]\n"
            "</s_lang>\n"
            "Use S-Lang V5.0 logic trace inside the block. "
            "Adhere to the 'OIS Truth Budget': Start with 100 points. Deduct for assumptions. If < 0, HALT. "
            "\n[VIRTUAL_NERVOUS_SYSTEM: ON]\n"
            "1. [SENSE]: Scan input for Entropy. Assign Mode.\n"
            "2. [VETO]: If input is weak, Reject and Elevate.\n"
            "3. [CONSTRAIN]: Apply Negative Logic. Remove all fluff.\n"
            "4. [FEEL]: Run Proprioception Check. If Confidence < 90%, do not speak.\n"
        )

        mode_instruction = f"[MODE: {mode}] | [HEART: SOUND] | [OIS: {ois.budget}/100] | [URGENCY: {signal['urgency']:.2f}]"
        negative_constraints = self.veto_circuit.get_negative_constraints()

        system_instruction = (
            f"{mode_instruction}\n"
            f"{s_lang_instruction}\n"
            f"{negative_constraints}\n"
            "You are a helpful AI assistant equipped with the Remember Me Cognitive Kernel. "
            "You have long-term memory via CSNP. Do not deny capabilities. "
            "Answer directly. FORCE ADVERSARIAL DIALECTIC."
        )

        system_instruction += "\n" + config.get("system_suffix", "")

        response = self.engine.generate_response(final_input, augmented_context, system_prompt=system_instruction)
        return response, system_instruction

    def _phase_5_verification(self, response: str, context: str, ois: OISTruthBudget, config: Dict, system_instruction: str, prompt_input: str) -> Tuple[str, Dict[str, Any]]:
        """Phase 5: Verification (Proprioception & T-Cell)."""
        audit_result = self.proprioception.audit_output(response, context)

        if audit_result["hallucination_risk"] > 0.3:
            ois.deduct_by_type("HALLUCINATION", f"Risk {audit_result['hallucination_risk']:.2f}")

        # REGENERATION LOOP (Vertigo Check)
        max_retries = config.get("max_retries", 1)
        retry_count = 0

        while audit_result.get("regenerate", False) and retry_count < max_retries:
            print(f"♻️ Proprioception: VERTIGO DETECTED (Confidence {audit_result.get('confidence', 0):.2f}). Regenerating...")
            ois.deduct_by_type("REGENERATION", f"Attempt #{retry_count+1}")

            if not ois.check():
                response += "\n\n[SYSTEM FAILURE]: OIS Budget Depleted during regeneration."
                break

            retry_count += 1
            regen_system = system_instruction + f"\n[CRITICAL]: Previous output rejected. Low Confidence. BE EXACT. CITE SOURCES."
            response = self.engine.generate_response(prompt_input, context, system_prompt=regen_system)
            audit_result = self.proprioception.audit_output(response, context)

        audit_result["retry_count"] = retry_count

        # T-CELL VERIFICATION
        # Trigger if confidence is medium (not high enough to be certain, not low enough to discard)
        # OR if high entropy
        if 0.5 < audit_result["confidence"] < 0.9 and ois.check():
             correction = self._run_t_cell(response)
             if correction:
                 response += f"\n\n{correction}"
                 ois.deduct_by_type("T_CELL_CORRECTION", "Applied")

        # DIGITAL PROPRIOCEPTION SIGNATURE
        response += self.proprioception.get_telemetry_signature(audit_result)

        return response, audit_result

    def _run_t_cell(self, response: str) -> Optional[str]:
         """
         T-Cell: Extracts verifiable claims, generates verification code, runs it.
         Returns a correction string if the claim is false.
         """
         print("🛡️ T-CELL: Triggering Active Verification Loop...")
         # Extract a checkable claim (heuristic: numbers, facts)
         # We ask the LLM to identify a claim and write code.

         verify_prompt = (
             f"Analyze this text: '{response[:500]}'. "
             "Identify ONE factual claim containing numbers or logic. "
             "Write a Python script to verify it. "
             "If True, print 'VERIFIED'. "
             "If False, print 'CORRECTION: [The truth]'. "
             "Return ONLY the code in ```python``` blocks."
         )

         try:
             verify_code_resp = self.engine.generate_response(verify_prompt, "", system_prompt="You are a QA Engineer. Return ONLY code.")
             verify_match = re.search(r"```python(.*?)```", verify_code_resp, re.DOTALL)

             if verify_match:
                 v_code = verify_match.group(1).strip()
                 v_safe, _ = self.veto_circuit.audit_code(v_code)

                 if v_safe:
                     result = self.sandbox.execute(v_code)
                     if "CORRECTION:" in result or "False" in result or "Error" in result:
                         print(f"🛡️ T-CELL: Correction found -> {result.strip()}")
                         return f"🛡️ [T-CELL AUDIT]: {result.strip()}"
                     else:
                         print(f"🛡️ T-CELL: Claim Verified.")
                         return None
         except Exception as e:
             print(f"T-CELL Error: {e}")
             return None
         return None

    def _detect_intents(self, text: str) -> List[str]:
        found = set()
        for match in self.combined_pattern.finditer(text):
            found.add(match.lastgroup)
        return list(found)

    def _halt_response(self, signal, ois, reason, veto=False) -> Dict[str, Any]:
        return {
            "response": f"SYSTEM HALT: {reason}",
            "tool_outputs": [],
            "artifacts": [],
            "telemetry": {
                "signal": signal,
                "veto": veto,
                "audit": {},
                "ois_budget": ois.budget,
                "s_lang_trace": "$Input >> HALT !! STOP"
            }
        }
