import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.core.sandbox import SecurePythonSandbox

class TestSandboxSecurity(unittest.TestCase):
    def setUp(self):
        self.sandbox = SecurePythonSandbox()

    def tearDown(self):
        self.sandbox.shutdown()

    def test_block_socket(self):
        code = "import socket"
        result = self.sandbox.execute(code)
        self.assertIn("strictly forbidden", result)

    def test_block_requests(self):
        code = "import requests"
        result = self.sandbox.execute(code)
        self.assertIn("strictly forbidden", result)

    def test_allow_math(self):
        code = "import math; print(math.pi)"
        result = self.sandbox.execute(code)
        self.assertIn("3.14", result)

    def test_block_arbitrary(self):
        code = "import ctypes"
        result = self.sandbox.execute(code)
        self.assertIn("forbidden", result)

if __name__ == "__main__":
    unittest.main()
