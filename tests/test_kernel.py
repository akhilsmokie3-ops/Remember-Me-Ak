import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath("src"))

class TestKernel(unittest.TestCase):
    @patch('remember_me.integrations.engine.ModelRegistry')
    @patch('remember_me.core.csnp.CSNPManager')
    @patch('remember_me.integrations.tools.ToolArsenal')
    def test_kernel_init(self, MockTools, MockCSNP, MockRegistry):
        from remember_me.kernel import Kernel

        # Mock dependencies
        MockRegistry.return_value.load_model.return_value = True

        k = Kernel(model_key="tiny")

        # Verify components initialized
        self.assertTrue(MockRegistry.called)
        self.assertTrue(MockCSNP.called)
        self.assertTrue(MockTools.called)

        # Verify structure
        self.assertIsNotNone(k.engine)
        self.assertIsNotNone(k.shield)
        self.assertIsNotNone(k.agent)

    @patch('remember_me.integrations.engine.ModelRegistry')
    @patch('remember_me.core.csnp.CSNPManager')
    @patch('remember_me.integrations.tools.ToolArsenal')
    def test_run_cycle(self, MockTools, MockCSNP, MockRegistry):
        from remember_me.kernel import Kernel
        k = Kernel(model_key=None)

        # Mock agent run
        k.agent.run = MagicMock(return_value={
            "response": "Test Response",
            "tool_outputs": [],
            "artifacts": [],
            "telemetry": {}
        })

        response = k.run_cycle("Hello")
        self.assertEqual(response, "Test Response")
        # Verify context retrieved
        k.shield.retrieve_context.assert_called()
        # Verify state updated
        k.shield.update_state.assert_called_with("Hello", "Test Response")

if __name__ == '__main__':
    unittest.main()
