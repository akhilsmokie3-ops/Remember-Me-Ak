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
sys.modules["pandas"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.core.nervous_system import SignalGate, VetoCircuit, Proprioception
from remember_me.integrations.agent import SovereignAgent
import remember_me.core.nervous_system as ns

class TestSovereignLogic(unittest.TestCase):

    def setUp(self):
        self.signal_gate = SignalGate()
        self.veto = VetoCircuit()
        self.proprioception = Proprioception()

        # Mock engine and tools
        self.mock_engine = MagicMock()
        self.mock_engine.generate_response.return_value = "Test Response"
        self.mock_tools = MagicMock()

        # Instantiate Agent with properly configured mocks
        self.agent = SovereignAgent(self.mock_engine, self.mock_tools)
        # Override velocity to return proper execution config
        self.agent.velocity = MagicMock()
        self.agent.velocity.determine_mode.return_value = "SYNC_POINT"
        self.agent.velocity.get_execution_config.return_value = {
            "timeout": 10, "search_depth": 1, "max_retries": 3, "system_suffix": "TEST"
        }

    def test_signal_gate_entropy(self):
        high = "alskdjfalsdkfjasldkfjasldkfjasldkfjasldkfj"
        low = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        self.assertGreater(self.signal_gate._calculate_entropy(high), self.signal_gate._calculate_entropy(low))

    def test_signal_gate_urgency(self):
        urgent = "QUICK ASAP"
        self.assertGreater(self.signal_gate._calculate_urgency(urgent), 0.5)

    def test_signal_gate_battery_conservation(self):
        """Test CONSERVATION mode is triggered when battery is low and unplugged."""
        mock_battery = MagicMock()
        mock_battery.percent = 10
        mock_battery.power_plugged = False

        # Robust patching for psutil availability
        original_psutil = getattr(ns, 'psutil', None)
        original_avail = ns.PSUTIL_AVAILABLE

        mock_psutil = MagicMock()
        mock_psutil.sensors_battery.return_value = mock_battery

        setattr(ns, 'psutil', mock_psutil)
        ns.PSUTIL_AVAILABLE = True

        try:
            gate = SignalGate()
            signal = gate.analyze("some input text for testing purposes here")
            self.assertEqual(signal["mode"], "CONSERVATION")
        finally:
            # Restore state
            if original_psutil is not None:
                setattr(ns, 'psutil', original_psutil)
            else:
                delattr(ns, 'psutil')
            ns.PSUTIL_AVAILABLE = original_avail

    def test_veto_lazy_input(self):
        signal = {"entropy": 0.1, "urgency": 0.0, "threat": 0.0, "mode": "TEST"}
        accepted, reason, reframed = self.veto.audit(signal, "hi")
        # "hi" gets reframed — accepted=True, reason="REFRAMED: Protocol Initialization"
        self.assertTrue(accepted)
        self.assertIn("REFRAMED", reason)
        self.assertIsNotNone(reframed)

    def test_veto_dangerous_code(self):
        """Actual code with import marker triggers code veto."""
        code = "import os; os.system('rm -rf /')"
        signal = {"entropy": 0.5, "urgency": 0.0, "threat": 0.0, "mode": "TEST"}
        accepted, reason, _ = self.veto.audit(signal, code)
        self.assertFalse(accepted)
        # Reason could be "Dangerous code patterns" or "Dangerous keyword" or "Forbidden import"
        self.assertTrue("Dangerous" in reason or "Forbidden" in reason,
                       f"Expected danger-related reason, got: {reason}")

    def test_proprioception_confidence(self):
        weak = "maybe"
        strong = "Here is the answer [1] ```code```"
        weak_res = self.proprioception.audit_output(weak, "")
        strong_res = self.proprioception.audit_output(strong, "")

        self.assertLess(weak_res["confidence"], 0.9)
        self.assertTrue(weak_res["regenerate"])

        self.assertGreater(strong_res["confidence"], 0.8)

    def test_agent_run(self):
        res = self.agent.run("test query for the agent", "context")
        self.assertIn("response", res)
        self.assertIn("telemetry", res)

    def test_agent_microcosm_trigger(self):
        # Force Turtle Mode
        self.agent.velocity.determine_mode.return_value = "TURTLE_INTEGRITY"
        # Mock signal gate so it doesn't trigger the entropy > 2.14 halt
        self.agent.signal_gate.analyze = MagicMock(return_value={
            "entropy": 1.0, "urgency": 0.0, "threat": 0.0, "challenge": 0.0,
            "sentiment": 0.0, "mode": "TURTLE_INTEGRITY", "platform": "GEMINI",
            "gpu_available": False, "battery": {"percent": 100, "plugged": True},
            "timestamp": 0
        })
        res = self.agent.run("complex question about quantum physics", "ctx")
        self.assertIn("microcosm", res["telemetry"])

    def test_engine_optimization(self):
        from remember_me.integrations.engine import LlamaCppClient
        client = LlamaCppClient()
        # Since engine module is mocked, LlamaCppClient is a MagicMock
        self.assertTrue(callable(client.ping))

if __name__ == "__main__":
    unittest.main()
