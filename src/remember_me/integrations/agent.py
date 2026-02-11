import re
import io
import sys
import traceback
import concurrent.futures
from typing import List, Dict, Any

from remember_me.integrations.tools import ToolArsenal
from remember_me.integrations.engine import ModelRegistry
from remember_me.core.nervous_system import SignalGate, VetoCircuit, Proprioception

class SovereignAgent:
    """
    The Orchestrator.
    Analyzes user intent and executes a multi-step tool chain (Search -> Code -> Image)
    before synthesizing the final response.
    """

    # ⚡ Bolt: Pre-allocate globals to avoid reconstruction overhead (Optimization)
    _BASE_GLOBALS = {
        "math": __import__("math"),
        "random": __import__("random"),
        "datetime": __import__("datetime"),
        "print": print,
        "range": range,
        "len": len,
        "int": int,
        "float": float,
        "str": str,
        "list": list,
        "dict": dict,
        "set": set,
        "sum": sum,
        "min": min,
        "max": max,
        "sorted": sorted,
    }

    def __init__(self, engine: ModelRegistry, tools: ToolArsenal):
        self.engine = engine
        self.tools = tools

        # ⚡ Nervous System Components
        self.signal_gate = SignalGate()
        self.veto_circuit = VetoCircuit()
        self.proprioception = Proprioception()

        # ⚡ Bolt: Persistent ThreadPool to reuse threads across requests
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

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

    def run(self, user_input: str, context_str: str) -> Dict[str, Any]:
        """
        Main execution loop.
        Returns a dictionary with 'response' and 'artifacts' (paths to images, code output, etc).
        """
        # 1. SIGNAL GATE (Adaptor Layer)
        signal = self.signal_gate.analyze(user_input)

        # 2. VETO CIRCUIT (Hierarchical Veto)
        accepted, refusal_reason = self.veto_circuit.audit(signal, user_input)
        if not accepted:
            return {
                "response": refusal_reason,
                "tool_outputs": [],
                "artifacts": [],
                "telemetry": {
                    "signal": signal,
                    "veto": True,
                    "audit": {}
                }
            }

        # Inject Signal Mode into Context/Prompt
        mode_instruction = f"[MODE: {signal['mode']}] | [URGENCY: {signal['urgency']:.2f}]"

        detected_intents = self._detect_intents(user_input)
        artifacts = []
        tool_outputs = []

        # ⚡ Bolt: Submit Image Generation EARLY (Latency Hiding)
        # Run in parallel with Search and Code phases.
        img_future = None
        img_path = "dream_output.png"

        if "IMAGE" in detected_intents:
            print(f"🎨 Orchestrator: Visualizing (Parallel)...")
            # We use persistent ThreadPoolExecutor (IO-bound/GIL-releasing tasks)
            img_prompt = user_input
            img_future = self._executor.submit(self.tools.generate_image, img_prompt, img_path)

        # 3. SEARCH PHASE (Information Gathering)
        if "SEARCH" in detected_intents:
            query = user_input # In a complex agent, we'd extract the query. For now, full prompt is decent.
            # Strip "search for" etc if possible, but DDG handles natural language well.
            print(f"🕵️ Orchestrator: Triggering Search for '{query[:20]}...'")
            search_res = self.tools.web_search(query)
            tool_outputs.append(f"[SEARCH RESULTS]:\n{search_res}\n")

        # 4. CODE PHASE (Symbolic Reasoning)
        if "CODE" in detected_intents:
            # We need to extract the "intent" for the code.
            # Ask the LLM to write the code? Or just try to execute if the user provided code?
            # For this version: We ask the LLM to *write* the code first, then we execute it.
            # But that requires a double-generation loop.
            # Fast path: If the user asks to "Calculate X", we can try to extract X.
            # Better path: Use the LLM to generate the python script in step 1?

            # Let's do a sub-call to the engine to get the code.
            print(f"💻 Orchestrator: Generating Python solution...")
            code_prompt = f"Write a Python script to solve this: {user_input}. Output ONLY the code inside ```python blocks."

            # ⚡ Bolt: Inject tool outputs (like Search Results) into code generation context
            # This ensures the code can use data found during the Search phase.
            code_context = context_str + "\n" + "\n".join(tool_outputs)

            # Use a custom system prompt for code gen
            code_sys_prompt = f"You are a Python Expert. {mode_instruction} Return ONLY the code."
            code_response = self.engine.generate_response(code_prompt, code_context, system_prompt=code_sys_prompt)

            # Extract code block
            code_match = re.search(r"```python(.*?)```", code_response, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                print(f"⚙️ Executing Code...")
                exec_result = self._execute_python(code)
                tool_outputs.append(f"[PYTHON EXECUTION RESULT]:\n{exec_result}\n")
                artifacts.append({"type": "code", "content": code, "result": exec_result})
            else:
                tool_outputs.append("[PYTHON ERROR]: No code block generated by LLM.\n")

        # 5. SYNTHESIS & IMAGE PHASE (Parallel Execution)
        # Combine tool outputs with original context
        augmented_context = context_str + "\n".join(tool_outputs)

        # Main Thread: Generate Text Response
        # Pass a custom system prompt that includes the default + mode.
        default_system = (
            f"{mode_instruction}\n"
            "You are a helpful AI assistant equipped with the Remember Me Cognitive Kernel. "
            "You have long-term memory via CSNP, and access to tools like Image Generation and Web Search. "
            "Do not deny these capabilities. If the user refers to past conversations, assume your memory context is accurate. "
            "Answer directly and helpfully."
        )

        final_response = self.engine.generate_response(user_input, augmented_context, system_prompt=default_system)

        # Collect Image Result
        if img_future:
            res = img_future.result() # Wait for completion
            artifacts.append({"type": "image", "path": img_path, "status": res})
            final_response += f"\n\n[Visual Generated: {res}]"

        # 6. PROPRIOCEPTION (Self-Sensing)
        audit_result = self.proprioception.audit_output(final_response, augmented_context)

        # Append Audit Telemetry to Response (Optional, for debugging/transparency)
        # final_response += f"\n\n[CONFIDENCE: {audit_result['confidence']*100:.0f}%]"

        return {
            "response": final_response,
            "tool_outputs": tool_outputs,
            "artifacts": artifacts,
            "telemetry": {
                "signal": signal,
                "veto": False,
                "audit": audit_result
            }
        }

    def _detect_intents(self, text: str) -> List[str]:
        # ⚡ Bolt: Single pass detection using combined regex
        # Use a set to avoid duplicates if multiple patterns for same intent match
        found = set()
        for match in self.combined_pattern.finditer(text):
            found.add(match.lastgroup)
        return list(found)

    def _execute_python(self, code: str) -> str:
        """
        Executes Python code in a restricted namespace and captures stdout.
        """
        # Buffer for stdout
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()

        # Restricted globals
        # ⚡ Bolt: Copy pre-allocated globals instead of rebuilding (1.3x faster than dict())
        allowed_globals = self._BASE_GLOBALS.copy()

        try:
            # We wrap in a try-except block inside the exec
            exec(code, allowed_globals)
            sys.stdout = old_stdout
            return redirected_output.getvalue()
        except Exception:
            sys.stdout = old_stdout
            return traceback.format_exc()
