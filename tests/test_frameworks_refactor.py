import unittest
from unittest.mock import MagicMock, patch
import concurrent.futures
from remember_me.core.frameworks import VelocityPhysics, OISTruthBudget, HaiyueMicrocosm

class TestVelocityPhysics(unittest.TestCase):
    def setUp(self):
        self.physics = VelocityPhysics()

    def test_determine_mode(self):
        # Hare
        self.assertEqual(self.physics.determine_mode({"urgency": 0.7, "entropy": 0.1}), "WAR_SPEED")
        # Turtle
        self.assertEqual(self.physics.determine_mode({"urgency": 0.1, "entropy": 0.7}), "TURTLE_INTEGRITY")
        # Default
        self.assertEqual(self.physics.determine_mode({"urgency": 0.1, "entropy": 0.1}), "SYNC_POINT")
        # Override
        self.assertEqual(self.physics.determine_mode({"mode": "ARCHITECT_PRIME"}), "ARCHITECT_PRIME")

    def test_get_execution_config(self):
        # Check standard config keys exist
        config = self.physics.get_execution_config("WAR_SPEED")
        self.assertIn("timeout", config)
        self.assertIn("search_depth", config)
        self.assertIn("max_retries", config)
        self.assertEqual(config["timeout"], 10)

        # Check fallback
        config = self.physics.get_execution_config("UNKNOWN_MODE")
        self.assertEqual(config["timeout"], 15) # SYNC_POINT default

class TestOISTruthBudget(unittest.TestCase):
    def setUp(self):
        self.budget = OISTruthBudget(100)

    def test_deduct_by_type(self):
        self.budget.deduct_by_type("ASSUMPTION", "Test assumption")
        self.assertEqual(self.budget.budget, 80)

        self.budget.deduct_by_type("UNKNOWN_TYPE")
        self.assertEqual(self.budget.budget, 70) # Default 10

    def test_check(self):
        self.assertTrue(self.budget.check())
        self.budget.deduct(100, "Crash")
        self.assertFalse(self.budget.check())

class TestHaiyueMicrocosm(unittest.TestCase):
    def setUp(self):
        self.haiyue = HaiyueMicrocosm()

    def test_synthesize(self):
        sims = {
            "OPTIMISTIC": "All good.",
            "NEUTRAL": "Okay.",
            "PESSIMISTIC": "Bad."
        }
        prompt = self.haiyue.synthesize("Do something", sims)
        self.assertIn("All good.", prompt)
        self.assertIn("Bad.", prompt)
        self.assertIn("SYNTHESIS INSTRUCTION", prompt)

    def test_run_simulation(self):
        # Mock executor and engine
        mock_executor = MagicMock()
        mock_future = MagicMock()
        mock_executor.submit.return_value = mock_future

        mock_engine = MagicMock()

        # Run
        future = self.haiyue.run_simulation(mock_executor, mock_engine, "input", "context")

        # Verify submit called
        mock_executor.submit.assert_called_once()
        self.assertEqual(future, mock_future)

if __name__ == '__main__':
    unittest.main()
