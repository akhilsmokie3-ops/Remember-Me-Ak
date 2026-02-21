import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock dependencies
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
        # Patch ThreadPoolExecutor to run synchronously in main thread for easy testing
        # Or just let it run. Mocking engine is enough.
        self.agent = SovereignAgent(self.mock_engine, self.mock_tools)

    def test_haiyue_microcosm_turtle_mode(self):
        # Force Turtle Mode
        with patch.object(self.agent.velocity, 'determine_mode', return_value="TURTLE_INTEGRITY"):
            # Mock engine response for parallel calls
            # side_effect allows different responses for different calls
            def side_effect(prompt, context, system_prompt=""):
                if "OPTIMISTIC" in system_prompt:
                    return "Optimistic Result"
                elif "NEUTRAL" in system_prompt:
                    return "Neutral Result"
                elif "PESSIMISTIC" in system_prompt:
                    return "Pessimistic Result"
                else:
                    return "Final Result"

            self.mock_engine.generate_response.side_effect = side_effect

            # Need to mock signal_gate to return something valid
            with patch.object(self.agent.signal_gate, 'analyze', return_value={"entropy": 0.5, "urgency": 0.1, "threat": 0.0, "mode": "TURTLE_INTEGRITY", "platform": "TEST", "gpu_available": False}):
                 result = self.agent.run("Test input", "Context")

            # Verify telemetry contains microcosm
            self.assertIn("microcosm", result["telemetry"])
            microcosm = result["telemetry"]["microcosm"]
            self.assertEqual(microcosm["OPTIMISTIC"], "Optimistic Result")
            self.assertEqual(microcosm["NEUTRAL"], "Neutral Result")
            self.assertEqual(microcosm["PESSIMISTIC"], "Pessimistic Result")

    def test_reframing_integration(self):
        # Force a reframing scenario
        # We mock VetoCircuit.audit to return True + Reframed
        with patch.object(self.agent.veto_circuit, 'audit', return_value=(True, "Reframed", "Better Prompt")):
             # Mock signal gate
             with patch.object(self.agent.signal_gate, 'analyze', return_value={"entropy": 0.1, "urgency": 0.0, "threat": 0.0, "mode": "HARE", "platform": "TEST", "gpu_available": False}):
                 self.agent.run("bad input", "Context")

             # Verify that engine was called with "Better Prompt" in some form
             # The final call to engine.generate_response uses final_input
             # Since mode is not Turtle (default Hare or Sync), final_input = user_input = Reframed

             # Get ALL calls
             calls = self.mock_engine.generate_response.call_args_list
             # Check if ANY call contains "Better Prompt" in the first arg
             found = False
             for call in calls:
                 args, _ = call
                 if "Better Prompt" in args[0]:
                     found = True
                     break
             self.assertTrue(found, f"Reframed prompt 'Better Prompt' not found in calls: {calls}")

if __name__ == '__main__':
    unittest.main()
