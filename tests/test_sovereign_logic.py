import unittest
import sys
import os
import re
from unittest.mock import MagicMock, patch

# Mock heavy dependencies BEFORE import
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["psutil"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["pandas"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Now import the modules under test
from remember_me.core.nervous_system import SignalGate, VetoCircuit, Proprioception

# Mock imports inside agent
with patch.dict(sys.modules, {
    "remember_me.core.sandbox": MagicMock(),
    "remember_me.core.frameworks": MagicMock(),
    "remember_me.integrations.tools": MagicMock(),
    "remember_me.integrations.engine": MagicMock()
}):
    from remember_me.integrations.agent import SovereignAgent

class TestSovereignLogic(unittest.TestCase):

    def setUp(self):
        self.signal_gate = SignalGate()
        self.veto = VetoCircuit()
        self.proprioception = Proprioception()

        # Mock engine and tools
        self.mock_engine = MagicMock()
        self.mock_engine.generate_response.return_value = "Test Response"
        self.mock_tools = MagicMock()

        # Instantiate Agent
        with patch("remember_me.integrations.agent.SignalGate", return_value=self.signal_gate), \
             patch("remember_me.integrations.agent.VetoCircuit", return_value=self.veto), \
             patch("remember_me.integrations.agent.Proprioception", return_value=self.proprioception), \
             patch("remember_me.integrations.agent.SecurePythonSandbox"), \
             patch("remember_me.integrations.agent.HaiyueMicrocosm"), \
             patch("remember_me.integrations.agent.VelocityPhysics"):
            # We allow ThreadPoolExecutor to run (it's standard lib)
            self.agent = SovereignAgent(self.mock_engine, self.mock_tools)

    def test_signal_gate_entropy(self):
        high = "alskdjfalsdkfjasldkfjasldkfjasldkfjasldkfj"
        low = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        self.assertGreater(self.signal_gate._calculate_entropy(high), self.signal_gate._calculate_entropy(low))

    def test_signal_gate_urgency(self):
        urgent = "QUICK ASAP"
        self.assertGreater(self.signal_gate._calculate_urgency(urgent), 0.5)

    def test_signal_gate_battery_conservation(self):
        # Mock battery low and unplugged
        mock_battery = MagicMock()
        mock_battery.percent = 10
        mock_battery.power_plugged = False

        with patch("psutil.sensors_battery", return_value=mock_battery):
            # We need to re-init SignalGate or patch the method because it might be called in analyze
            # But SignalGate._check_battery calls psutil.sensors_battery directly

            # Re-instantiate SignalGate to clear any cached state if necessary,
            # though it calls _check_battery on analyze
            gate = SignalGate()
            signal = gate.analyze("some input")
            self.assertEqual(signal["mode"], "CONSERVATION")

    def test_veto_lazy_input(self):
        signal = {"entropy": 0.1, "urgency": 0.0, "threat": 0.0}
        accepted, _, reframed = self.veto.audit(signal, "hi")
        self.assertTrue(reframed or not accepted)

    def test_veto_dangerous_code(self):
        code = "import os; os.system('rm -rf /')"
        signal = {"entropy": 0.5, "urgency": 0.0, "threat": 0.0}
        accepted, reason, _ = self.veto.audit(signal, code)
        self.assertFalse(accepted)
        self.assertIn("Dangerous keyword", reason)

    def test_proprioception_confidence(self):
        weak = "maybe"
        strong = "Here is the answer [1] ```code```"
        weak_res = self.proprioception.audit_output(weak, "")
        strong_res = self.proprioception.audit_output(strong, "")

        self.assertLess(weak_res["confidence"], 0.9)
        self.assertTrue(weak_res["regenerate"])

        self.assertGreater(strong_res["confidence"], 0.8) # Might still be < 0.9 depending on exact heuristic
        # If strong confidence is > 0.9, then regenerate should be False

    def test_agent_run(self):
        res = self.agent.run("test", "ctx")
        self.assertIn("response", res)
        self.assertFalse(res["telemetry"]["veto"])

    def test_agent_microcosm_trigger(self):
        # Force Turtle Mode
        with patch.object(self.agent.velocity, "determine_mode", return_value="TURTLE_INTEGRITY"):
            res = self.agent.run("complex question", "ctx")
            self.assertIn("microcosm", res["telemetry"])

    def test_engine_optimization(self):
        from remember_me.integrations.engine import LlamaCppClient
        client = LlamaCppClient()

        # Test ping caching
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200

            # First call
            self.assertTrue(client.ping())
            self.assertEqual(mock_get.call_count, 1)

            # Second call (cached)
            self.assertTrue(client.ping())
            self.assertEqual(mock_get.call_count, 1)

            # Force check
            client.check_connection()
            self.assertEqual(mock_get.call_count, 2)

if __name__ == "__main__":
    unittest.main()
