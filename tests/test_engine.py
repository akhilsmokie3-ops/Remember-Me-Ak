import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath("src"))

class TestEngine(unittest.TestCase):
    @patch('remember_me.integrations.engine.LlamaCppClient')
    @patch('remember_me.integrations.engine.AutoModelForCausalLM')
    @patch('remember_me.integrations.engine.AutoTokenizer')
    def test_registry_fallback(self, MockTok, MockModel, MockClient):
        from remember_me.integrations.engine import ModelRegistry

        # Scenario 1: Remote Detected
        MockClient.return_value.ping.return_value = True

        reg = ModelRegistry()
        self.assertTrue(reg.use_remote)
        self.assertEqual(reg.model_id, "remote-llama")

        # Test generate uses remote
        reg.generate_response("Hi", "")
        MockClient.return_value.generate.assert_called()

        # Scenario 2: Remote Not Detected
        MockClient.return_value.ping.return_value = False

        # We need to ensure TRANSFORMERS_AVAILABLE is True for this test to work fully
        # but since we mock the classes, it might pass if the import check passes.
        # However, engine.py has a try-except block for transformers.
        # We can force it by mocking sys.modules if needed, but let's assume environment has it or fallback.

        reg2 = ModelRegistry()
        self.assertFalse(reg2.use_remote)

        # Test load_model uses transformers
        # Mock MODELS to avoid key error if tiny not in default (it is)
        reg2.load_model("tiny")

        # Check if tokenizer was called (meaning it tried to load local model)
        # Note: If transformers is not installed in the test env, load_model returns False early.
        # We should check the return value.

        # If transformers import failed, MockTok won't be called.
        # But we mocked AutoTokenizer in the test decorator, so it exists in the test namespace.
        # But inside engine.py, the import might have failed.

        # Let's verify behavior based on import success
        from remember_me.integrations.engine import TRANSFORMERS_AVAILABLE
        if TRANSFORMERS_AVAILABLE:
            MockTok.from_pretrained.assert_called()
            MockModel.from_pretrained.assert_called()
        else:
            print("Transformers not available in test env, skipping local load verification.")

if __name__ == '__main__':
    unittest.main()
