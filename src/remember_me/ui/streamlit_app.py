import streamlit as st
import time
import os
import sys

# Try to import psutil for hardware sensing, fallback if missing
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add src to path for absolute imports (remember_me package resolution)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

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
    .css-1aumxhk {
        background-color: #0e1117;
        color: #00ff41;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION (Singleton) ---
@st.cache_resource
def get_kernel():
    """Initializes the Sovereign Stack once."""
    print("⚡ KERNEL: Booting...")
    # Initialize Engine (Auto-detects llama-server or falls back to transformers)
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
        "signal": {"mode": "IDLE", "entropy": 0.0, "urgency": 0.0, "threat": 0.0, "platform": "UNKNOWN"},
        "audit": {"confidence": 0.0, "hallucination_risk": 0.0},
        "ois_budget": 100,
        "s_lang_trace": ""
    }

# --- SIDEBAR: NEURAL MONITORING ---
with st.sidebar:
    st.title("🧠 NEURAL STATUS")

    # 0. System Health (Physical Grounding)
    st.caption("PHYSICAL SUBSTRATE")

    # GPU Status (from Telemetry)
    gpu_ok = st.session_state.telemetry.get("signal", {}).get("gpu_available", False)
    gpu_status = "ONLINE" if gpu_ok else "OFFLINE"
    gpu_color = "green" if gpu_ok else "red"
    st.markdown(f"**GPU ACCELERATION:** :{gpu_color}[{gpu_status}]")

    if PSUTIL_AVAILABLE:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        c1, c2 = st.columns(2)
        c1.metric("CPU", f"{cpu}%")
        c2.metric("RAM", f"{ram}%")
    else:
        st.warning("Telemetry Offline (psutil missing)")

    st.markdown("---")

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

    # Virtual Nervous System
    st.markdown("### Virtual Nervous System")

    # Signal Mode & Urgency
    sig = st.session_state.telemetry.get("signal", {})
    mode = sig.get("mode", "IDLE")
    platform = sig.get("platform", "UNKNOWN")
    st.info(f"MODE: {mode} [{platform}]")

    # Power Telemetry (Device State Mapping)
    if "battery" in sig:
        bat = sig["battery"]
        plug_icon = "🔌" if bat['plugged'] else "🔋"
        st.caption(f"POWER: {plug_icon} {bat['percent']}%")

    c1, c2, c3 = st.columns(3)
    c1.metric("Entropy", f"{sig.get('entropy', 0.0):.2f}")
    c2.metric("Urgency", f"{sig.get('urgency', 0.0):.2f}")
    c3.metric("Threat", f"{sig.get('threat', 0.0):.2f}")

    st.caption("SIGNAL VECTOR")
    st.progress(min(1.0, sig.get('entropy', 0.0)), text="Entropy (Chaos)")
    st.progress(min(1.0, sig.get('urgency', 0.0)), text="Urgency (Velocity)")
    st.progress(min(1.0, sig.get('threat', 0.0)), text="Threat (Risk)")

    # OIS Budget
    ois = st.session_state.telemetry.get("ois_budget", 100)
    ois_icon = "🟢" if ois > 70 else "🟡" if ois > 30 else "🔴"
    st.progress(min(1.0, max(0.0, ois / 100.0)), text=f"OIS Truth Budget: {ois}/100 {ois_icon}")

    # Fatigue
    fatigue = st.session_state.telemetry.get("audit", {}).get("fatigue", 0.0)
    st.metric("System Fatigue", f"{fatigue*100:.0f}%", delta=f"-{fatigue*100:.0f}%" if fatigue > 0.5 else "Stable", delta_color="inverse")

    # Heart Status (Inferred from Veto)
    heart_status = "SOUND"
    heart_color = "green"
    if st.session_state.telemetry.get("veto", False):
        heart_status = "VETO ACTIVE"
        heart_color = "red"

    st.markdown(f"**HEART STATUS:** :{heart_color}[{heart_status}]")

    st.markdown("---")

    st.caption("S-LANG TERMINAL")
    trace = st.session_state.telemetry.get("s_lang_trace", "IDLE")
    st.code(trace, language="bash")

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

    if st.button("🔄 Reset Python Sandbox"):
        kernel["agent"].sandbox.reset()
        st.toast("Sandbox Reset.", icon="🔄")

    st.markdown("---")
    show_slang = st.checkbox("Show S-Lang Trace", value=True, help="Visualize the Agent's internal reasoning process.")

# --- MAIN: COGNITIVE MATRIX ---
st.title("REMEMBER ME // COGNITIVE MATRIX")

tab1, tab2 = st.tabs(["💬 COGNITION", "🧠 MEMORY BANK"])

with tab1:
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
                # Show Internal Monologue (S-Lang)
                s_lang_trace = telemetry.get("s_lang_trace", "")

                if show_slang and s_lang_trace:
                    st.caption("💭 **S-Lang Trace:**")
                    st.code(s_lang_trace, language="bash")

                # Show Microcosm Trajectories
                if "microcosm" in telemetry and telemetry["microcosm"]:
                    with st.expander("🔮 Haiyue Microcosm (Parallel Trajectories)"):
                        mc = telemetry["microcosm"]
                        cols = st.columns(3)
                        with cols[0]:
                            st.info("Optimistic (+1)")
                            st.markdown(mc.get("OPTIMISTIC", "N/A"))
                        with cols[1]:
                            st.warning("Neutral (0)")
                            st.markdown(mc.get("NEUTRAL", "N/A"))
                        with cols[2]:
                            st.error("Pessimistic (-1)")
                            st.markdown(mc.get("PESSIMISTIC", "N/A"))

                # Full Telemetry in Expander
                with st.expander("🔍 Deep Telemetry (JSON)"):
                     st.json(telemetry)

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
                    fatigue = aud.get("fatigue", 0.0)
                    st.caption(f"Confidence: {conf*100:.0f}% | Fatigue: {fatigue*100:.0f}% | OIS Budget: {telemetry.get('ois_budget', 0)}")

                # Save Message
                msg_data = {"role": "assistant", "content": response, "artifacts": result["artifacts"]}
                st.session_state.messages.append(msg_data)

                # 3. Update Memory
                kernel["memory"].update_state(prompt, response)

                # Force Rerun to update Sidebar Metrics
                st.rerun()

with tab2:
    st.header("Active Memory Buffer (CSNP)")
    st.caption("Quantum Dream Memory Architecture - Live State")

    if kernel["memory"].text_buffer:
        for i, (text, h) in enumerate(zip(kernel["memory"].text_buffer, kernel["memory"].hash_buffer)):
            with st.expander(f"Memory #{i} [Hash: {h[:8]}...]"):
                st.text(text)
                st.caption(f"Full Hash: {h}")

        # Integrity Chain Visualization
        st.markdown("---")
        st.subheader("⛓️ Merkle Integrity Chain")
        st.caption("Immutable History Ledger")

        # Access chain via private attributes or public export for visualization
        # We can use the cached chain from memory
        chain_hashes = kernel["memory"].chain.ordered_hashes
        if chain_hashes:
            st.code("\n⬇\n".join([f"[{h[:8]}...]" for h in chain_hashes]), language="text")
        else:
            st.info("Chain Empty.")

    else:
        st.info("Memory Buffer Empty. Engage in conversation to populate.")
