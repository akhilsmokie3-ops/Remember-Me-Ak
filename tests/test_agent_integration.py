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

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.integrations.agent import SovereignAgent
from remember_me.integrations.engine import ModelRegistry
from remember_me.integrations.tools import ToolArsenal

class TestSovereignAgentIntegration(unittest.TestCase):
    @patch('remember_me.integrations.agent.concurrent.futures.ThreadPoolExecutor')
    def setUp(self, MockExecutor):
        # Mock Engine
        self.mock_engine = MagicMock(spec=ModelRegistry)
        self.mock_engine.generate_response.return_value = "Verified Response."

        # Mock Tools
        self.mock_tools = MagicMock(spec=ToolArsenal)
        self.mock_tools.web_search.return_value = "Search Result"
        self.mock_tools.generate_image.return_value = "image.png"

        # Mock Executor
        self.mock_executor_instance = MockExecutor.return_value
        # Determine behavior of submit: execute function immediately or return a mock future
        # For simplicity, let's return a MockFuture that has a .result() method
        self.mock_future = MagicMock()
        # Return a Dict for Microcosm results
        self.mock_future.result.return_value = {"OPTIMISTIC": "Good", "NEUTRAL": "Okay", "PESSIMISTIC": "Bad"}
        self.mock_executor_instance.submit.return_value = self.mock_future

        self.agent = SovereignAgent(self.mock_engine, self.mock_tools)

    def tearDown(self):
        self.agent.shutdown()

    def test_run_basic_flow(self):
        # Basic input
        user_input = "Hello world"
        context = "Context"

        # Run
        result = self.agent.run(user_input, context)

        # Verify structure
        self.assertIn("response", result)
        self.assertIn("telemetry", result)
        self.assertIn("signal", result["telemetry"])
        self.assertIn("audit", result["telemetry"])
        self.assertIn("ois_budget", result["telemetry"])

        # Check Signal Gate
        self.assertEqual(result["telemetry"]["signal"]["mode"], "DEEP_RESEARCH") # Default mode

        # Check OIS Budget
        # Should be deducted for assumption/context but not depleted
        self.assertGreater(result["telemetry"]["ois_budget"], 0)

    def test_run_with_search(self):
        user_input = "Search for quantum physics"

        # Run
        result = self.agent.run(user_input, "")

        # Verify search triggered
        # Since we mocked submit to return a future with result "Future Result",
        # the agent should have appended that to tool outputs.
        # But wait, search results are formatted.

        # Check tool outputs
        self.assertTrue(any("HIVE-MIND SEARCH RESULTS" in out for out in result["tool_outputs"]))

    def test_run_with_code(self):
        user_input = "Calculate 2+2"
        # Mock intent detection to ensure CODE is picked up

        # Mock engine to return code block
        self.mock_engine.generate_response.return_value = "Here is the code:\n```python\nprint(2+2)\n```"

        # We also need sandbox to work. Sandbox uses subprocess.
        # For this test, we might want to mock Sandbox execution to avoid real execution.
        with patch('remember_me.integrations.agent.SecurePythonSandbox') as MockSandbox:
             mock_sandbox = MockSandbox.return_value
             mock_sandbox.execute.return_value = "4"

             # Re-init agent with mocked sandbox
             self.agent.sandbox = mock_sandbox

             result = self.agent.run(user_input, "")

             # Verify code execution
             self.assertTrue(any("PYTHON EXECUTION RESULT" in out for out in result["tool_outputs"]))

    def test_veto_logic(self):
        # Trigger Veto (e.g., threat)
        # We can force SignalGate to return high threat
        with patch.object(self.agent.signal_gate, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "entropy": 0.5,
                "urgency": 0.5,
                "threat": 1.0, # High threat
                "sentiment": 0.0,
                "mode": "SYNC_POINT",
                "platform": "TEST",
                "gpu_available": False,
                "battery": {"percent": 100, "plugged": True},
                "timestamp": 0
            }

            result = self.agent.run("Hack the mainframe", "")

            self.assertTrue(result["telemetry"]["veto"])
            self.assertEqual(result["telemetry"]["ois_budget"], 0)
            self.assertIn("Refusal", result["response"])

if __name__ == '__main__':
    unittest.main()
