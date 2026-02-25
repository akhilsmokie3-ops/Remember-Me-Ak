import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies before import
sys.modules["requests"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["psutil"] = MagicMock()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from remember_me.integrations.agent import SovereignAgent

class TestAgentTCell(unittest.TestCase):
    def test_tcell_trigger(self):
        # Setup real agent with mocked engine and tools
        engine = MagicMock()
        tools = MagicMock()

        agent = SovereignAgent(engine, tools)

        # Configure velocity with proper config
        agent.velocity = MagicMock()
        agent.velocity.determine_mode.return_value = "SYNC_POINT"
        agent.velocity.get_execution_config.return_value = {
            "timeout": 10, "search_depth": 1, "max_retries": 3, "system_suffix": "TEST"
        }

        # Mock Signal — include all required keys
        agent.signal_gate.analyze = MagicMock(return_value={
            "entropy": 0.5, "urgency": 0.0, "threat": 0.0,
            "challenge": 0.0, "sentiment": 0.0,
            "mode": "SYNC_POINT", "platform": "TEST",
            "gpu_available": False,
            "battery": {"percent": 100, "plugged": True},
            "timestamp": 0
        })

        # Mock Veto — returns 3-tuple
        agent.veto_circuit.audit = MagicMock(return_value=(True, "OK", None))
        agent.veto_circuit.audit_code = MagicMock(return_value=(True, "Safe"))

        # Mock sandbox to return a CORRECTION (required for T-Cell to produce output)
        agent.sandbox = MagicMock()
        agent.sandbox.execute.return_value = "CORRECTION: The actual answer is 99"

        # Mock Responses — first response has low confidence, triggers regeneration loop.
        # Need: 1 synthesis + 3 retries + 1 T-Cell verify = 5 engine calls
        engine.generate_response.side_effect = [
            "The magic number is 42.",       # Initial synthesis -> low confidence
            "The magic number is 42.",       # Retry 1 -> low confidence
            "The magic number is 42.",       # Retry 2 -> low confidence
            "The magic number is 42.",       # Retry 3 -> medium confidence, exits loop
            "```python\nprint('CORRECTION: The actual answer is 99')\n```"  # T-Cell verification code
        ]

        # Mock Proprioception to always flag low confidence
        audit_result_low = {
            "confidence": 0.5,
            "hallucination_risk": 0.5,
            "executable": False,
            "cited": False,
            "fatigue": 0.0,
            "regenerate": True
        }
        # After max_retries (3), we exit the regen loop. The exit audit needs:
        # confidence in (0.5, 0.9) to trigger T-Cell
        audit_result_medium = {
            "confidence": 0.7,
            "hallucination_risk": 0.1,
            "executable": False,
            "cited": False,
            "fatigue": 0.0,
            "regenerate": False  # Stop regeneration
        }
        agent.proprioception.audit_output = MagicMock(side_effect=[
            audit_result_low,   # Initial audit -> regenerate
            audit_result_low,   # Retry 1 -> regenerate
            audit_result_low,   # Retry 2 -> regenerate
            audit_result_medium # Retry 3 -> stop regen, confidence in T-Cell range
        ])

        # Run
        result = agent.run("Tell me magic", "")

        # Verify T-Cell was triggered — actual format is [T-CELL AUDIT]
        self.assertIn("[T-CELL AUDIT]", result["response"])
        self.assertIn("CORRECTION", result["response"])

        agent.shutdown()

if __name__ == "__main__":
    unittest.main()
