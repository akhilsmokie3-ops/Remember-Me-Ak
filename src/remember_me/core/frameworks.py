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
        "PARADOX": 50, # Added for Paradox Engine
        "DEPENDENCY_AUDIT": 10,
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

    def check_ledger(self, claim_cost: int = 5) -> bool:
        """
        FRAMEWORK 10: THE SEMANTIC LEDGER.
        Every claim must PURCHASE the next claim.
        Returns True if budget allows the transaction.
        """
        if self.budget >= claim_cost:
            self.deduct(claim_cost, "SEMANTIC_LEDGER: Claim Verification")
            return True
        return False

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
             # Use a dedicated private pool for isolation
             results = {}
             with concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="Haiyue") as sim_pool:
                 future_map = {}
                 for p_name, p_text in prompts.items():
                     sys_p = f"You are a Simulation Engine. Mode: {p_name}. Output only the simulation. Be concise."
                     # Submit task
                     future_map[sim_pool.submit(engine.generate_response, p_text, context, system_prompt=sys_p)] = p_name

                 # Wait for all with a hard timeout
                 done, not_done = concurrent.futures.wait(future_map.keys(), timeout=30)

                 for future in done:
                     p_name = future_map[future]
                     try:
                         results[p_name] = future.result()
                     except Exception as e:
                         results[p_name] = f"Simulation Failed: {e}"

                 for future in not_done:
                     p_name = future_map[future]
                     results[p_name] = "Simulation Timeout"
                     # We can't cancel running threads easily in Python, but we ignore the result.

             return results

        return executor.submit(_execute_microcosm)

    def synthesize(self, user_input: str, simulations: Dict[str, str]) -> str:
        """
        Synthesizes the 3 trajectories into a single coherent prompt input.
        FRAMEWORK 4.D: Select the Fastest Coherent Result.
        """
        return (
             f"User Input: {user_input}\n"
             f"--- HAIYUE SIMULATION DATA ---\n"
             f"[OPTIMISTIC (+1)]: {simulations.get('OPTIMISTIC', 'N/A')}\n"
             f"[NEUTRAL (0)]: {simulations.get('NEUTRAL', 'N/A')}\n"
             f"[PESSIMISTIC (-1)]: {simulations.get('PESSIMISTIC', 'N/A')}\n"
             "------------------------------\n"
             "SYNTHESIS INSTRUCTION: Apply 'Haiyue Fusion'.\n"
             "1. MITIGATE: Address the risks identified in the Pessimistic trajectory.\n"
             "2. ACCELERATE: Capture the value from the Optimistic trajectory.\n"
             "3. GROUND: Use the Neutral trajectory for reality checking.\n"
             "RESULT: Generate 'The Fastest Coherent Result'. Do not list the trajectories. Output the final consolidated answer directly."
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
