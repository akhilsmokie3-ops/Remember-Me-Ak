import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Mock torch before import
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False
sys.modules["torch"] = mock_torch

# Ensure src is in path
sys.path.append(os.path.abspath("src"))

from remember_me.core.nervous_system import SignalGate, VetoCircuit, Proprioception
from remember_me.core.frameworks import OISTruthBudget, HaiyueMicrocosm

class TestMohamadPrime(unittest.TestCase):

    def setUp(self):
        self.signal_gate = SignalGate()
        self.veto_circuit = VetoCircuit()
        self.proprioception = Proprioception()
        self.ois = OISTruthBudget(initial_budget=100)
        self.haiyue = HaiyueMicrocosm()

    def test_signal_gate_battery_mock(self):
        # Create mock battery file
        with open(".battery_status", "w") as f:
            f.write("50,False")

        try:
            # Force PSUTIL_AVAILABLE to False for this test if it was True
            with patch("remember_me.core.nervous_system.PSUTIL_AVAILABLE", False):
                batt = self.signal_gate._check_battery()
                self.assertEqual(batt["percent"], 50)
                self.assertFalse(batt["plugged"])
        finally:
            if os.path.exists(".battery_status"):
                os.remove(".battery_status")

    def test_veto_circuit_quality_veto(self):
        # Test lazy input rejection
        signal = {"entropy": 0.1, "mode": "DEEP_RESEARCH", "threat": 0.0}

        # "hi" should be reframed
        accepted, reason, reframed = self.veto_circuit.audit(signal, "hi")
        self.assertTrue(accepted)
        self.assertIn("REFRAMED", reason)

        # "do stuff" should be rejected by quality audit
        # Wait, audit_quality is called inside audit.
        # "do stuff" is 2 words. < 3 words and low entropy.
        accepted, reason, _ = self.veto_circuit.audit(signal, "do stuff")
        self.assertFalse(accepted)
        self.assertIn("VETO [QUALITY]", reason)

    def test_veto_circuit_framework_100(self):
        constraints = self.veto_circuit.get_negative_constraints()
        self.assertIn("FRAMEWORK 100", constraints)
        self.assertIn("NEVER SUMMARIZE", constraints)

    def test_ois_semantic_ledger(self):
        initial_budget = self.ois.budget
        # Check ledger for a claim
        allowed = self.ois.check_ledger(claim_cost=10)
        self.assertTrue(allowed)
        self.assertEqual(self.ois.budget, initial_budget - 10)

        # Deplete budget
        self.ois.deduct(100, "Depletion")
        allowed = self.ois.check_ledger(claim_cost=10)
        self.assertFalse(allowed)

    def test_proprioception_telemetry(self):
        audit_result = {
            "confidence": 0.95,
            "hallucination_risk": 0.05,
            "battery_level": 80,
            "regenerate": False
        }
        signature = self.proprioception.get_telemetry_signature(audit_result)
        self.assertIn("[DIGITAL PROPRIOCEPTION]", signature)
        self.assertIn("CONFIDENCE: 95.0%", signature)
        self.assertIn("BATTERY: 80%", signature)

    def test_haiyue_synthesis_prompt(self):
        user_input = "What is the future of AI?"
        simulations = {
            "OPTIMISTIC": "Utopia",
            "NEUTRAL": "Tool",
            "PESSIMISTIC": "Doom"
        }
        prompt = self.haiyue.synthesize(user_input, simulations)
        self.assertIn("Haiyue Fusion", prompt)
        self.assertIn("MITIGATE", prompt)
        self.assertIn("ACCELERATE", prompt)
        self.assertIn("The Fastest Coherent Result", prompt)

if __name__ == '__main__':
    unittest.main()
