from typing import Dict, Any, List, Optional
import time
import concurrent.futures

class OISTruthBudget:
    """
    FRAMEWORK 4.A: THE OIS TRUTH BUDGET (Granular Economic Logic)
    Every assumption burns capital. Execution HALTS if budget <= 0.
    """

    # Standardized Cost Table
    COSTS = {
        "ASSUMPTION": 20,
        "CONTEXT": 5,
        "CORRELATION": 15,
        "EMOTIONAL_DRIVER": 25,
        "UNDECIDABLE": 40,
        "HIGH_ENTROPY": 10,
        "VETO_TRIGGER": 100,
        "SEARCH_TIMEOUT": 15,
        "CODE_FAILURE": 10,
        "DANGEROUS_CODE": 20,
        "HALLUCINATION": 40,
        "REGENERATION": 10,
    }

    def __init__(self, initial_budget: int = 100):
        self.budget = initial_budget
        self.history = [] # Audit log of deductions

    def deduct(self, amount: int, reason: str):
        """Deducts points and logs the transaction."""
        self.budget -= amount
        self.history.append({"action": "DEDUCT", "amount": amount, "reason": reason, "remaining": self.budget})

    def deduct_by_type(self, action_type: str, details: str = ""):
        """Deducts points based on standardized action types."""
        amount = self.COSTS.get(action_type, 10) # Default to 10 if unknown
        reason = f"{action_type}: {details}" if details else action_type
        self.deduct(amount, reason)

    def check(self) -> bool:
        """Returns True if budget is positive, False if depleted (HALT)."""
        return self.budget > 0

    def get_status(self) -> Dict[str, Any]:
        return {
            "current": self.budget,
            "status": "SOUND" if self.budget > 0 else "DEPLETED",
            "history": self.history
        }

class HaiyueMicrocosm:
    """
    FRAMEWORK 4.D: THE HAIYUE-FUSION MICROCOSM (Active Simulation)
    Spawns 3 simultaneous Trajectory Timelines (Optimistic, Neutral, Pessimistic).
    Selects the Fastest Coherent Result.
    """
    def __init__(self):
        pass

    def run_simulation(self, executor: concurrent.futures.ThreadPoolExecutor, engine: Any, user_input: str, context: str) -> concurrent.futures.Future:
        """
        Spawns 3 parallel simulation tasks.
        Returns a Future that resolves to a Dict of trajectories.
        """
        print("🔮 Haiyue Microcosm: Spawning 3 Timelines...")
        prompts = {
            "OPTIMISTIC": f"Simulate an OPTIMISTIC (+1) outcome/answer for: {user_input}. Be concise.",
            "NEUTRAL": f"Simulate a NEUTRAL (0) outcome/answer for: {user_input}. Be concise.",
            "PESSIMISTIC": f"Simulate a PESSIMISTIC (-1) outcome/answer for: {user_input}. Focus on risks. Be concise."
        }

        def _execute_microcosm():
             futures = {}
             # Run sequentially inside this thread to avoid deadlock on the main pool if it's small?
             # Or use a private pool.
             with concurrent.futures.ThreadPoolExecutor(max_workers=3) as sim_pool:
                 for p_name, p_text in prompts.items():
                     sys_p = f"You are a Simulation Engine. Mode: {p_name}. Output only the simulation."
                     futures[p_name] = sim_pool.submit(engine.generate_response, p_text, context, system_prompt=sys_p)

                 local_results = {}
                 for p_name, future in futures.items():
                     try:
                         local_results[p_name] = future.result(timeout=20)
                     except Exception as e:
                         local_results[p_name] = f"Simulation Failed: {e}"

             return local_results

        return executor.submit(_execute_microcosm)

    def synthesize(self, user_input: str, simulations: Dict[str, str]) -> str:
        """
        Synthesizes the 3 trajectories into a single coherent prompt input.
        """
        return (
             f"User Input: {user_input}\n"
             f"Simulated Trajectories (Use these to form a robust answer):\n"
             f"[OPTIMISTIC]: {simulations.get('OPTIMISTIC', 'N/A')}\n"
             f"[NEUTRAL]: {simulations.get('NEUTRAL', 'N/A')}\n"
             f"[PESSIMISTIC]: {simulations.get('PESSIMISTIC', 'N/A')}\n"
             "SYNTHESIS INSTRUCTION: You must weigh the Optimistic (Growth), Neutral (Reality), and Pessimistic (Risk) trajectories.\n"
             "The final answer must be 'The Fastest Coherent Result' that mitigates the Pessimistic risks while capturing Optimistic value.\n"
             "Output ONLY the final synthesized answer. Do not output the trajectories."
        )

class VelocityPhysics:
    """
    FRAMEWORK 4.B: VELOCITY PHYSICS (Turtle vs Hare Protocol)
    Determines execution mode based on Signal Vector (Entropy/Urgency).
    """

    MODES = {
        "WAR_SPEED": {
            "timeout": 10,
            "search_depth": 1,
            "max_retries": 1,
            "system_suffix": "MODE: WAR_SPEED. Output < 60s. No filler. Pure kinetic payload."
        },
        "TURTLE_INTEGRITY": {
            "timeout": 30,
            "search_depth": 3,
            "max_retries": 3,
            "system_suffix": "MODE: TURTLE_INTEGRITY. Verify every claim. Build Cathedrals of Logic."
        },
        "DEEP_RESEARCH": {
            "timeout": 60,
            "search_depth": 5,
            "max_retries": 3,
            "system_suffix": "MODE: DEEP_RESEARCH. Exhaustive analysis. Cite all sources."
        },
        "SYNC_POINT": {
            "timeout": 15,
            "search_depth": 2,
            "max_retries": 2,
            "system_suffix": "MODE: STANDARD. Balanced velocity and integrity."
        },
         "ARCHITECT_PRIME": {
            "timeout": 45,
            "search_depth": 4,
            "max_retries": 3,
            "system_suffix": "MODE: ARCHITECT_PRIME. High-Entropy Handling. Structure First."
        }
    }

    def determine_mode(self, signal: Dict[str, Any]) -> str:
        entropy = signal.get("entropy", 0.0)
        urgency = signal.get("urgency", 0.0)

        # Explicit override from signal if present
        if "mode" in signal and signal["mode"] in self.MODES:
            return signal["mode"]

        # Hare Velocity (War Speed)
        if urgency > 0.6:
            return "WAR_SPEED"

        # Turtle Integrity (Deep Research)
        if entropy > 0.6:
            return "TURTLE_INTEGRITY"

        # Default Synchronization Point
        return "SYNC_POINT"

    def get_execution_config(self, mode: str) -> Dict[str, Any]:
        """Returns the execution parameters for the given mode."""
        return self.MODES.get(mode, self.MODES["SYNC_POINT"])
