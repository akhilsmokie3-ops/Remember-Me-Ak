import unittest
from unittest.mock import MagicMock, call, patch
import sys
import os

# Mock dependencies before import
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import after mocking
import torch
from remember_me.math.transport import WassersteinMetric
from remember_me.core.csnp import CSNPManager

class TestBoltBufferOptimization(unittest.TestCase):

    def setUp(self):
        # Reset mocks
        torch.reset_mock()
        torch.nn.functional.reset_mock()

        # Setup common mock returns
        torch.zeros.return_value = MagicMock(name="zeros_tensor")
        torch.argmax.return_value = MagicMock(name="argmax_tensor")
        torch.argmax.return_value.item.return_value = 0 # Default index
        # Fix topk mock to return tuple
        torch.topk.return_value = (MagicMock(name="values"), MagicMock(name="indices"))
        # Fix sort mock to return tuple
        torch.sort.return_value = (MagicMock(name="sorted_indices"), MagicMock(name="sorted_values"))

    def test_compute_cost_matrix_uses_out_buffer(self):
        """
        Verify that compute_cost_matrix uses torch.add(..., out=buffer)
        """
        metric = WassersteinMetric()
        x = MagicMock(name="x")
        y = MagicMock(name="y")
        x_norm = MagicMock(name="x_norm")
        y_norm = MagicMock(name="y_norm")
        out_buffer = MagicMock(name="out_buffer")

        # Call with out buffer
        metric.compute_cost_matrix(x, y, x_norm, y_norm, out=out_buffer)

        # Verify torch.add called with out kwarg
        torch.add.assert_called_with(x_norm, y_norm, out=out_buffer)

    def test_csnp_initializes_transport_buffer(self):
        """
        Verify CSNPManager creates transport_buffer in __init__
        """
        embedder = MagicMock()
        embedder.device = 'cpu'
        embedder.dim = 384

        manager = CSNPManager(embedder=embedder, context_limit=10)

        # Verify transport_buffer attribute exists and is a tensor (mock)
        self.assertTrue(hasattr(manager, 'transport_buffer'))
        # Should be initialized with zeros
        # We expect torch.zeros called with shape [capacity, 1]
        # capacity = 11
        torch.zeros.assert_any_call(11, 1, device='cpu')

    def test_compress_uses_transport_buffer_and_argmax(self):
        """
        Verify _compress passes buffer and uses argmax for excess=1
        """
        embedder = MagicMock()
        embedder.device = 'cpu'
        manager = CSNPManager(embedder=embedder, context_limit=2)

        # Simulate full buffer (size 3, limit 2 -> excess 1)
        manager.size = 3
        # Fill buffers to avoid IndexError
        manager.text_buffer = ["A", "B", "C"]
        manager.hash_buffer = ["hA", "hB", "hC"]

        manager.memory_bank = MagicMock(name="memory_bank")
        manager.memory_norms = MagicMock(name="memory_norms")
        # Mock slicing
        manager.memory_bank.__getitem__.return_value = MagicMock(name="sliced_bank")
        manager.memory_norms.__getitem__.return_value = MagicMock(name="sliced_norms")

        # Mock transport_buffer
        manager.transport_buffer = MagicMock(name="transport_buffer")
        sliced_buffer = MagicMock(name="sliced_buffer")
        manager.transport_buffer.__getitem__.return_value = sliced_buffer

        # Mock metric
        manager.metric = MagicMock()
        # Mock cost matrix return (should be the buffer itself ideally, or whatever compute_cost_matrix returns)
        # In our implementation, compute_cost_matrix will return the buffer (clamped).
        cost_matrix = MagicMock(name="cost_matrix")
        manager.metric.compute_cost_matrix.return_value = cost_matrix

        # Call _compress
        manager._compress()

        # 1. Verify compute_cost_matrix called with out=sliced_buffer
        manager.metric.compute_cost_matrix.assert_called()
        _, kwargs = manager.metric.compute_cost_matrix.call_args
        self.assertEqual(kwargs['out'], sliced_buffer)

        # 2. Verify torch.argmax called on the cost matrix
        torch.argmax.assert_called_with(cost_matrix)

        # 3. Verify F.softmax NOT called (optimization)
        torch.nn.functional.softmax.assert_not_called()

    def test_compress_fallback_softmax(self):
        """
        Verify _compress uses softmax for excess > 1
        """
        embedder = MagicMock()
        manager = CSNPManager(embedder=embedder, context_limit=2)

        # Simulate overflow (size 4, limit 2 -> excess 2)
        manager.size = 4
        manager.text_buffer = ["A", "B", "C", "D"]
        manager.hash_buffer = ["hA", "hB", "hC", "hD"]

        # Mock metric
        manager.metric = MagicMock()
        cost_matrix = MagicMock(name="cost_matrix")
        manager.metric.compute_cost_matrix.return_value = cost_matrix

        # Call _compress
        manager._compress()

        # Verify F.softmax IS called
        torch.nn.functional.softmax.assert_called()

if __name__ == "__main__":
    unittest.main()
