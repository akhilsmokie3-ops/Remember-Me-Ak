import unittest
import sys
import os
sys.path.append(os.path.abspath("src"))

from remember_me.core.nervous_system import SignalGate, VetoCircuit

class TestNervousSystemSecurity(unittest.TestCase):
    def setUp(self):
        self.veto_circuit = VetoCircuit()
        self.signal_gate = SignalGate()

    def test_dangerous_code_veto(self):
        signal = {"entropy": 0.5, "urgency": 0.5, "threat": 0.0, "mode": "TEST"}

        # Test actual code containing os.system (has "import " marker)
        accepted, reason, _ = self.veto_circuit.audit(signal, "import os; os.system('rm -rf /')")
        self.assertFalse(accepted)
        self.assertTrue("Dangerous" in reason or "Forbidden" in reason,
                       f"Expected danger-related reason, got: {reason}")

        # Test subprocess code
        accepted, reason, _ = self.veto_circuit.audit(signal, "import subprocess; subprocess.call('ls')")
        self.assertFalse(accepted)
        self.assertTrue("Dangerous" in reason or "Forbidden" in reason,
                       f"Expected danger-related reason, got: {reason}")

        # Test rm -rf as code
        accepted, reason, _ = self.veto_circuit.audit(signal, "```bash\nrm -rf /\n```")
        self.assertFalse(accepted)
        self.assertTrue("Dangerous" in reason,
                       f"Expected danger-related reason, got: {reason}")

        # Test safe code question
        accepted, reason, _ = self.veto_circuit.audit(signal, "How do I calculate fibonacci in python?")
        self.assertTrue(accepted)

if __name__ == '__main__':
    unittest.main()
