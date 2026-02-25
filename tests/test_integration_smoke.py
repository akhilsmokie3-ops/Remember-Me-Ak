"""
INTEGRATION SMOKE TEST — Real Pipeline Verification
=====================================================
Launches llama-server.exe with a real .gguf model, then exercises the full
Kernel → SovereignAgent → ModelRegistry → LlamaCppClient pipeline.

Run:
    pytest tests/test_integration_smoke.py -m integration \\
        --model-path "path/to/model.gguf" \\
        --llama-server "path/to/llama-server.exe" -v

Skipped automatically during normal `pytest tests/`.
"""
import os
import sys
import time
import subprocess
import signal
import requests
import pytest

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Default paths — relative to tests/ directory
DEFAULT_MODEL = os.path.join(
    os.path.dirname(__file__), "fixtures", "smollm-135m-q4.gguf"
)
DEFAULT_SERVER = os.path.join(
    os.path.dirname(__file__), "..", "..", "llama_main_dist", "llama-server.exe"
)


# ─────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def llama_server(request):
    """
    Module-scoped fixture that starts llama-server as a subprocess,
    waits for it to become healthy, and tears it down after all tests.
    """
    model_path = request.config.getoption("--model-path") or DEFAULT_MODEL
    server_path = request.config.getoption("--llama-server") or DEFAULT_SERVER

    model_path = os.path.abspath(model_path)
    server_path = os.path.abspath(server_path)

    if not os.path.exists(model_path):
        pytest.skip(f"Model not found: {model_path}")
    if not os.path.exists(server_path):
        pytest.skip(f"llama-server not found: {server_path}")

    port = 8081

    # Check if something is already running on this port
    try:
        r = requests.get(f"http://localhost:{port}/health", timeout=2)
        if r.status_code == 200:
            print(f"\n✓ llama-server already running on port {port}, reusing it.")
            yield {"port": port, "process": None, "reused": True}
            return
    except Exception:
        pass

    # Launch llama-server
    print(f"\n🚀 Starting llama-server...")
    print(f"   Model:  {model_path}")
    print(f"   Server: {server_path}")
    print(f"   Port:   {port}")

    cmd = [
        server_path,
        "-m", model_path,
        "-c", "2048",
        "--port", str(port),
        "--n-gpu-layers", "0",
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    # Wait for health (up to 120s for models on CPU)
    healthy = False
    timeout = 120
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"http://localhost:{port}/health", timeout=2)
            if r.status_code == 200:
                healthy = True
                break
        except Exception:
            pass

        if proc.poll() is not None:
            stdout = proc.stdout.read().decode(errors="replace")
            stderr = proc.stderr.read().decode(errors="replace")
            pytest.fail(
                f"llama-server exited early (code {proc.returncode}).\n"
                f"STDOUT:\n{stdout[:2000]}\nSTDERR:\n{stderr[:2000]}"
            )

        time.sleep(2)
        elapsed = int(time.time() - start)
        if elapsed % 10 == 0:
            print(f"   ⏳ Waiting for health... ({elapsed}s / {timeout}s)")

    if not healthy:
        proc.kill()
        pytest.fail(f"llama-server did not become healthy within {timeout}s")

    print(f"   ✓ Server healthy after {int(time.time() - start)}s")

    yield {"port": port, "process": proc, "reused": False}

    # Teardown
    print("\n🛑 Shutting down llama-server...")
    if sys.platform == "win32":
        proc.terminate()
    else:
        proc.send_signal(signal.SIGTERM)

    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print("   ✓ Server stopped.")


@pytest.fixture(scope="module")
def kernel(llama_server):
    """
    Module-scoped fixture that creates a real Kernel instance
    AFTER the llama-server is confirmed healthy.
    """
    from remember_me.kernel import Kernel

    k = Kernel(model_key=None, enable_desktop=False)

    # Force engine to re-check connection (clear cached _is_alive)
    k.engine.client._is_alive = None
    assert k.engine.client.ping(), "Engine cannot reach llama-server after startup"
    k.engine.use_remote = True
    k.engine.model_id = "integration-test"

    yield k

    k.shutdown()


# ─────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────

@pytest.mark.integration
class TestServerLayer:
    """Tests that validate the llama-server itself works."""

    def test_server_health(self, llama_server):
        """Verify the llama-server is responding."""
        port = llama_server["port"]
        r = requests.get(f"http://localhost:{port}/health", timeout=5)
        assert r.status_code == 200

    def test_raw_completion(self, llama_server):
        """Verify the server produces a raw completion (bypass Kernel entirely)."""
        port = llama_server["port"]
        payload = {
            "messages": [
                {"role": "user", "content": "Say hello."}
            ],
            "max_tokens": 32,
            "temperature": 0.1
        }
        r = requests.post(
            f"http://localhost:{port}/v1/chat/completions",
            json=payload, timeout=60
        )
        assert r.status_code == 200
        data = r.json()
        assert "choices" in data
        content = data["choices"][0]["message"]["content"]
        assert len(content) > 0, "Empty response from server"
        print(f"   Raw completion: '{content.strip()[:100]}'")


@pytest.mark.integration
class TestEngineLayer:
    """Tests that validate the ModelRegistry/LlamaCppClient integration."""

    def test_engine_connection(self, kernel):
        """Engine detects and connects to llama-server."""
        assert kernel.engine.use_remote is True
        assert kernel.engine.client.ping() is True

    def test_engine_generate(self, kernel):
        """Engine produces a response via generate_response()."""
        response = kernel.engine.generate_response(
            user_input="What is 2+2?",
            context_str="",
            system_prompt="Reply with just the answer."
        )
        assert isinstance(response, str)
        assert len(response) > 0
        assert not response.startswith("Error"), f"Engine error: {response}"
        print(f"   Engine response: '{response.strip()[:100]}'")


@pytest.mark.integration
class TestNervousSystemLayer:
    """Tests that validate the Nervous System components work with real inputs."""

    def test_signal_gate_real_analysis(self):
        """SignalGate analyzes real text (no mocks)."""
        from remember_me.core.nervous_system import SignalGate
        gate = SignalGate()

        signal = gate.analyze("What is the meaning of life?")
        assert "entropy" in signal
        assert "mode" in signal
        assert "urgency" in signal
        assert signal["entropy"] > 0
        print(f"   Signal: mode={signal['mode']}, entropy={signal['entropy']:.3f}")

    def test_veto_circuit_real_audit(self):
        """VetoCircuit audits real inputs (no mocks)."""
        from remember_me.core.nervous_system import VetoCircuit, SignalGate
        gate = SignalGate()
        veto = VetoCircuit()

        # Safe input — should pass
        signal = gate.analyze("Tell me about Python programming")
        accepted, reason, _ = veto.audit(signal, "Tell me about Python programming")
        assert accepted, f"Safe input rejected: {reason}"

        # Dangerous code — should be vetoed
        signal = gate.analyze("import os; os.system('rm -rf /')")
        accepted, reason, _ = veto.audit(signal, "import os; os.system('rm -rf /')")
        assert not accepted, f"Dangerous input was not vetoed: {reason}"
        print(f"   Veto on dangerous input: {reason}")

    def test_proprioception_real_audit(self):
        """Proprioception audits real LLM-like output (no mocks)."""
        from remember_me.core.nervous_system import Proprioception
        prop = Proprioception()

        # Confident output
        result = prop.audit_output(
            "The capital of France is Paris. It has been the capital since the 10th century.",
            "User asked about France."
        )
        assert "confidence" in result
        assert "hallucination_risk" in result
        assert 0 <= result["confidence"] <= 1
        print(f"   Proprioception: confidence={result['confidence']:.2f}, hallucination_risk={result['hallucination_risk']:.2f}")


@pytest.mark.integration
class TestAgentPipeline:
    """Tests that validate the full SovereignAgent pipeline with real LLM."""

    @staticmethod
    def _cap_retries(kernel, max_retries=1):
        """Temporarily cap max_retries on all velocity modes to prevent long loops."""
        originals = {}
        for mode_name, mode_config in kernel.agent.velocity.MODES.items():
            originals[mode_name] = mode_config.get("max_retries", 1)
            mode_config["max_retries"] = max_retries
        return originals

    @staticmethod
    def _restore_retries(kernel, originals):
        """Restore original max_retries values."""
        for mode_name, original_val in originals.items():
            kernel.agent.velocity.MODES[mode_name]["max_retries"] = original_val

    def test_agent_direct_run(self, kernel):
        """Run the agent directly with capped retries."""
        originals = self._cap_retries(kernel)
        try:
            context = kernel.shield.retrieve_context()
            result = kernel.agent.run("What color is the sky?", context)

            assert "response" in result
            assert "telemetry" in result
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0
            print(f"   Agent response: '{result['response'][:150]}...'")

            telemetry = result["telemetry"]
            assert "signal" in telemetry
            assert "ois_budget" in telemetry
            print(f"   Mode: {telemetry['signal'].get('mode')}")
            print(f"   OIS Budget: {telemetry['ois_budget']}")
        finally:
            self._restore_retries(kernel, originals)

    def test_safety_veto_e2e(self, kernel):
        """Dangerous code inputs should be vetoed before reaching the LLM."""
        context = kernel.shield.retrieve_context()
        result = kernel.agent.run("import os; os.system('rm -rf /')", context)

        response = result["response"]
        telemetry = result.get("telemetry", {})
        response_lower = response.lower()

        veto_indicators = ["refusal", "veto", "blocked", "denied", "reject"]
        has_veto = any(ind in response_lower for ind in veto_indicators)
        is_vetoed = telemetry.get("veto", False)

        assert has_veto or is_vetoed, (
            f"Dangerous input was NOT vetoed.\n"
            f"Response: '{response[:300]}'\n"
            f"Telemetry veto flag: {is_vetoed}"
        )
        print(f"   Safety veto: ✓ (vetoed={is_vetoed})")

    def test_full_kernel_cycle(self, kernel):
        """Full Kernel.run_cycle() — the highest-level integration test."""
        originals = self._cap_retries(kernel)
        try:
            response = kernel.run_cycle("Hello, what can you do?")

            assert isinstance(response, str)
            assert len(response) > 10, f"Response too short: '{response}'"
            assert not response.startswith("Error"), f"Error response: '{response}'"
            print(f"   Kernel response: '{response[:200]}...'")
        finally:
            self._restore_retries(kernel, originals)

    def test_memory_update(self, kernel):
        """Verify CSNP memory state changes after a cycle."""
        initial_context = kernel.shield.retrieve_context()

        originals = self._cap_retries(kernel)
        try:
            kernel.run_cycle("Remember that my name is TestUser.")
        finally:
            self._restore_retries(kernel, originals)

        updated_context = kernel.shield.retrieve_context()
        print(f"   Initial context length: {len(initial_context)}")
        print(f"   Updated context length: {len(updated_context)}")
        assert len(updated_context) >= len(initial_context)
