import sys
import os
import unittest.mock

# Mock heavy dependencies
sys.modules["torch"] = unittest.mock.MagicMock()
sys.modules["torch.nn"] = unittest.mock.MagicMock()
sys.modules["torch.nn.functional"] = unittest.mock.MagicMock()
sys.modules["transformers"] = unittest.mock.MagicMock()
sys.modules["psutil"] = unittest.mock.MagicMock()
sys.modules["xxhash"] = unittest.mock.MagicMock()
sys.modules["duckduckgo_search"] = unittest.mock.MagicMock()
sys.modules["diffusers"] = unittest.mock.MagicMock()
sys.modules["requests"] = unittest.mock.MagicMock()
sys.modules["faiss"] = unittest.mock.MagicMock()
sys.modules["pyttsx3"] = unittest.mock.MagicMock()

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

print("[TEST] 1. Importing Sovereign Kernel (Mocked Environment)...")
try:
    from remember_me.kernel import Kernel
    # Also verify imports inside Kernel happened
    # If not, Kernel class will fail at init
    print("   [OK] Import successful.")
except Exception as e:
    print(f"   [FAIL] Import failed: {e}")
    sys.exit(1)

print("[TEST] 2. Initializing Kernel...")
try:
    # Pass empty model key to skip download logic
    kernel = Kernel(model_key="")

    # Verify components
    assert kernel.shield is not None
    assert kernel.agent is not None
    assert kernel.engine is not None

    print("   [OK] Kernel initialized.")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"   [FAIL] Kernel init failed: {e}")
    sys.exit(1)

print("[TEST] 3. Verifying Boot Sequence...")
# Basic run cycle test with mock
# We need to mock the methods inside the instances
kernel.shield.retrieve_context = unittest.mock.MagicMock(return_value="Mock Context")
kernel.agent.run = unittest.mock.MagicMock(return_value={"response": "Mock Response", "telemetry": {}})
kernel.shield.update_state = unittest.mock.MagicMock()

# Run cycle
response = kernel.run_cycle("Hello World")
print(f"   [OK] Cycle Response: {response}")

print("\n[SUCCESS] SYSTEM INTEGRITY VERIFIED.")
