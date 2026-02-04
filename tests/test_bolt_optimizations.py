import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock torch and heavy dependencies BEFORE importing anything
mock_torch = MagicMock()
sys.modules["torch"] = mock_torch
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()

sys.modules["transformers"] = MagicMock()
sys.modules["duckduckgo_search"] = MagicMock()
sys.modules["diffusers"] = MagicMock()
sys.modules["pyttsx3"] = MagicMock()
sys.modules["xxhash"] = MagicMock()

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Now import targets
from remember_me.integrations.agent import SovereignAgent
from remember_me.core.csnp import CSNPManager
from remember_me.core.embedder import LocalEmbedder
from remember_me.integrations.tools import ToolArsenal

class TestBoltOptimizations(unittest.TestCase):

    def setUp(self):
        # Mocks
        self.engine = MagicMock()
        self.tools = MagicMock()

    def test_sovereign_agent_threadpool_reuse(self):
        """
        Verify that SovereignAgent reuses its ThreadPoolExecutor.
        """
        agent = SovereignAgent(self.engine, self.tools)

        # Verify executor exists (after refactor)
        if not hasattr(agent, '_executor'):
            self.fail("SovereignAgent should have _executor attribute")

        executor_first = agent._executor

        # Simulate run with IMAGE intent
        agent._detect_intents = MagicMock(return_value=["IMAGE"])
        agent.engine.generate_response.return_value = "Response"
        self.tools.generate_image.return_value = "Image Generated"

        agent.run("draw cat", "context")

        executor_second = agent._executor

        self.assertIs(executor_first, executor_second, "Executor should be reused")

        # Verify it wasn't shutdown
        future = agent._executor.submit(lambda: True)
        self.assertTrue(future.result(), "Executor should still be active")

        if hasattr(agent, 'shutdown'):
            agent.shutdown()

    @patch('remember_me.core.csnp.torch.load')
    def test_csnp_load_state_device_enforcement(self, mock_load):
        """
        Verify that load_state forces tensors to the configured device.
        """
        target_device = 'cpu'

        # Mock Embedder
        mock_embedder = MagicMock()
        mock_embedder.device = target_device

        manager = CSNPManager(embedder=mock_embedder)

        # Simulate loaded tensor
        loaded_tensor = MagicMock()
        loaded_tensor.device = 'cuda:0'
        loaded_tensor.shape = [5, 384]
        loaded_tensor.__len__.return_value = 5

        # Mock .to()
        converted_tensor = MagicMock()
        converted_tensor.device = target_device
        loaded_tensor.to.return_value = converted_tensor

        converted_tensor.norm.return_value.item.return_value = 1.0
        converted_tensor.shape = [5, 384]

        state_dict = {
            "memory_bank": loaded_tensor,
            "memory_norms": loaded_tensor,
            "identity_state": loaded_tensor,
            "text_buffer": ["a"] * 5,
            "chain_data": ["a"] * 5,
            "config": {"dim": 384, "context_limit": 50}
        }
        mock_load.return_value = state_dict

        with patch('os.path.exists', return_value=True):
            manager.load_state("fake.pt")

        # Verify loaded tensor was moved to target device
        loaded_tensor.to.assert_any_call(target_device)

    def test_tool_arsenal_lazy_ddgs(self):
        """
        Verify that ToolArsenal initializes DDGS lazily.
        """
        # Create fresh instance
        tools = ToolArsenal()

        # 1. Verify not initialized initially
        self.assertIsNone(tools.ddgs, "DDGS should be None on init")

        # 2. Simulate web_search call
        mock_ddgs_module = sys.modules["duckduckgo_search"]
        mock_ddgs_cls = MagicMock()
        mock_ddgs_instance = MagicMock()
        mock_ddgs_cls.return_value = mock_ddgs_instance

        # Important: The module mock needs to return our class mock when accessed as .DDGS
        mock_ddgs_module.DDGS = mock_ddgs_cls

        # The instance needs to return a result list
        mock_ddgs_instance.text.return_value = [{"title": "Test Title", "body": "Test Body"}]

        # We need to ensure _ddgs_imported is reset or handled,
        # but since we are running in the same process, it might be False initially?
        # In tools.py: _ddgs_imported = False (module level).
        # Since imports are cached, reloading might be tricky, but we are just calling the function.
        # Assuming this is the first time running this test in this process (which it is for the test runner usually).
        # However, if other tests imported ToolArsenal, the module is loaded.
        # But _ddgs_imported is a global in tools.py.
        # We can reset it manually if needed, but 'ToolArsenal' import at top of file sets it to False.
        # If previous tests called web_search, it might be True.
        # Let's inspect remember_me.integrations.tools global state if possible, or just rely on the fact that we mocked DDGS.

        # Reset the global flag to ensure we test the import logic
        import remember_me.integrations.tools as tools_mod
        tools_mod._ddgs_imported = False
        tools_mod.DDGS = None

        result = tools.web_search("test query")

        # 3. Verify DDGS was initialized
        self.assertIsNotNone(tools.ddgs, "DDGS should be initialized after search")
        # Check if it's our mock instance (might fail if _import_ddgs grabs a different mock object from sys.modules)
        # But sys.modules["duckduckgo_search"].DDGS is what we set.

        self.assertIn("- Test Title: Test Body", result)

        # Verify call
        mock_ddgs_instance.text.assert_called_with("test query", max_results=3)

if __name__ == "__main__":
    unittest.main()
