import unittest
from unittest.mock import MagicMock, patch
import time
import re
import sys
import os
import concurrent.futures

# Mock dependencies
sys.modules["torch"] = MagicMock()
sys.modules["requests"] = MagicMock() # Mock requests
sys.path.append(os.path.abspath("src"))

from remember_me.core.nervous_system import VetoCircuit
from remember_me.core.frameworks import HaiyueMicrocosm
from remember_me.integrations.agent import SovereignAgent

class TestNervousSystemV2(unittest.TestCase):
    def setUp(self):
        self.veto = VetoCircuit()
        self.haiyue = HaiyueMicrocosm()
        self.mock_engine = MagicMock()
        self.mock_tools = MagicMock()
        self.agent = SovereignAgent(self.mock_engine, self.mock_tools)
        # Mock internal components for isolation
        self.agent.velocity = MagicMock()
        self.agent.signal_gate = MagicMock()
        self.agent.veto_circuit = MagicMock()

    def test_slang_enforcement(self):
        """
        Test that the agent instructions enforce S-Lang output in tags,
        and the agent correctly extracts it.
        """
        # Mock engine to return S-Lang tagged response
        response_with_slang = (
            "<s_lang>\n$Target: INPUT >> $Mode: TEST >> $Entropy: 0.1 !! Action: REPLY\n</s_lang>\n"
            "This is the actual user response."
        )
        self.mock_engine.generate_response.return_value = response_with_slang

        # We need to mock the internal components to avoid side effects
        self.agent.signal_gate.analyze.return_value = {
            "entropy": 0.1, "urgency": 0.1, "threat": 0.0,
            "mode": "TEST", "platform": "TEST", "battery": {"percent": 100, "plugged": True}
        }
        self.agent.veto_circuit.audit.return_value = (True, "OK", None)
        self.agent.velocity.determine_mode.return_value = "TEST"
        self.agent.velocity.get_execution_config.return_value = {"timeout": 1, "max_retries": 0}

        # Run agent
        result = self.agent.run("Hello", "Context")

        # Verify S-Lang was extracted to telemetry
        # This will fail initially because the extraction logic isn't implemented
        self.assertIn("$Target: INPUT", result["telemetry"]["s_lang_trace"])
        # Verify S-Lang was REMOVED from the main response
        self.assertNotIn("<s_lang>", result["response"])
        self.assertIn("This is the actual user response.", result["response"])
        # Check that the proprioception footer is present (added by phase 5)
        self.assertIn("[DIGITAL PROPRIOCEPTION]", result["response"])

    def test_haiyue_parallelism(self):
        """
        Verify that Haiyue Microcosm actually runs in parallel.
        We'll make the mock engine sleep for 0.5s per call.
        If serial: 1.5s. If parallel: ~0.5s.
        """
        def slow_generate(user_input, context, system_prompt=None):
            time.sleep(0.5)
            return "Simulated Result"

        self.mock_engine.generate_response.side_effect = slow_generate

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        start_time = time.time()

        # Run simulation
        future = self.haiyue.run_simulation(executor, self.mock_engine, "input", "context")
        results = future.result()

        duration = time.time() - start_time
        executor.shutdown()

        print(f"Haiyue Parallel Duration: {duration:.2f}s")
        # This will likely pass if parallelism is working, fail if not
        self.assertLess(duration, 1.0, "Haiyue Microcosm should run in parallel (< 1.0s for 3x 0.5s tasks)")
        self.assertEqual(len(results), 3)

    def test_enhanced_veto_security(self):
        """
        Test new security rules for VetoCircuit.
        """
        # Obfuscated import keyword construction
        unsafe_1 = "x = '__im' + 'port__'" # Becomes "__import__"

        signal = {"threat": 0.0, "mode": "TEST"}

        accepted_1, _ = self.veto.audit_code(unsafe_1)
        self.assertFalse(accepted_1, "Should catch string concatenation forming '__import__'")

    def test_veto_false_positives(self):
        """
        Test that common words are not blocked (Regression Fix).
        """
        safe_1 = "status = 'Execution complete'"
        safe_2 = "role = 'executive'"

        acc_1, _ = self.veto.audit_code(safe_1)
        self.assertTrue(acc_1, "Should allow 'Execution'")

        acc_2, _ = self.veto.audit_code(safe_2)
        self.assertTrue(acc_2, "Should allow 'executive'")

if __name__ == "__main__":
    unittest.main()
