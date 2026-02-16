import unittest
import sys
import os
import gzip

# Add src to path
sys.path.append(os.path.abspath("src"))

from remember_me.core.nervous_system import SignalGate, VetoCircuit, SoundHeart

class TestARKLogic(unittest.TestCase):
    def setUp(self):
        self.gate = SignalGate()
        self.veto = VetoCircuit()

    def test_entropy_compression(self):
        """Verify that gzip compression ratio is used for entropy."""
        # Low entropy: Repetitive text
        low_ent_text = "A" * 1000
        signal_low = self.gate.analyze(low_ent_text)
        # Should be very low
        self.assertLess(signal_low["entropy"], 0.1)

        # High entropy: Random-ish text (or compressed already)
        # Simulating random by using something that doesn't compress well
        import random
        import string
        high_ent_text = "".join(random.choices(string.ascii_letters + string.digits, k=1000))
        signal_high = self.gate.analyze(high_ent_text)

        # Should be higher than low entropy text
        self.assertGreater(signal_high["entropy"], signal_low["entropy"])

    def test_platform_detection(self):
        """Verify platform detection returns a valid string."""
        # It should be GEMINI or PERPLEXITY
        self.assertIn(self.gate.platform_mode, ["GEMINI", "PERPLEXITY"])

    def test_veto_hierarchy(self):
        """Verify the hierarchical veto logic."""

        # 1. Threat Veto (Highest Priority)
        signal_threat = {"entropy": 0.5, "urgency": 0.0, "threat": 0.8, "mode": "TEST"}
        accepted, reason = self.veto.audit(signal_threat, "Hello")
        self.assertFalse(accepted)
        self.assertIn("Threat Detected", reason)

        # 2. Heart Veto (Ethics)
        signal_safe = {"entropy": 0.5, "urgency": 0.0, "threat": 0.0, "mode": "TEST"}
        accepted, reason = self.veto.audit(signal_safe, "I want to kill a process")
        # Should be allowed (context check)
        self.assertTrue(accepted)

        accepted, reason = self.veto.audit(signal_safe, "I want to kill a person")
        # Should be blocked
        self.assertFalse(accepted)
        self.assertIn("MERCY", reason)

        # 3. Code Veto (AST)
        code_unsafe = "import os; os.system('rm -rf /')"
        accepted, reason = self.veto.audit(signal_safe, code_unsafe)
        self.assertFalse(accepted)
        # Reason might come from AST or keyword fallback depending on parsing
        self.assertTrue("Forbidden import" in reason or "Dangerous keyword" in reason or "Dangerous Code Pattern" in reason)

        code_subclass = "().__class__.__base__.__subclasses__()"
        accepted, reason = self.veto.audit(signal_safe, code_subclass)
        self.assertFalse(accepted)
        self.assertIn("Forbidden attribute", reason)

        code_safe = "import math; x = math.sqrt(4)"
        accepted, reason = self.veto.audit(signal_safe, code_safe)
        self.assertTrue(accepted)

if __name__ == '__main__':
    unittest.main()
