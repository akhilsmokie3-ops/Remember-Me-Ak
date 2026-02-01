import unittest
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from remember_me.core.integrity import IntegrityChain, MerkleNode

class TestIntegrityRefactor(unittest.TestCase):

    def test_soa_structure(self):
        """
        Verify that IntegrityChain uses the new SoA structure.
        """
        chain = IntegrityChain()
        self.assertTrue(hasattr(chain, 'ordered_hashes'), "Should have ordered_hashes")
        self.assertTrue(hasattr(chain, 'ordered_data'), "Should have ordered_data")
        self.assertTrue(hasattr(chain, 'leaf_hashes'), "Should have leaf_hashes")
        self.assertFalse(hasattr(chain, 'leaves'), "Should NOT have old leaves list")

    def test_add_entry_and_verify(self):
        """
        Verify adding entries updates all buffers correctly.
        """
        chain = IntegrityChain()
        data = "Hello World"

        h = chain.add_entry(data)

        self.assertIn(h, chain.ordered_hashes)
        self.assertIn(data, chain.ordered_data)
        self.assertIn(h, chain.leaf_hashes)
        self.assertTrue(chain.verify(data))
        self.assertTrue(chain.verify_hash(h))
        self.assertFalse(chain.verify("Fake"))

    def test_tree_construction(self):
        """
        Verify Merkle Tree construction logic works with SoA.
        """
        chain = IntegrityChain()
        chain.add_entry("A")
        chain.add_entry("B")
        chain.add_entry("C")

        root_hash = chain.get_root_hash()
        self.assertIsNotNone(chain.root)
        self.assertIsInstance(chain.root, MerkleNode)
        self.assertNotEqual(root_hash, "00000000")

        # Verify determinism
        chain2 = IntegrityChain()
        chain2.add_entry("A")
        chain2.add_entry("B")
        chain2.add_entry("C")
        self.assertEqual(chain.get_root_hash(), chain2.get_root_hash())

    def test_fallback_hashing(self):
        """
        Verify hashing works (whether xxhash or hashlib).
        """
        chain = IntegrityChain()
        data = "test"
        h = chain._hash(data)
        self.assertIsInstance(h, str)
        self.assertTrue(len(h) > 0)

        # Manually verify fallback if xxhash is missing
        try:
            import xxhash
        except ImportError:
            import hashlib
            expected = hashlib.sha256(data.encode('utf-8')).hexdigest()
            self.assertEqual(h, expected, "Should use sha256 fallback")

if __name__ == "__main__":
    unittest.main()
