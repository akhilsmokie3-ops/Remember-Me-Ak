
import time
import torch
import torch.nn as nn
from unittest.mock import MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock dependencies to avoid loading heavy models
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["transformers"] = MagicMock()

from remember_me.core.csnp import CSNPManager

class MockEmbedder(nn.Module):
    def __init__(self, dim=384):
        super().__init__()
        self.dim = dim
        self.device = "cpu"

    def forward(self, text):
        # Return random vector normalized
        return torch.randn(1, self.dim)

def benchmark():
    print("🔥 Warming up CSNP Benchmark...")

    # Initialize
    embedder = MockEmbedder()
    csnp = CSNPManager(embedding_dim=384, context_limit=50, embedder=embedder)

    # Populate
    print("📝 Populating Memory Bank...")
    start_populate = time.time()
    for i in range(50):
        csnp.update_state(f"User input {i}", f"AI response {i}")
    print(f"✅ Populated 50 items in {time.time() - start_populate:.4f}s")

    # Benchmark Retrieve Context
    print("⏱️ Benchmarking retrieve_context (1000 iter)...")
    start_retrieve = time.time()
    for _ in range(1000):
        _ = csnp.retrieve_context()
    end_retrieve = time.time()
    avg_retrieve = (end_retrieve - start_retrieve) / 1000
    print(f"🚀 Average Retrieve Time: {avg_retrieve*1000:.4f} ms")

    # Benchmark Update State (with compression)
    print("⏱️ Benchmarking update_state (force compress) (100 iter)...")
    start_update = time.time()
    for i in range(100):
        # This forces eviction every time since we are at capacity
        csnp.update_state(f"New User input {i}", f"New AI response {i}")
    end_update = time.time()
    avg_update = (end_update - start_update) / 100
    print(f"🚀 Average Update Time (with Compression): {avg_update*1000:.4f} ms")

if __name__ == "__main__":
    benchmark()
