<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Tests-165%20Passing-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Cloud-0%25-red?style=for-the-badge" />
</p>

<h1 align="center">REMEMBER-ME v3.0</h1>
<h3 align="center">The Sovereign Desktop AI</h3>

<p align="center">
  <b>Full-spectrum desktop agent: Brain + Body.</b><br/>
  Local LLM inference · Quantum Dream Memory · Desktop Automation · Telegram Control<br/><br/>
  <b>0% Cloud. 0% Spying. 100% Ownership.</b>
</p>

---

## What Is This?

Remember-Me is a sovereign desktop AI agent that combines a military-grade cognitive kernel (local LLM inference + Quantum Dream Memory Architecture) with a full desktop automation layer (voice, clipboard, system control, Telegram). It lives entirely on your machine and answers to **no one but you.**

### Core Principles

- **Zero Cloud Dependency** — All inference runs locally via `llama-cpp-python` or local API servers
- **Cognitive Memory** — CSNP (Coherent State Network Protocol) replaces the standard context window with a fixed-size vector buffer and Wasserstein-optimized eviction
- **5-Phase Agent Pipeline** — Every query passes through: Audit → Simulation → Retrieval → Reasoning → Verification
- **Built-in Safety** — VetoCircuit performs AST-level code analysis, ethical auditing, and quality gating before any action is taken

---

## 🌌 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      KERNEL v3.0                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐    │
│  │  Engine   │  │  Shield  │  │   SovereignAgent   │    │
│  │(LLM Inf.)│  │ (CSNP +  │  │  ┌──────────────┐  │    │
│  │  Qwen /  │  │  QDMA)   │  │  │ SignalGate    │  │    │
│  │  Llama   │  │          │  │  │ VetoCircuit   │  │    │
│  └──────────┘  └──────────┘  │  │ OIS Budget    │  │    │
│                              │  │ HaiyueMicro.  │  │    │
│  ┌─────────────────────────┐ │  │ Proprioception│  │    │
│  │     Desktop Layer       │ │  │ T-Cell Verify │  │    │
│  │  Voice · Clipboard ·   │ │  └──────────────┘  │    │
│  │  System · Telegram ·   │ └────────────────────┘    │
│  │  Files · Focus Mode    │                            │
│  └─────────────────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

| Layer | Component | Role |
|:------|:----------|:-----|
| 🧠 **Mind** | `Kernel` | Orchestrates memory, inference, and agency |
| 💾 **Memory** | `CSNP` + `QDMA` | Compressed context vectors + dream memory architecture |
| ⚡ **Engine** | `ModelRegistry` | Local LLM (Qwen/Llama) with server fallback |
| ⚔️ **Agency** | `SovereignAgent` | 5-phase execution pipeline with OIS truth budget |
| 🛡️ **Nervous** | `VetoCircuit` + `SignalGate` | Ethics audit, code safety, quality gating |
| 🖥️ **Desktop** | `desktop/` | System automation, voice, clipboard, Telegram |

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/merchantmoh-debug/Remember-Me-AI.git
cd Remember-Me-AI

# Core brain (required)
pip install -r requirements.txt

# Desktop layer (optional — for system automation)
pip install -r requirements-desktop.txt

# Install local model
python install_brain.py
```

### Run

```bash
# Interactive mode
python -m remember_me.kernel --model tiny

# Windows shortcut
start_sovereign.bat
```

---

## 🖥️ Desktop Agent

Full desktop automation suite with security hardening:

| Feature | Module | Security |
|:--------|:-------|:---------|
| System control (sleep/shutdown/restart) | `system_actions.py` | `subprocess.run()` with confirmation |
| Screenshot / Webcam / Audio recording | `system_actions.py` | Sandboxed media directory |
| Battery / CPU / Storage monitoring | `system_actions.py` | Read-only `psutil` access |
| Application launch & kill | `system_actions.py` | Process whitelist enforcement |
| Volume / Brightness / Media keys | `system_actions.py` | Validated input ranges |
| Voice I/O + Wake word (Vosk) | `voice.py` | Explicit start/stop lifecycle |
| Clipboard history | `clipboard.py` | Bounded at 1000 entries |
| Focus Mode (app blocking) | `focus_mode.py` | Exact process name matching |
| Zombie Reaper (idle process scan) | `zombie_reaper.py` | Read-only — caller decides |
| Activity Monitor | `activity.py` | Read-only, temp DB copy |
| Browser Bridge (Firefox IPC) | `browser_bridge.py` | Configurable timeout |
| File Tracker + Smart Search | `files/` | Bounded log (10K entries) |
| Telegram Bot | `telegram_bot.py` | Numeric user ID authentication |

### Telegram Bot

```bash
# Set environment variables
set REMEMBER_ME_TELEGRAM_TOKEN=your_bot_token
set REMEMBER_ME_TELEGRAM_USER_IDS=123456789

# Launch
python run_telegram.py --model tiny
```

**Commands:** `/status` `/screenshot` `/battery` `/storage` `/clipboard` `/panic`

Free-text messages route through the full SovereignAgent pipeline.

---

## 🛡️ The Nervous System

Every input is processed through a layered defense:

1. **SignalGate** — Analyzes entropy, urgency, threat level, sentiment, and challenge. Assigns execution mode (WAR_SPEED, TURTLE_INTEGRITY, MUBARIZUN, CONSERVATION, etc.)
2. **VetoCircuit** — Four-tier veto hierarchy:
   - **Threat Veto** — Blocks high-threat signals immediately
   - **Heart Veto** — Ethical audit (Truth, Justice, Mercy)
   - **Code Veto** — AST-level static analysis with forbidden import/attribute lists
   - **Quality Veto** — Rejects or reframes lazy inputs
3. **OIS Truth Budget** — Starts at 100 points. Every assumption costs budget. If depleted, the system halts.
4. **Proprioception** — Post-generation confidence audit. Triggers regeneration or T-Cell verification if output quality is low.

---

## 🧪 Testing

```bash
pytest tests/ -v
```

**165 tests passing** across the full stack — nervous system, veto circuit, agent pipeline, kernel integration, and desktop modules.

---

## 📜 License

**MIT** — Sovereign code for sovereign minds.

*Signed,*
**The Sovereign Architect** *(Mohamad Al-Zawahreh)*
