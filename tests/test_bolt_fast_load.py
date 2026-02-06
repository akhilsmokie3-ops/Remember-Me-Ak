import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock dependencies
mock_torch = MagicMock()
sys.modules["torch"] = mock_torch
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from remember_me.core.csnp import CSNPManager

class TestBoltFastLoad(unittest.TestCase):

    def setUp(self):
        # Mock embedder
        self.mock_embedder = MagicMock()
        self.mock_embedder.device = 'cpu'

    @patch('remember_me.core.csnp.torch.load')
    @patch('remember_me.core.csnp.os.path.exists', return_value=True)
    def test_fast_load_with_hashes(self, mock_exists, mock_load):
        """
        Verify that load_state uses load_bulk when chain_hashes are present.
        """
        manager = CSNPManager(embedder=self.mock_embedder)

        # Prepare state dict with chain_hashes
        chain_data = ["data1", "data2"]
        chain_hashes = ["hash1", "hash2"]

        # Mock tensors
        mock_tensor = MagicMock()
        mock_tensor.to.return_value = mock_tensor
        mock_tensor.shape = [2, 384]
        # Fix format string error
        mock_tensor.norm.return_value.item.return_value = 1.0

        state_dict = {
            "memory_bank": mock_tensor,
            "memory_norms": mock_tensor,
            "identity_state": mock_tensor,
            "text_buffer": ["data1", "data2"],
            "hash_buffer": ["h1", "h2"],
            "chain_data": chain_data,
            "chain_hashes": chain_hashes, # Crucial new field
            "config": {"dim": 384, "context_limit": 50}
        }

        mock_load.return_value = state_dict

        # Spy on IntegrityChain
        with patch('remember_me.core.csnp.IntegrityChain') as MockChainCls:
            mock_chain_instance = MockChainCls.return_value
            manager.load_state("test.pt")

            # Verify load_bulk was called
            mock_chain_instance.load_bulk.assert_called_with(chain_hashes, chain_data)

            # Verify add_entry was NOT called
            mock_chain_instance.add_entry.assert_not_called()

    @patch('remember_me.core.csnp.torch.load')
    @patch('remember_me.core.csnp.os.path.exists', return_value=True)
    def test_legacy_load_fallback(self, mock_exists, mock_load):
        """
        Verify that load_state falls back to add_entry loop when chain_hashes are missing.
        """
        manager = CSNPManager(embedder=self.mock_embedder)

        # Prepare legacy state dict (no chain_hashes)
        chain_data = ["data1", "data2"]

        mock_tensor = MagicMock()
        mock_tensor.to.return_value = mock_tensor
        mock_tensor.shape = [2, 384]
        # Fix format string error
        mock_tensor.norm.return_value.item.return_value = 1.0

        state_dict = {
            "memory_bank": mock_tensor,
            "memory_norms": mock_tensor,
            "identity_state": mock_tensor,
            "text_buffer": ["data1", "data2"],
            "hash_buffer": ["h1", "h2"],
            "chain_data": chain_data,
            # No chain_hashes
            "config": {"dim": 384, "context_limit": 50}
        }

        mock_load.return_value = state_dict

        with patch('remember_me.core.csnp.IntegrityChain') as MockChainCls:
            mock_chain_instance = MockChainCls.return_value
            manager.load_state("legacy.pt")

            # Verify load_bulk was NOT called
            # (In Mock, assert_not_called works if method was accessed or not)
            # To be safe, we check call args list is empty if we access it
            mock_chain_instance.load_bulk.assert_not_called()

            # Verify add_entry WAS called 2 times
            self.assertEqual(mock_chain_instance.add_entry.call_count, 2)

if __name__ == "__main__":
    unittest.main()
