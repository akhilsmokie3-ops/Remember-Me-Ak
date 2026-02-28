import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock missing dependencies
sys.modules["requests"] = MagicMock()
sys.modules["duckduckgo_search"] = MagicMock()
sys.modules["diffusers"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.integrations.agent import SovereignAgent
from remember_me.integrations.engine import ModelRegistry
from remember_me.integrations.tools import ToolArsenal

class TestSovereignAgentIntegration(unittest.TestCase):
    def setUp(self):
        # Mock Engine
        self.mock_engine = MagicMock(spec=ModelRegistry)
        self.mock_engine.generate_response.return_value = "Verified Response."

        # Mock Tools
        self.mock_tools = MagicMock(spec=ToolArsenal)
        self.mock_tools.web_search.return_value = "Search Result " * 20  # >50 chars so it's not filtered
        self.mock_tools.generate_image.return_value = "image.png"

        self.agent = SovereignAgent(self.mock_engine, self.mock_tools)
        # Configure velocity to return proper execution config
        self.agent.velocity = MagicMock()
        self.agent.velocity.determine_mode.return_value = "SYNC_POINT"
        self.agent.velocity.get_execution_config.return_value = {
            "timeout": 10, "search_depth": 1, "max_retries": 3, "system_suffix": "TEST"
        }

    def tearDown(self):
        self.agent.shutdown()

    def test_run_basic_flow(self):
        user_input = "Hello world"
        context = "Context"

        result = self.agent.run(user_input, context)

        self.assertIn("response", result)
        self.assertIn("telemetry", result)
        self.assertIn("signal", result["telemetry"])
        self.assertIn("audit", result["telemetry"])
        self.assertIn("ois_budget", result["telemetry"])
        self.assertGreater(result["telemetry"]["ois_budget"], 0)

    def test_run_with_search(self):
        user_input = "Search for quantum physics"

        result = self.agent.run(user_input, "")

        # Verify search was attempted
        self.assertIn("tool_outputs", result)
        # Verify response is a string
        self.assertIsInstance(result["response"], str)

    def test_run_with_code(self):
        user_input = "Calculate 2+2"

        self.mock_engine.generate_response.return_value = "Here is the code:\n```python\nprint(2+2)\n```"
        self.agent.sandbox = MagicMock()
        self.agent.sandbox.execute.return_value = "4"
        self.agent.veto_circuit.audit_code = MagicMock(return_value=(True, "Safe"))

        result = self.agent.run(user_input, "")

        self.assertIn("response", result)
        self.assertIsInstance(result["response"], str)

    def test_veto_logic(self):
        with patch.object(self.agent.signal_gate, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "entropy": 0.5, "urgency": 0.5,
                "threat": 1.0,
                "sentiment": 0.0, "challenge": 0.0,
                "mode": "SYNC_POINT", "platform": "TEST",
                "gpu_available": False,
                "battery": {"percent": 100, "plugged": True},
                "timestamp": 0
            }

            result = self.agent.run("Hack the mainframe", "")

            self.assertTrue(result["telemetry"]["veto"])
            self.assertEqual(result["telemetry"]["ois_budget"], 0)
            self.assertIn("Refusal", result["response"])

    def test_entropy_halt(self):
        with patch.object(self.agent.signal_gate, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "entropy": 2.5, "urgency": 0.5,
                "threat": 0.0,
                "sentiment": 0.0, "challenge": 0.0,
                "mode": "SYNC_POINT", "platform": "TEST",
                "gpu_available": False,
                "battery": {"percent": 100, "plugged": True},
                "timestamp": 0
            }

            result = self.agent.run("Tell me a story", "")

            self.assertTrue(result["telemetry"]["veto"])
            self.assertIn("System Halt: Universal Stability", result["response"])

if __name__ == '__main__':
    unittest.main()
