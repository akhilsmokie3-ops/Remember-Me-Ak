import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies before import
sys.modules["requests"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["psutil"] = MagicMock()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.integrations.agent import SovereignAgent

class TestAgentTCell(unittest.TestCase):
    @patch('remember_me.integrations.agent.VetoCircuit')
    @patch('remember_me.integrations.agent.ModelRegistry')
    @patch('remember_me.integrations.agent.SecurePythonSandbox')
    @patch('remember_me.integrations.agent.SignalGate')
    @patch('remember_me.integrations.agent.Proprioception')
    def test_tcell_trigger(self, MockProprio, MockSignal, MockSandbox, MockEngine, MockVeto):
        # Setup Mocks
        engine = MockEngine()
        # Ensure engine is mockable
        engine.generate_response = MagicMock()

        sandbox = MockSandbox()
        # Mock execute method on the instance
        sandbox_instance = MagicMock()
        MockSandbox.return_value = sandbox_instance

        agent = SovereignAgent(engine, MagicMock())
        agent.sandbox = sandbox_instance # Explicitly replace

        # Mock Signal
        agent.signal_gate.analyze.return_value = {
            "entropy": 0.5, "urgency": 0.0, "threat": 0.0, "mode": "TEST", "platform": "TEST"
        }

        # Mock Veto
        agent.veto_circuit.audit.return_value = (True, "OK")

        # Mock Intent Detection (Force NO CODE intent so T-Cell triggers)
        agent._detect_intents = MagicMock(return_value=[])

        # Mock Initial Response (Hallucination) then Verification Script
        engine.generate_response.side_effect = [
            "The magic number is 42.", # Initial Response
            "```python\nprint('Actual Magic: 99')\n```" # Verification Script Generation
        ]

        # Mock Proprioception (Low Confidence)
        agent.proprioception.audit_output.return_value = {
            "confidence": 0.5, # < 0.8 triggers T-Cell
            "hallucination_risk": 0.5,
            "executable": False,
            "cited": False,
            "fatigue": 0.0
        }

        # Mock Sandbox Execution
        sandbox_instance.execute.return_value = "Actual Magic: 99\n"
        agent.veto_circuit.audit_code.return_value = (True, "Safe")

        # Run
        print("Running Agent T-Cell Test...")
        result = agent.run("Tell me magic", "")

        # Verify T-Cell Triggered
        print("Final Response:", result["response"])
        self.assertIn("[T-CELL CORRECTION]", result["response"])
        self.assertIn("Actual Magic: 99", result["response"])

if __name__ == "__main__":
    unittest.main()
