import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import shutil

sys.path.append(os.path.abspath("src"))

class TestQDMA(unittest.TestCase):
    def setUp(self):
        # Create temp dir for qdma data
        self.test_dir = os.path.abspath("test_qdma_data")
        os.environ["QDMA_DATA_DIR"] = self.test_dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('remember_me.core.qdma.VectorSpace')
    @patch('remember_me.core.qdma.DetoxSystem')
    def test_dream_entity(self, MockDetox, MockVector):
        from remember_me.core.qdma import DreamEntity

        e = DreamEntity(id="test", embedding=[0.1, 0.2], shards=["s1"])
        self.assertEqual(e.id, "test")
        self.assertEqual(e.shards, ["s1"])

        d = e.to_dict()
        self.assertEqual(d["id"], "test")

        e2 = DreamEntity.from_dict(d)
        self.assertEqual(e2.id, "test")

    @patch('remember_me.core.qdma.DreamRegistry')
    @patch('remember_me.core.qdma.DreamSeedIndex')
    @patch('remember_me.core.qdma.ProjectionEngine')
    @patch('remember_me.core.qdma.FusionCore')
    def test_storage_put_get(self, MockFusion, MockProj, MockSeed, MockReg):
        from remember_me.core.qdma import DreamStorage, DreamEntity

        # Mock dependencies
        reg = MockReg()
        seed = MockSeed()
        fusion = MockFusion()
        proj = MockProj()

        # Initialize storage
        storage = DreamStorage(reg, seed, fusion, proj)

        # Test put_entity
        e = DreamEntity(id="test", embedding=[0.1]*128, shards=["s1"])
        storage.put_entity(e)

        # Verify hot storage
        self.assertIn("test", storage.hot)

        # Verify get
        retrieved = storage.get_entity("test")
        self.assertEqual(retrieved.id, "test")

        # Cleanup
        storage.shutdown()

if __name__ == '__main__':
    unittest.main()
