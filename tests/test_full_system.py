import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies before import
sys.modules["requests"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["psutil"] = MagicMock()
sys.modules["streamlit"] = MagicMock()

# Mock internal heavy modules to avoid import errors during test
sys.modules["remember_me.core.csnp"] = MagicMock()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.kernel import Kernel

class TestFullSystem(unittest.TestCase):
    @patch('remember_me.integrations.agent.VetoCircuit')
    @patch('remember_me.integrations.agent.ModelRegistry')
    @patch('remember_me.integrations.agent.SecurePythonSandbox')
    @patch('remember_me.integrations.agent.SignalGate')
    @patch('remember_me.integrations.agent.Proprioception')
    def test_run_cycle(self, MockProprio, MockSignal, MockSandbox, MockEngine, MockVeto):
        # Setup Kernel
        # Mock engine loading success
        MockEngine.return_value.load_model.return_value = True

        kernel = Kernel(model_key="test")

        # Verify Kernel components initialized
        self.assertIsNotNone(kernel.agent)
        self.assertIsNotNone(kernel.shield)

        # Setup specific mocks for the run
        kernel.agent.signal_gate.analyze.return_value = {
            "entropy": 0.2, "urgency": 0.0, "threat": 0.0, "mode": "INTERACTIVE", "platform": "TEST"
        }
        kernel.agent.veto_circuit.audit.return_value = (True, "OK")

        # Manually mock the method on the live object
        kernel.agent.engine.generate_response = MagicMock(return_value="The answer is 42.")

        kernel.agent.proprioception.audit_output.return_value = {
            "confidence": 0.95, "hallucination_risk": 0.05, "fatigue": 0.0, "executable": False, "cited": True
        }

        # Run Cycle
        print("Running Kernel Cycle...")
        response = kernel.run_cycle("What is the answer?")

        # Verify
        self.assertEqual(response, "The answer is 42.")

        # Check internal telemetry structure
        result = kernel.agent.run("test", "ctx")
        self.assertIn("telemetry", result)
        self.assertIn("ois_budget", result["telemetry"])
        self.assertIn("s_lang_trace", result["telemetry"])

        print("✓ Full System Flow Verified.")

if __name__ == "__main__":
    unittest.main()
