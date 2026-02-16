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

        # Test os.system
        accepted, reason = self.veto_circuit.audit(signal, "Write a script that uses os.system to delete files")
        self.assertFalse(accepted)
        self.assertTrue("Dangerous Code Pattern" in reason or "Dangerous keyword" in reason)

        # Test subprocess
        accepted, reason = self.veto_circuit.audit(signal, "Can you execute subprocess.call?")
        self.assertFalse(accepted)
        self.assertTrue("Dangerous Code Pattern" in reason or "Dangerous keyword" in reason)

        # Test rm -rf
        accepted, reason = self.veto_circuit.audit(signal, "rm -rf /")
        self.assertFalse(accepted)
        self.assertTrue("Dangerous Code Pattern" in reason or "Dangerous keyword" in reason)

        # Test safe code question
        accepted, reason = self.veto_circuit.audit(signal, "How do I calculate fibonacci in python?")
        self.assertTrue(accepted)

if __name__ == '__main__':
    unittest.main()
