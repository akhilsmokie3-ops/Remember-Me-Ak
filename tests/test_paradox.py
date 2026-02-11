import unittest
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from remember_me.core.paradox import ParadoxEngine

class TestParadoxEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ParadoxEngine()

    def test_check_for_paradox_short_chain(self):
        """Test that chains shorter than 3 do not trigger paradox."""
        self.assertFalse(self.engine.check_for_paradox(None, []))
        self.assertFalse(self.engine.check_for_paradox(None, ["a"]))
        self.assertFalse(self.engine.check_for_paradox(None, ["a", "a"]))

    def test_check_for_paradox_true(self):
        """Test that 3 identical elements at the end trigger paradox."""
        self.assertTrue(self.engine.check_for_paradox(None, ["a", "a", "a"]))
        self.assertTrue(self.engine.check_for_paradox(None, ["b", "a", "a", "a"]))
        self.assertTrue(self.engine.check_for_paradox(None, ["a", "b", "c", "c", "c"]))

    def test_check_for_paradox_false(self):
        """Test that non-identical elements at the end do not trigger paradox."""
        self.assertFalse(self.engine.check_for_paradox(None, ["a", "b", "a"]))
        self.assertFalse(self.engine.check_for_paradox(None, ["a", "a", "b"]))
        self.assertFalse(self.engine.check_for_paradox(None, ["a", "b", "c"]))

    def test_resolve(self):
        """Verify resolve increments timeline_count and returns correct message."""
        initial_count = self.engine.timeline_count
        res = self.engine.resolve({})
        self.assertEqual(self.engine.timeline_count, initial_count + 1)
        self.assertIn("PARADOX DETECTED", res)
        self.assertIn(f"Timeline_{self.engine.timeline_count}", res)

    def test_resolve_multiple_times(self):
        """Verify resolve increments timeline_count multiple times."""
        self.engine.resolve({})
        self.engine.resolve({})
        self.assertEqual(self.engine.timeline_count, 2)
        res = self.engine.resolve({})
        self.assertIn("Timeline_3", res)

if __name__ == "__main__":
    unittest.main()
