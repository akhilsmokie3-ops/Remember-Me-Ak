import streamlit as st
import time
import os
import torch
from remember_me.core.csnp import CSNPManager
from remember_me.integrations.engine import ModelRegistry
from remember_me.integrations.tools import ToolArsenal
from remember_me.integrations.agent import SovereignAgent

# --- CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="REMEMBER ME: COGNITIVE MATRIX",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cyberpunk / Matrix CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
    }
    .stTextInput > div > div > input {
        background-color: #111;
        color: #00ff41;
        border: 1px solid #00ff41;
    }
    .stChatMessage {
        background-color: #000;
        border: 1px solid #333;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #00ff41;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION (Singleton) ---
@st.cache_resource
def get_kernel():
    """Initializes the Sovereign Stack once."""
    print("⚡ KERNEL: Booting...")
    engine = ModelRegistry()
    memory = CSNPManager(context_limit=15)
    tools = ToolArsenal()
    agent = SovereignAgent(engine, tools)
    return {"engine": engine, "memory": memory, "agent": agent}

kernel = get_kernel()

# Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

if "telemetry" not in st.session_state:
    st.session_state.telemetry = {
        "signal": {"mode": "IDLE", "entropy": 0.0, "urgency": 0.0},
        "audit": {"confidence": 0.0, "hallucination_risk": 0.0}
    }

# --- SIDEBAR: NEURAL MONITORING ---
with st.sidebar:
    st.title("🧠 NEURAL STATUS")

    # 1. Model Selection
    model_keys = list(kernel["engine"].MODELS.keys())
    current_model = st.selectbox(
        "Inference Engine",
        model_keys,
        index=0 if not kernel["engine"].model_id else model_keys.index(kernel["engine"].model_id),
        help="Select the active brain model."
    )

    if st.button("Load Engine"):
        with st.spinner(f"Mounting {current_model}..."):
            success = kernel["engine"].load_model(current_model)
            if success:
                st.success(f"Mounted: {current_model}")
            else:
                st.error("Failed to mount engine.")

    st.markdown("---")

    # 2. Cognitive Metrics (Live)
    col1, col2 = st.columns(2)

    # Memory Integrity (Merkle Root Depth / Norm)
    integrity = kernel["memory"].identity_state.norm().item()
    col1.metric("Integrity", f"{integrity:.4f}", delta="Stable")

    # Context Usage
    usage = len(kernel["memory"].text_buffer)
    limit = kernel["memory"].context_limit
    col2.metric("Memory", f"{usage}/{limit}", help="Active Context Shards")

    # Entropy Gauge
    entropy = st.session_state.telemetry["signal"]["entropy"]
    st.progress(entropy, text=f"Input Entropy: {entropy:.2f}")

    # Signal Mode
    mode = st.session_state.telemetry["signal"]["mode"]
    st.info(f"SIGNAL MODE: {mode}")

    st.markdown("---")

    # 3. Persistence
    if st.button("💾 Save Cognitive State"):
        kernel["memory"].save_state("brain.pt")
        st.toast("Brain saved to disk.", icon="💾")

    if st.button("📂 Load Cognitive State"):
        try:
            kernel["memory"].load_state("brain.pt")
            st.toast("Brain loaded from disk.", icon="📂")
            st.rerun()
        except FileNotFoundError:
            st.error("No brain file found.")

# --- MAIN: COGNITIVE MATRIX ---
st.title("REMEMBER ME // COGNITIVE MATRIX")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "artifacts" in msg:
            for artifact in msg["artifacts"]:
                if artifact["type"] == "image":
                    st.image(artifact["path"], caption="Visual Artifact")
                elif artifact["type"] == "code":
                    with st.expander("Code Execution"):
                        st.code(artifact["content"], language="python")
                        st.text(artifact["result"])

# Input
if prompt := st.chat_input("Command the Sovereign..."):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI Execution
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # 1. Retrieve Context
        context_str = kernel["memory"].retrieve_context()

        # 2. Execute Agent
        with st.spinner("Thinking..."):
            result = kernel["agent"].run(prompt, context_str)

        response = result["response"]
        telemetry = result.get("telemetry", {})

        # Update Session Telemetry
        st.session_state.telemetry = telemetry

        # Veto Handling
        if telemetry.get("veto", False):
            st.error(f"⛔ VETO TRIGGERED: {response}")
            st.session_state.messages.append({"role": "assistant", "content": f"⛔ {response}"})
        else:
            # Show Tool Outputs
            if result["tool_outputs"]:
                with st.expander("🛠️ Tool Outputs"):
                    for output in result["tool_outputs"]:
                        st.text(output)

            # Show Artifacts
            for artifact in result["artifacts"]:
                if artifact["type"] == "image":
                    st.image(artifact["path"], caption="Visual Artifact")
                elif artifact["type"] == "code":
                    with st.expander("💻 Generated Code"):
                        st.code(artifact["content"], language="python")
                        st.text(f"Result: {artifact['result']}")

            # Final Response
            message_placeholder.markdown(response)

            # Audit Footer
            if "audit" in telemetry:
                aud = telemetry["audit"]
                conf = aud.get("confidence", 0.0)
                st.caption(f"Confidence: {conf*100:.0f}% | Risk: {aud.get('hallucination_risk', 0.0):.2f}")

            # Save Message
            msg_data = {"role": "assistant", "content": response, "artifacts": result["artifacts"]}
            st.session_state.messages.append(msg_data)

            # 3. Update Memory
            kernel["memory"].update_state(prompt, response)

            # Force Rerun to update Sidebar Metrics
            st.rerun()
