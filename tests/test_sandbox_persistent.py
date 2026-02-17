import sys
import os
import unittest
import time

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.core.sandbox import SecurePythonSandbox

class TestPersistentSandbox(unittest.TestCase):
    def setUp(self):
        self.sandbox = SecurePythonSandbox(timeout=2)

    def tearDown(self):
        self.sandbox.shutdown()

    def test_persistence(self):
        print("\n--- Testing Persistence ---")
        # Step 1: Define variable
        res1 = self.sandbox.execute("x = 42")
        self.assertIn("[No Output]", res1)

        # Step 2: Access variable
        res2 = self.sandbox.execute("print(x)")
        self.assertEqual(res2.strip(), "42")
        print("✓ Persistence Verified: x = 42 retained.")

    def test_reset(self):
        print("\n--- Testing Reset ---")
        # Step 1: Define variable
        self.sandbox.execute("y = 100")

        # Step 2: Reset
        self.sandbox.reset()

        # Step 3: Access variable (should fail)
        res3 = self.sandbox.execute("print(y)")
        self.assertIn("NameError", res3)
        print("✓ Reset Verified: y is gone.")

    def test_timeout_and_recovery(self):
        print("\n--- Testing Timeout ---")
        # Step 1: Infinite Loop
        res1 = self.sandbox.execute("while True: pass")
        self.assertIn("Timed Out", res1)

        # Step 2: Verify Recovery (Worker should be restarted)
        res2 = self.sandbox.execute("print('Recovered')")
        self.assertEqual(res2.strip(), "Recovered")
        print("✓ Timeout Recovery Verified.")

if __name__ == "__main__":
    unittest.main()
