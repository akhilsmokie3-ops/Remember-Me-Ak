
import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["duckduckgo_search"] = MagicMock()
sys.modules["diffusers"] = MagicMock()
sys.modules["pyttsx3"] = MagicMock()
sys.modules["remember_me.integrations.engine"] = MagicMock()
sys.modules["remember_me.integrations.tools"] = MagicMock()

# Manually define the class structure if import fails,
# but we want to test the ACTUAL file.
# So we need to make sure the imports inside agent.py work.
# agent.py imports: re, io, sys, traceback, typing
# from remember_me.integrations.tools import ToolArsenal
# from remember_me.integrations.engine import ModelRegistry

# Now we can import agent
# We need to set PYTHONPATH first in bash
from remember_me.integrations.agent import SovereignAgent

import time

def test_execute_python_performance():
    print("Testing SovereignAgent._execute_python performance...")

    # Setup
    engine = MagicMock()
    tools = MagicMock()
    agent = SovereignAgent(engine, tools)

    code = "a = 1 + 1"

    # Warmup
    for _ in range(2):
        agent.sandbox.execute(code)

    start = time.time()
    iterations = 10 # Process spawning is heavy
    for _ in range(iterations):
        agent.sandbox.execute(code)
    end = time.time()

    print(f"Execution time for {iterations} calls: {end - start:.4f}s")
    print(f"Per call: {(end - start) / iterations * 1000:.4f}ms")

if __name__ == "__main__":
    test_execute_python_performance()
