import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from remember_me.core.sandbox import SecurePythonSandbox

class TestSecurePythonSandbox(unittest.TestCase):
    def setUp(self):
        # Shorter timeout for tests to be fast
        self.sandbox = SecurePythonSandbox(timeout=1)

    def test_safe_execution(self):
        code = "print(1 + 1)"
        result = self.sandbox.execute(code)
        self.assertEqual(result.strip(), "2")

    def test_unsafe_import(self):
        code = "import os\nos.system('echo malicious')"
        result = self.sandbox.execute(code)
        self.assertIn("forbidden", result)
        self.assertIn("ImportError", result)

    def test_infinite_loop_timeout(self):
        code = "while True: pass"
        result = self.sandbox.execute(code)
        self.assertIn("Timed Out", result)

    def test_allowed_import(self):
        code = "import math\nprint(math.sqrt(4))"
        result = self.sandbox.execute(code)
        self.assertEqual(result.strip(), "2.0")

if __name__ == "__main__":
    unittest.main()
