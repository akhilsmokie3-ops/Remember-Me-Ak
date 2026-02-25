# REMEMBER-ME v3.0 — THE SOVEREIGN DESKTOP AI

### Full-Spectrum Desktop Agent: Brain + Body

```ascii
      .       .         .           .      .
   .       .      .   (   )    .     .
      .     ______   (     )      .
  .        |      | (       )  .      .
     .     |  ____|  (     )     .
        .  | |_____   (   )    .    .
    .      |_______|    |    .     
       .      | |       |   .    .
   .          | |       |      .
      ________|_|_______|________ 
     |                           |
     |  SOVEREIGN  ::  SYSTEM    |
     |___________________________|
```

**0% Cloud. 0% Spying. 100% Ownership.**

Remember-Me is a sovereign desktop AI agent that combines a military-grade cognitive kernel (local LLM inference + Quantum Dream Memory) with a full desktop automation layer (voice, clipboard, system control, Telegram). It lives entirely on your machine and answers to **no one but you.**

---

## 🌌 Architecture Overview

| Layer | Component | Description |
| :--- | :--- | :--- |
| 🧠 **Mind** | **Kernel** | Orchestrates Memory + Inference + Agency |
| 💾 **Memory** | **CSNP + QDMA** | Compressed context + vector dream memory |
| ⚡ **Engine** | **ModelRegistry** | Local LLM (Qwen/Llama) with server fallback |
| ⚔️ **Agency** | **SovereignAgent** | 5-phase execution (audit → sim → retrieve → reason → verify) |
| 🛡️ **Nervous** | **VetoCircuit + SignalGate** | Ethics auditing + safety checks |
| 🖥️ **Desktop** | **desktop/**  | System automation, voice, clipboard, Telegram |

---

## 🚀 Installation

**Prerequisites:** Python 3.10+, 8GB RAM, Windows 10/11.

```bash
# Clone
git clone https://github.com/merchantmoh-debug/Remember-Me-AI.git
cd Remember-Me-AI

# Core brain (required)
pip install -r requirements.txt

# Desktop layer (optional - for system automation)
pip install -r requirements-desktop.txt

# Install local model
python install_brain.py
```

---

## 🖥️ Desktop Agent Features

All ported from Zyron-Assistant with security hardening:

| Feature | Module | Security |
| :--- | :--- | :--- |
| System control (sleep/shutdown/restart) | `system_actions.py` | `subprocess.run()` + confirmation required |
| Screenshot / Webcam / Audio recording | `system_actions.py` | Media dir sandboxed |
| Battery / CPU / Storage monitoring | `system_actions.py` | Read-only `psutil` |
| Application launch & kill | `system_actions.py` | **Process whitelist** — rejects unknown exe names |
| Volume / Brightness / Media keys | `system_actions.py` | Validated input ranges |
| Voice I/O + Wake word (Vosk) | `voice.py` | Explicit start/stop lifecycle |
| Clipboard history (bounded) | `clipboard.py` | Max 1000 entries, no auto-start |
| Focus Mode (app blocking) | `focus_mode.py` | Exact process name matching |
| Zombie Reaper (idle process scan) | `zombie_reaper.py` | Returns data, caller decides |
| Activity Monitor (processes + tabs) | `activity.py` | Read-only, temp DB copy |
| Browser Bridge (Firefox IPC) | `browser_bridge.py` | Configurable timeout |
| File Tracker + Smart Search | `files/` | Bounded log (10K entries) |
| **Telegram Bot** | `telegram_bot.py` | **Auth via `user.id`** (not username) |

### Telegram Bot

```bash
# Set environment variables
set REMEMBER_ME_TELEGRAM_TOKEN=your_bot_token
set REMEMBER_ME_TELEGRAM_USER_IDS=123456789

# Launch
python run_telegram.py --model tiny
```

Commands: `/status` `/screenshot` `/battery` `/storage` `/clipboard` `/panic`  
Free-text messages route through the full SovereignAgent pipeline.

---

## 🏗️ Quick Start

### Interactive Mode
```bash
python -m remember_me.kernel --model tiny
```

### Windows
```bash
start_sovereign.bat
```

---

## 🧪 Testing

```bash
pytest tests/ -v
```

33 existing tests + desktop integration tests.

---

## 📜 License

**MIT** — Sovereign code for sovereign minds.

*Signed,*  
**The Sovereign Architect** *(Mohamad Al-Zawahreh)*
