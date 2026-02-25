import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["faiss"] = MagicMock()
sys.modules["pyttsx3"] = MagicMock()
sys.modules["diffusers"] = MagicMock()
sys.modules["duckduckgo_search"] = MagicMock()

from remember_me.integrations.agent import SovereignAgent
from remember_me.integrations.engine import ModelRegistry
from remember_me.integrations.tools import ToolArsenal

class TestSovereignAgentParallel(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock(spec=ModelRegistry)
        self.mock_engine.generate_response.return_value = "Mocked Response"
        self.mock_tools = MagicMock(spec=ToolArsenal)
        self.agent = SovereignAgent(self.mock_engine, self.mock_tools)
        # Configure velocity
        self.agent.velocity = MagicMock()
        self.agent.velocity.determine_mode.return_value = "SYNC_POINT"
        self.agent.velocity.get_execution_config.return_value = {
            "timeout": 10, "search_depth": 1, "max_retries": 3, "system_suffix": "TEST"
        }

    def test_haiyue_microcosm_turtle_mode(self):
        # Force Turtle Mode
        self.agent.velocity.determine_mode.return_value = "TURTLE_INTEGRITY"

        with patch.object(self.agent.signal_gate, 'analyze', return_value={
            "entropy": 0.5, "urgency": 0.1, "threat": 0.0,
            "challenge": 0.0, "sentiment": 0.0,
            "mode": "TURTLE_INTEGRITY", "platform": "TEST",
            "gpu_available": False,
            "battery": {"percent": 100, "plugged": True},
            "timestamp": 0
        }):
             result = self.agent.run("Test input", "Context")

        # Verify telemetry contains microcosm
        self.assertIn("microcosm", result["telemetry"])

    def test_reframing_integration(self):
        """Test that the VetoCircuit correctly reframes lazy inputs.
        Note: The current agent implementation's telemetry stores only the
        proprioception audit, not the veto audit. We test the reframing
        mechanism directly via VetoCircuit."""
        from remember_me.core.nervous_system import VetoCircuit
        veto = VetoCircuit()
        signal = {"entropy": 0.1, "urgency": 0.0, "threat": 0.0, "mode": "TEST"}

        # 'hi' should be reframed
        accepted, reason, reframed = veto.audit(signal, "hi")
        self.assertTrue(accepted)
        self.assertIn("REFRAMED", reason)
        self.assertIsNotNone(reframed)
        self.assertIn("Initialize", reframed)

        # Also verify the agent still works with reframed input
        result = self.agent.run("hi", "Context")
        self.assertIn("response", result)
        self.assertIsInstance(result["response"], str)

if __name__ == '__main__':
    unittest.main()
