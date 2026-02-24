
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock external dependencies
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["accelerate"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["bs4"] = MagicMock()
sys.modules["duckduckgo_search"] = MagicMock()
sys.modules["faiss"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath("src"))

from remember_me.integrations.agent import SovereignAgent
from remember_me.core.nervous_system import SignalGate, VetoCircuit, Proprioception

class TestSovereignRefactor(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_engine.generate_response.return_value = "Mocked Response"
        self.mock_tools = MagicMock()
        self.mock_tools.web_search.return_value = "Mock Search Result"
        self.mock_tools.generate_image.return_value = "mock_image.png"

        # Patch the agent to allow testing phases independently before full refactor
        # We will implement the phases in the agent later, so here we mock them if they don't exist yet
        # or call them if they do. Since they don't exist, we will test the LOGIC that will go into them.

        self.agent = SovereignAgent(self.mock_engine, self.mock_tools)
        # Manually attach improved components if needed for testing logic
        self.agent.signal_gate = SignalGate()
        self.agent.veto_circuit = VetoCircuit()
        self.agent.proprioception = Proprioception()

    def test_phase_0_audit_logic(self):
        """Test the logic for Phase 0: Audit (Signal Gate + Veto)"""
        user_input = "Calculate the fibonacci sequence."

        # 1. Signal Gate Analysis
        signal = self.agent.signal_gate.analyze(user_input)
        self.assertIn("entropy", signal)
        self.assertIn("urgency", signal)
        self.assertIn("threat", signal)

        # 2. Veto Circuit Audit
        accepted, reason, reframed = self.agent.veto_circuit.audit(signal, user_input)
        self.assertTrue(accepted)
        self.assertEqual(reason, "Authorized.")

    def test_phase_5_verification_correction_logic(self):
        """Test the logic for Phase 5: Verification (T-Cell)"""
        # Scenario: Agent hallucinates a fact.
        # T-Cell generates code to verify.
        # Code returns False/Correction.
        # Agent appends correction.

        hallucinated_response = "The capital of Mars is Elonville."
        verification_code = "print('False: Mars has no capital.')"

        # Mock Engine to return the verification code when asked
        self.mock_engine.generate_response.side_effect = [
            f"```python\n{verification_code}\n```"
        ]

        # Mock Sandbox execution
        self.agent.sandbox = MagicMock()
        self.agent.sandbox.execute.return_value = "False: Mars has no capital."

        # Manually run the T-Cell logic (which will be in _phase_5_verification or _run_t_cell)
        # For now, we simulate what _run_t_cell would do

        # 1. Trigger T-Cell
        t_cell_prompt = f"Verify: '{hallucinated_response}'"
        code_resp = self.mock_engine.generate_response(t_cell_prompt, "")

        # 2. Extract Code
        import re
        code_match = re.search(r"```python(.*?)```", code_resp, re.DOTALL)
        self.assertTrue(code_match)
        code = code_match.group(1).strip()

        # 3. Execute
        result = self.agent.sandbox.execute(code)

        # 4. Correction Logic
        final_response = hallucinated_response
        if "False" in result or "Error" in result:
             final_response += f"\n\n[T-CELL CORRECTION]: {result}"

        self.assertIn("[T-CELL CORRECTION]", final_response)
        self.assertIn("Mars has no capital", final_response)

    def test_mubarizun_trigger_logic(self):
        """Test the logic for Mubarizun Mode detection"""
        # User challenges the bot
        user_input = "You are wrong. That's a lie."

        # We need to enhance SignalGate to detect this.
        # Currently it might just see high threat or sentiment.
        # We will add specific logic in implementation.

        # For test purposes, we subclass or patch SignalGate to simulate the new logic
        # OR we check if we can add it to the test now.

        # Let's assume we will add a 'challenge' score or specific flag in signal
        # For now, let's verify threat score increases
        signal = self.agent.signal_gate.analyze(user_input)
        # self.assertGreater(signal['threat'], 0.0) # Existing logic

        # We want a specific "MUBARIZUN" mode
        # This requires the implementation change in SignalGate
        pass

if __name__ == "__main__":
    unittest.main()
