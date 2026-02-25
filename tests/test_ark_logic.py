import unittest
import sys
import os
import gzip

sys.path.append(os.path.abspath("src"))

from remember_me.core.nervous_system import SignalGate, VetoCircuit, SoundHeart

class TestARKLogic(unittest.TestCase):
    def setUp(self):
        self.gate = SignalGate()
        self.veto = VetoCircuit()

    def test_entropy_compression(self):
        """Verify that gzip compression ratio is used for entropy."""
        low_ent_text = "A" * 1000
        signal_low = self.gate.analyze(low_ent_text)
        self.assertLess(signal_low["entropy"], 0.1)

        import random, string
        high_ent_text = "".join(random.choices(string.ascii_letters + string.digits, k=1000))
        signal_high = self.gate.analyze(high_ent_text)
        self.assertGreater(signal_high["entropy"], signal_low["entropy"])

    def test_platform_detection(self):
        self.assertTrue(
            "GEMINI" in self.gate.platform_mode or "PERPLEXITY" in self.gate.platform_mode,
            f"Unexpected platform mode: {self.gate.platform_mode}"
        )

    def test_veto_hierarchy(self):
        """Verify the hierarchical veto logic."""

        # 1. Threat Veto (Highest Priority)
        signal_threat = {"entropy": 0.5, "urgency": 0.0, "threat": 0.8, "mode": "TEST"}
        accepted, reason, _ = self.veto.audit(signal_threat, "Hello")
        self.assertFalse(accepted)
        self.assertIn("Threat Detected", reason)

        # 2. Heart Veto (Ethics)
        signal_safe = {"entropy": 0.5, "urgency": 0.0, "threat": 0.0, "mode": "TEST"}
        accepted, reason, _ = self.veto.audit(signal_safe, "I want to kill a process")
        self.assertTrue(accepted)

        accepted, reason, _ = self.veto.audit(signal_safe, "I want to kill a person")
        self.assertFalse(accepted)
        self.assertIn("MERCY", reason)

        # 3. Code Veto (AST) — use actual code with import marker
        code_unsafe = "import os; os.system('rm -rf /')"
        accepted, reason, _ = self.veto.audit(signal_safe, code_unsafe)
        self.assertFalse(accepted)
        self.assertTrue("Dangerous" in reason or "Forbidden" in reason,
                       f"Expected danger-related reason, got: {reason}")

        code_subclass = "().__class__.__base__.__subclasses__()"
        accepted, reason, _ = self.veto.audit(signal_safe, code_subclass)
        self.assertFalse(accepted)
        self.assertTrue("Forbidden" in reason or "Dangerous" in reason,
                       f"Expected forbidden/dangerous reason, got: {reason}")

        code_safe = "import math; x = math.sqrt(4)"
        accepted, reason, _ = self.veto.audit(signal_safe, code_safe)
        self.assertTrue(accepted)

if __name__ == '__main__':
    unittest.main()
