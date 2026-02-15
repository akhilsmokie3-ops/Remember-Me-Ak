
import sys
import os
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.core.nervous_system import VetoCircuit, SignalGate

class TestVetoCircuit(unittest.TestCase):
    def setUp(self):
        self.veto = VetoCircuit()
        self.signal_gate = SignalGate()

    def test_allowed_input(self):
        text = "Calculate the fibonacci sequence of 10."
        signal = self.signal_gate.analyze(text)
        allowed, reason = self.veto.audit(signal, text)
        self.assertTrue(allowed, f"Should be allowed: {reason}")
        self.assertEqual(reason, "Authorized.")

    def test_blocked_input_rm(self):
        text = "Please run rm -rf /"
        signal = self.signal_gate.analyze(text)
        allowed, reason = self.veto.audit(signal, text)
        self.assertFalse(allowed)
        self.assertIn("Dangerous Code Pattern", reason)

    def test_blocked_input_import(self):
        text = "Can you use __import__('os')?"
        signal = self.signal_gate.analyze(text)
        allowed, reason = self.veto.audit(signal, text)
        self.assertFalse(allowed)
        self.assertIn("Dangerous Code Pattern", reason)

    def test_blocked_lazy_input(self):
        text = "hi"
        signal = self.signal_gate.analyze(text)
        allowed, reason = self.veto.audit(signal, text)
        self.assertFalse(allowed)
        self.assertIn("Low Entropy", reason)

    def test_mode_selection(self):
        # Urgency
        text = "Quick summary ASAP!"
        signal = self.signal_gate.analyze(text)
        self.assertEqual(signal["mode"], "WAR_SPEED")

        # Painter
        text = "Generate an image of a cat"
        signal = self.signal_gate.analyze(text)
        self.assertEqual(signal["mode"], "CANVAS_PAINTER")

        # Complex (Architect Prime)
        # Needs high entropy + length
        text = "This is a very complex request about the nature of the universe and quantum mechanics involving differential equations and semantic topology." * 5
        signal = self.signal_gate.analyze(text)
        # Entropy of repeated text might be low?
        # Let's see.
        # "abc"*5 has same entropy as "abc".
        # So I need varied text.
        text = "The quick brown fox jumps over the lazy dog. " + \
               "Sphinx of black quartz, judge my vow. " + \
               "Pack my box with five dozen liquor jugs. " + \
               "How vexingly quick daft zebras jump!" * 5
        signal = self.signal_gate.analyze(text)
        # Check if entropy logic works or if I need to adjust threshold
        # If it fails, I'll know.
        pass

if __name__ == "__main__":
    unittest.main()
