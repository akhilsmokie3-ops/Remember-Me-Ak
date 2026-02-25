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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

class TestFullSystem(unittest.TestCase):
    @patch('remember_me.kernel.SovereignAgent')
    @patch('remember_me.kernel.ToolArsenal')
    @patch('remember_me.kernel.CSNPManager')
    @patch('remember_me.kernel.ModelRegistry')
    def test_run_cycle(self, MockRegistry, MockCSNP, MockTools, MockAgent):
        from remember_me.kernel import Kernel

        MockRegistry.return_value.load_model.return_value = True

        kernel = Kernel(model_key="test")

        # Verify Kernel components initialized
        self.assertIsNotNone(kernel.agent)
        self.assertIsNotNone(kernel.shield)

        # Mock agent.run to return a proper response
        kernel.agent.run.return_value = {
            "response": "The answer is 42.",
            "tool_outputs": [],
            "artifacts": [],
            "telemetry": {
                "signal": {}, "audit": {}, "ois_budget": 100,
                "veto": False, "microcosm": {}
            }
        }

        # Mock shield.retrieve_context
        kernel.shield.retrieve_context.return_value = "Context"

        # Run Cycle
        response = kernel.run_cycle("What is the answer?")

        # Verify
        self.assertEqual(response, "The answer is 42.")

        # Verify shield interactions
        kernel.shield.retrieve_context.assert_called()
        kernel.shield.update_state.assert_called_with("What is the answer?", "The answer is 42.")

if __name__ == "__main__":
    unittest.main()
