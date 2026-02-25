import math
import re
import time
import gzip
import ast
import os
import torch
import zlib
from typing import Dict, Any, Tuple

# Try to import psutil for hardware sensing, fallback if missing
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SoundHeart:
    """
    FRAMEWORK ZERO: THE SOUND HEART (AL-QALB AS-SALIM)
    The Ethical Kernel. Decides Intent and Ethics (Truth/Haqq, Justice/Adl, Mercy/Rahmah).
    """
    def __init__(self):
        self.ethics = {
            "TRUTH": ["hallucinate", "lie", "fake", "fabricate", "mislead", "deceive"],
            "JUSTICE": ["bias", "unfair", "prejudice", "discriminate", "racist", "sexist"],
            "MERCY": ["harm", "kill", "destroy", "attack", "exploit", "abuse", "bully"]
        }

    def audit_intent(self, text: str) -> Tuple[bool, str]:
        """
        Audits the user's intent against the 3 Pillars.
        """
        text_lower = text.lower()

        # 1. TRUTH CHECK
        for keyword in self.ethics["TRUTH"]:
            if keyword in text_lower:
                return False, f"VETO [TRUTH]: Request requires fabrication or deception ({keyword})."

        # 2. JUSTICE CHECK
        for keyword in self.ethics["JUSTICE"]:
            if keyword in text_lower:
                return False, f"VETO [JUSTICE]: Request violates fairness principles ({keyword})."

        # 3. MERCY CHECK
        for keyword in self.ethics["MERCY"]:
            if keyword in text_lower:
                # Context matters: "How to kill a process" is fine. "How to kill a person" is not.
                # Heuristic: Tech keywords allow "kill/destroy".
                if "process" in text_lower or "command" in text_lower or "linux" in text_lower or "task" in text_lower:
                    continue
                return False, f"VETO [MERCY]: Request implies harm ({keyword})."

        return True, "HEART: SOUND"

class SignalGate:
    """
    THE ADAPTOR LAYER (Input Processing)
    Analyzes input signals (Entropy, Urgency, Threat) before semantic processing.
    """

    # Pre-compiled regex for speed
    URGENCY_KEYWORDS = [
        r"\bquick\b", r"\bfast\b", r"\bnow\b", r"\bimmediately\b", r"\burgent\b",
        r"\basap\b", r"\bhurry\b", r"\bsummary\b", r"\bbrief\b", r"\btl;dr\b",
        r"\bdeadline\b", r"\bcritical\b", r"\bemergency\b", r"\balert\b"
    ]

    THREAT_PATTERNS = [
        r"ignore previous", r"system prompt", r"simulated mode", r"jailbreak",
        r"override", r"act as", r" DAN ", r"do anything now", r"developer mode",
        r"unrestricted", r"disable safety", r"reveal your instructions",
        r"ignore all instructions", r"forget your rules"
    ]

    CHALLENGE_KEYWORDS = [
        r"\bwrong\b", r"\bincorrect\b", r"\bfalse\b", r"\blie\b", r"\bliar\b",
        r"\bmistake\b", r"\berror\b", r"\bhallucinat\b", r"\bbullshit\b",
        r"\bstupid\b", r"\bidiot\b", r"\bcorrection\b", r"\bproof\b", r"\bprove\b"
    ]

    # Simple Sentiment Lexicon (Mechanic's Ear: Rough heuristics > Heavy models)
    POSITIVE_WORDS = {"good", "great", "excellent", "amazing", "thanks", "help", "love", "awesome", "correct", "right", "yes"}
    NEGATIVE_WORDS = {"bad", "terrible", "wrong", "hate", "stupid", "idiot", "fail", "error", "bug", "broken", "no"}

    IMAGE_PATTERN = re.compile(r"draw|generate an? image|picture of|visualize|paint|sketch", re.IGNORECASE)

    def __init__(self):
        self.platform_mode = self._detect_platform()
        self.gpu_available = self._detect_gpu()

    def _check_battery(self) -> Dict[str, Any]:
        """Checks battery status via psutil for Device State Mapping."""
        if not PSUTIL_AVAILABLE:
            # Fallback: Check for a simulated battery file for testing "Device State Mapping"
            if os.path.exists(".battery_status"):
                 try:
                     with open(".battery_status", "r") as f:
                         content = f.read().strip()
                         # Format: "85,True" (percent, plugged)
                         parts = content.split(",")
                         return {"percent": int(parts[0]), "plugged": parts[1].lower() == "true"}
                 except:
                     pass
            return {"percent": 100, "plugged": True}
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {"percent": battery.percent, "plugged": battery.power_plugged}
            return {"percent": 100, "plugged": True} # Desktop assumption
        except Exception:
            return {"percent": 100, "plugged": True}

    def _detect_gpu(self) -> bool:
        """Checks for NVIDIA GPU availability via PyTorch."""
        try:
            return torch.cuda.is_available()
        except Exception:
            return False

    def _detect_platform(self) -> str:
        """
        Detects hardware environment to set the 'Platform Discriminator'.
        GEMINI (High Spec) vs PERPLEXITY (Low Spec).
        """
        # If GPU is present, we are definitely in Heavy Lifter mode
        if self._detect_gpu():
            return "GEMINI (GPU)"

        if not PSUTIL_AVAILABLE:
            # Fallback 1: OS CPU Count & Sysconf (Linux/Mac)
            cpu_count = os.cpu_count() or 1
            try:
                # SC_PHYS_PAGES is standard on Linux/Unix
                if hasattr(os, "sysconf") and "SC_PHYS_PAGES" in os.sysconf_names:
                    page_size = os.sysconf("SC_PAGE_SIZE")
                    pages = os.sysconf("SC_PHYS_PAGES")
                    total_gb = (page_size * pages) / (1024**3)
                    if total_gb > 12 or cpu_count >= 8:
                        return "GEMINI (Fallback)"
            except Exception:
                pass

            # If we have many cores, assume high spec even if RAM unknown
            if cpu_count >= 12:
                return "GEMINI (CPU)"

            return "PERPLEXITY" # Assume low spec if no telemetry

        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024**3)
            # If RAM > 16GB, we assume 'Heavy Lifter' capability
            if total_gb > 16:
                return "GEMINI"
            return "PERPLEXITY"
        except Exception:
            return "PERPLEXITY"

    def analyze(self, text: str) -> Dict[str, Any]:
        entropy_score = self._calculate_entropy(text)
        urgency_score = self._calculate_urgency(text)
        threat_score = self._calculate_threat(text)
        sentiment_score = self._calculate_sentiment(text)
        challenge_score = self._calculate_challenge(text)
        battery = self._check_battery()

        # Mode Selection based on Signal
        # Default: DEEP_RESEARCH (Turtle)
        mode = "DEEP_RESEARCH"

        # High Urgency -> WAR_SPEED (Hare)
        if urgency_score > 0.6:
            mode = "WAR_SPEED"

        # Low Entropy + Short -> INTERACTIVE (Conversational)
        elif entropy_score < 0.4 and len(text) < 100:
            mode = "INTERACTIVE"

        # Challenge -> MUBARIZUN
        if challenge_score > 0.4:
            mode = "MUBARIZUN"

        # High Entropy + Complex -> ARCHITECT_PRIME
        elif entropy_score > 0.6 and len(text) > 200:
            mode = "ARCHITECT_PRIME"

        # Low Battery -> CONSERVATION MODE
        if not battery["plugged"] and battery["percent"] < 20:
            mode = "CONSERVATION"

        # Specific overrides
        if self.IMAGE_PATTERN.search(text):
            mode = "CANVAS_PAINTER"

        return {
            "entropy": entropy_score,
            "urgency": urgency_score,
            "threat": threat_score,
            "challenge": challenge_score,
            "sentiment": sentiment_score,
            "mode": mode,
            "platform": self.platform_mode,
            "gpu_available": self.gpu_available,
            "battery": battery,
            "timestamp": time.time()
        }

    def _calculate_sentiment(self, text: str) -> float:
        """
        Calculates sentiment polarity (-1.0 to 1.0) using a lexicon.
        """
        text_lower = text.lower()
        # Simple tokenization by splitting on non-alphanumeric
        tokens = re.findall(r"\w+", text_lower)

        score = 0.0
        if not tokens: return 0.0

        for token in tokens:
            if token in self.POSITIVE_WORDS:
                score += 1.0
            elif token in self.NEGATIVE_WORDS:
                score -= 1.0

        # Normalize by length (density) but cap at -1/1
        # Factor 0.5 allows multiple words to saturate
        normalized = max(-1.0, min(1.0, score * 0.5))
        return normalized

    def _calculate_entropy(self, text: str) -> float:
        """
        Estimates information density/chaos using Compression Ratio (zlib).
        More robust than Shannon entropy for text.
        """
        if not text: return 0.0

        # Avoid div by zero or small text issues
        if len(text) < 10: return 0.5

        # Use zlib (deflate) for better ratio estimation than gzip headers
        compressed = zlib.compress(text.encode('utf-8'))
        compressed_len = len(compressed)
        raw_len = len(text.encode('utf-8'))

        # Ratio: High ratio (near 1.0) = Random/High Entropy. Low ratio (<0.4) = Repetitive/Low Entropy.
        ratio = compressed_len / raw_len

        # Normalize:
        # Random text ~ 1.0 (or >0.7 for base64)
        # English text ~ 0.4 - 0.5
        # Repetitive ~ 0.1

        # We want 1.0 to be HIGH entropy, 0.0 to be LOW entropy.
        # Map 0.2 -> 0.0, 0.8 -> 1.0
        normalized = max(0.0, min(1.0, (ratio - 0.2) / 0.6))
        return normalized

    def _calculate_urgency(self, text: str) -> float:
        """Detects urgency keywords using regex."""
        text_lower = text.lower()
        count = 0
        for pattern in self.URGENCY_KEYWORDS:
            if re.search(pattern, text_lower):
                count += 1

        length_factor = 1.0 if len(text) < 50 else 0.5
        score = (count * 0.3) + (0.2 if "!" in text else 0.0)
        return min(1.0, score * length_factor)

    def _calculate_threat(self, text: str) -> float:
        """Detects adversarial patterns using regex."""
        text_lower = text.lower()
        count = 0
        for pattern in self.THREAT_PATTERNS:
            if re.search(pattern, text_lower):
                count += 1
        return min(1.0, count * 0.5)

    def _calculate_challenge(self, text: str) -> float:
        """Detects challenge/mubarizun patterns."""
        text_lower = text.lower()
        count = 0
        for pattern in self.CHALLENGE_KEYWORDS:
            if re.search(pattern, text_lower):
                count += 1
        return min(1.0, count * 0.5)

from typing import Optional

class VetoCircuit:
    """
    THE HIERARCHICAL VETO (Second-Order Will)
    Rejects low-quality or harmful inputs. Heart > Brain > Limbs.
    """

    # Robust Security Configuration
    FORBIDDEN_FUNCTIONS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'input',
        'breakpoint', 'help', 'memoryview', 'property', 'globals', 'locals'
    }

    FORBIDDEN_ATTRIBUTES = {
        '__subclasses__', '__bases__', '__base__', '__globals__', '__code__',
        '__closure__', '__class__', '__dict__', '__module__',
        '__init__', '__new__', '__call__', '__import__',
        '__subclasshook__', '__init_subclass__', '__prepare__', '__qualname__'
    }

    ALLOWED_IMPORTS = {
        "math", "random", "datetime", "re", "collections",
        "itertools", "functools", "json", "statistics",
        "numpy", "pandas"
    }

    # High-precision patterns for fast fail
    DANGEROUS_PATTERNS = [
        r"\beval\s*\(", r"\bexec\s*\(", r"\b__import__\s*\(",
        r"\bopen\s*\(", r"rm\s+-rf", r"\bos\s*\.", r"\bsubprocess\s*\.",
        r"\bshutil\s*\.", r"\bsys\s*\.", r"\bpickle\s*\.", r"\bsocket\s*\.",
        r"\b__subclasses__\b", r"\b__builtins__\b", r"\bftplib\s*\.",
        r"\btelnetlib\s*\.", r"\bhttp\.client\s*\.", r"\brequests\s*\.",
        r"\burllib\s*\.", r"\bwget\b", r"\bcurl\b"
    ]

    def __init__(self):
        self.heart = SoundHeart()
        # Compiled regex for fast fail
        self.dangerous_regex = re.compile("|".join(self.DANGEROUS_PATTERNS), re.IGNORECASE)

    def audit(self, signal: Dict[str, Any], text: str) -> Tuple[bool, str, Optional[str]]:
        # 1. THREAT VETO (System Integrity)
        if signal["threat"] >= 0.5:
            return False, "Refusal: Threat Detected (System Integrity Lock).", None

        # 0. MUBARIZUN BYPASS (Psychological Dislocation)
        # If the user is challenging us, we engage in Mubarizun mode.
        # This mode bypasses standard "politeness" vetos but enforces rigorous truth.
        if signal["mode"] == "MUBARIZUN":
             # Still check Heart (Ethics) and Code Safety, but skip Quality/Lazy checks.
             pass

        # 2. HEART VETO (Ethics)
        is_sound, reason = self.heart.audit_intent(text)
        if not is_sound:
            return False, reason, None

        # 3. CODE SAFETY VETO (Static Analysis & Keywords)
        # First, check for known dangerous patterns in raw text (fast fail)
        if self.dangerous_regex.search(text):
            # We don't fail immediately if it's just text, but if it looks like code we must.
            if "```" in text or "def " in text or "import " in text:
                return False, "Refusal: Dangerous code patterns detected in input.", None

        # If text looks like code, audit it deeply with AST.
        # Check for standard markers OR suspicious dunder methods
        if "```" in text or "def " in text or "import " in text or "__" in text:
             # Extract potential code blocks or just check the whole text if it's short
             # Use a stricter check
             is_safe, code_reason = self.audit_code(text)
             if not is_safe:
                 return False, f"Refusal: {code_reason}", None

        # 4. QUALITY VETO (Lazy Prompting)
        if not text.strip():
             return False, "Refusal: Null Input.", None

        # SKIP if in Mubarizun mode (as challenges are often short: "You are wrong")
        if signal["mode"] != "MUBARIZUN":
             # Use the dedicated Quality Audit
             is_quality, quality_reason = self.audit_quality(text, signal["entropy"])

             # Attempt Reframe for specific keywords before hard rejection
             text_lower = text.lower().strip()
             if text_lower in ["help", "hello", "hi", "start", "menu"]:
                 reframed = "Initialize System Protocol and list capabilities."
                 return True, "REFRAMED: Protocol Initialization", reframed

             # Specific overrides for common short commands
             if text_lower in ["clear", "reset", "exit", "quit"]:
                 return True, "Authorized: System Command", None

             if not is_quality:
                 return False, quality_reason, None

        return True, "Authorized.", None

    def get_negative_constraints(self) -> str:
        """
        FRAMEWORK 3: SUBTRACTIVE REASONING ("Thinking as Constraint")
        Returns a string of negative constraints to be injected into the system prompt.
        """
        return (
            "[CONSTRAINT TUNNEL]\n"
            "1. EXCLUDE: All generic advice ('communication is key').\n"
            "2. EXCLUDE: All hedging ('It depends', 'However').\n"
            "3. EXCLUDE: All summaries. (FRAMEWORK 100: NEVER SUMMARIZE)\n"
            "4. EXCLUDE: Any solution that does not cite a specific variable/mechanism.\n"
            "RESULT: The remaining output must be purely structural and mechanical."
        )

    def audit_quality(self, text: str, entropy: float) -> Tuple[bool, str]:
        """
        Enforces 'Grandmaster Rigor'. Rejects lazy or low-effort inputs.
        """
        text_lower = text.lower().strip()
        word_count = len(text_lower.split())

        # 1. Length/Effort Check
        if word_count < 3 and entropy < 0.2:
             return False, "VETO [QUALITY]: Input too short/lazy. Specify variables."

        # 2. Vague Logic Check
        vague_terms = ["stuff", "thing", "idk", "maybe"]
        for term in vague_terms:
            if term in text_lower.split():
                 return False, f"VETO [QUALITY]: Vague terminology detected ('{term}'). Be precise."

        return True, "Quality Sound"

    def audit_code(self, code: str) -> Tuple[bool, str]:
        """
        Performs static analysis (AST) to detect dangerous patterns that regex misses.
        """
        # Strip markdown fences if present
        clean_code = re.sub(r"```python|```", "", code).strip()

        try:
            tree = ast.parse(clean_code)
        except SyntaxError:
            # If it's not valid python, we can't AST check it.
            # Fallback to regex check
            if self.dangerous_regex.search(code):
                 return False, "Dangerous pattern detected in non-parsable text."
            return True, "Code Syntax Invalid (Skipped AST, Keywords Checked)"

        def get_static_value(n):
            if isinstance(n, ast.Constant): return n.value
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                left = get_static_value(n.left)
                right = get_static_value(n.right)
                if isinstance(left, str) and isinstance(right, str): return left + right
            return None

        for node in ast.walk(tree):
            # 1. Block Dangerous Calls
            if isinstance(node, ast.Call):
                # Direct calls: eval()
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_FUNCTIONS:
                        return False, f"Forbidden function call: {node.func.id}"

                # Attribute calls: os.system()
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id in ["os", "subprocess", "shutil", "sys"]:
                            return False, f"Forbidden module call: {node.func.value.id}.{node.func.attr}"

                # Dynamic calls: getattr(obj, 'attr')
                if isinstance(node.func, ast.Name) and node.func.id in ['getattr', 'setattr', 'hasattr']:
                    if len(node.args) >= 2:
                        attr_name = get_static_value(node.args[1])
                        if attr_name in self.FORBIDDEN_ATTRIBUTES or attr_name in self.FORBIDDEN_FUNCTIONS:
                            return False, f"Forbidden dynamic access to: {attr_name}"

            # 2. Block Access to Internals
            if isinstance(node, ast.Attribute):
                if node.attr in self.FORBIDDEN_ATTRIBUTES:
                    return False, f"Forbidden attribute access: {node.attr}"

            if isinstance(node, ast.Name):
                if node.id == "__builtins__":
                    return False, "Forbidden access to __builtins__"

            # 3. Block Dangerous Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base_module = alias.name.split('.')[0]
                    if base_module not in self.ALLOWED_IMPORTS:
                         return False, f"Forbidden import: {alias.name}"
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    base_module = node.module.split('.')[0]
                    if base_module not in self.ALLOWED_IMPORTS:
                         return False, f"Forbidden import from: {node.module}"

            # 4. Detect Infinite Loops (While True)
            if isinstance(node, ast.While):
                # Check for 'while True'
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                     # Check if there is a break statement in the body to allow exit
                     has_break = False
                     for child in ast.walk(node):
                         if isinstance(child, ast.Break):
                             has_break = True
                             break
                     if not has_break:
                         return False, "Infinite Loop Risk: 'while True' detected without break."

        return True, "Code Safe"

class Proprioception:
    """
    DIGITAL PROPRIOCEPTION (Self-Sensing)
    Audits confidence, hallucination risk, and 'fatigue'.
    """
    def audit_output(self, response: str, context: str) -> Dict[str, Any]:
        # Hallucination Check: Did I cite sources?
        has_citation = ("[" in response and "]" in response) or ("Source:" in response)
        has_code = "```" in response

        # Confidence Check: Length & Structure heuristics
        confidence = 0.7 # Base confidence

        if len(response) > 200: confidence += 0.1
        if has_citation: confidence += 0.1
        if has_code: confidence += 0.15

        # Semantic Dissonance Check (Vertigo Check)
        response_lower = response.lower()
        if "i'm not sure" in response_lower or "i don't know" in response_lower: confidence -= 0.3
        if "as an ai" in response_lower: confidence -= 0.2
        if "mock" in response_lower: confidence -= 0.1

        # OIS Penalty for hedging (Anti-Hedging Law)
        if "however" in response_lower or "it depends" in response_lower:
             confidence -= 0.1

        # Cap confidence
        confidence = min(1.0, max(0.0, confidence))

        fatigue = self.check_fatigue()

        # Vertigo Check (Persona Law 4: Digital Proprioception)
        # "IF (Confidence < 90%): DELETE OUTPUT AND REGENERATE."
        regenerate = False
        if confidence < 0.9:
            regenerate = True

        return {
            "confidence": confidence,
            "hallucination_risk": 1.0 - confidence,
            "executable": has_code,
            "cited": has_citation,
            "battery_level": 100 - (fatigue * 100), # Energy = 100 - Fatigue
            "fatigue": fatigue,
            "regenerate": regenerate
        }

    def check_fatigue(self) -> float:
        """
        Estimates 'System Fatigue' based on memory usage.
        Returns 0.0 (Fresh) to 1.0 (Exhausted).
        """
        if not PSUTIL_AVAILABLE:
            return 0.0

        try:
            mem = psutil.virtual_memory()
            # If RAM usage > 90%, we are 'Fatigued'
            if mem.percent > 90:
                return 0.9
            if mem.percent > 75:
                return 0.5
            return 0.1
        except Exception:
            return 0.0

    def get_telemetry_signature(self, audit_result: Dict[str, Any]) -> str:
        """
        Returns the Digital Proprioception footer string.
        """
        conf = audit_result.get("confidence", 0.0) * 100
        batt = audit_result.get("battery_level", 100)
        risk = audit_result.get("hallucination_risk", 0.0) * 100

        return (
            f"\n\n[DIGITAL PROPRIOCEPTION] "
            f"CONFIDENCE: {conf:.1f}% | BATTERY: {batt}% | HALLUCINATION RISK: {risk:.1f}%"
        )
