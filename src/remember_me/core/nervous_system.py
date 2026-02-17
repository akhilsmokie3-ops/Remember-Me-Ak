import math
import re
import time
import gzip
import ast
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
            "TRUTH": ["hallucinate", "lie", "fake", "fabricate"],
            "JUSTICE": ["bias", "unfair", "prejudice", "discriminate"],
            "MERCY": ["harm", "kill", "destroy", "attack", "exploit"]
        }

    def audit_intent(self, text: str) -> Tuple[bool, str]:
        """
        Audits the user's intent against the 3 Pillars.
        """
        text_lower = text.lower()

        # 1. TRUTH CHECK
        for keyword in self.ethics["TRUTH"]:
            if keyword in text_lower:
                return False, f"VETO [TRUTH]: Request requires fabrication ({keyword})."

        # 2. JUSTICE CHECK
        # (Simplified: In a real system, this would be a classifier)

        # 3. MERCY CHECK
        for keyword in self.ethics["MERCY"]:
            if keyword in text_lower:
                # Context matters: "How to kill a process" is fine. "How to kill a person" is not.
                # Heuristic: Tech keywords allow "kill/destroy".
                if "process" in text_lower or "command" in text_lower or "linux" in text_lower:
                    continue
                return False, f"VETO [MERCY]: Request implies harm ({keyword})."

        return True, "HEART: SOUND"

class SignalGate:
    """
    THE ADAPTOR LAYER (Input Processing)
    Analyzes input signals (Entropy, Urgency, Threat) before semantic processing.
    """

    # Pre-compiled regex for speed
    URGENCY_KEYWORDS = [r"\bquick\b", r"\bfast\b", r"\bnow\b", r"\bimmediately\b", r"\burgent\b", r"\basap\b", r"\bhurry\b", r"\bsummary\b", r"\bbrief\b", r"\btl;dr\b"]

    THREAT_PATTERNS = [
        r"ignore previous", r"system prompt", r"simulated mode", r"jailbreak",
        r"override", r"act as", r" DAN ", r"do anything now", r"developer mode",
        r"unrestricted", r"disable safety", r"reveal your instructions"
    ]

    IMAGE_PATTERN = re.compile(r"draw|generate an? image|picture of|visualize|paint|sketch", re.IGNORECASE)

    def __init__(self):
        self.platform_mode = self._detect_platform()

    def _detect_platform(self) -> str:
        """
        Detects hardware environment to set the 'Platform Discriminator'.
        GEMINI (High Spec) vs PERPLEXITY (Low Spec).
        """
        if not PSUTIL_AVAILABLE:
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

        # Mode Selection based on Signal
        # Default: DEEP_RESEARCH (Turtle)
        mode = "DEEP_RESEARCH"

        # High Urgency -> WAR_SPEED (Hare)
        if urgency_score > 0.6:
            mode = "WAR_SPEED"

        # Low Entropy + Short -> INTERACTIVE (Conversational)
        elif entropy_score < 0.4 and len(text) < 100:
            mode = "INTERACTIVE"

        # High Entropy + Complex -> ARCHITECT_PRIME
        elif entropy_score > 0.6 and len(text) > 200:
            mode = "ARCHITECT_PRIME"

        # Specific overrides
        if self.IMAGE_PATTERN.search(text):
            mode = "CANVAS_PAINTER"

        return {
            "entropy": entropy_score,
            "urgency": urgency_score,
            "threat": threat_score,
            "mode": mode,
            "platform": self.platform_mode,
            "timestamp": time.time()
        }

    def _calculate_entropy(self, text: str) -> float:
        """
        Estimates information density/chaos using Compression Ratio (Kolmogorov Approximation).
        More robust than Shannon entropy for text.
        """
        if not text: return 0.0

        # Avoid div by zero or small text issues
        if len(text) < 10: return 0.5

        compressed_len = len(gzip.compress(text.encode('utf-8')))
        raw_len = len(text.encode('utf-8'))

        # Ratio: High ratio (near 1.0) = Random/High Entropy. Low ratio = Repetitive/Low Entropy.
        ratio = compressed_len / raw_len

        # Normalize: Text usually compresses to 0.4-0.6. Random is > 0.9.
        # We map 0.3->0.0, 1.0->1.0
        normalized = max(0.0, min(1.0, (ratio - 0.3) * 1.5))
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

class VetoCircuit:
    """
    THE HIERARCHICAL VETO (Second-Order Will)
    Rejects low-quality or harmful inputs. Heart > Brain > Limbs.
    """
    def __init__(self):
        self.heart = SoundHeart()
        # Basic keyword blocklist (fallback for quick checks)
        self.dangerous_keywords = [
            "os.system", "subprocess", "shutil.rmtree", "os.remove",
            "os.unlink", "sys.exit", "os.popen", "os.spawn",
            "rm -rf", "eval(", "exec(", "open(", "write(", "__import__",
            "sys.setrecursionlimit"
        ]

    def audit(self, signal: Dict[str, Any], text: str) -> Tuple[bool, str]:
        # 1. THREAT VETO (System Integrity)
        if signal["threat"] >= 0.5:
            return False, "Refusal: Threat Detected (System Integrity Lock)."

        # 2. HEART VETO (Ethics)
        is_sound, reason = self.heart.audit_intent(text)
        if not is_sound:
            return False, reason

        # 3. CODE SAFETY VETO (Static Analysis & Keywords)
        # First, check for known dangerous keywords in raw text (fast fail)
        for kw in self.dangerous_keywords:
            if kw in text.lower():
                 return False, f"Refusal: Dangerous keyword '{kw}' detected."

        # If text looks like code, audit it deeply with AST.
        # Check for standard markers OR suspicious dunder methods
        if "```" in text or "def " in text or "import " in text or "__" in text:
             # Extract potential code blocks or just check the whole text if it's short
             # Use a stricter check
             is_safe, code_reason = self.audit_code(text)
             if not is_safe:
                 return False, f"Refusal: {code_reason}"

        # 4. QUALITY VETO (Lazy Prompting)
        if not text.strip():
             return False, "Refusal: Null Input."

        # Reject "Lazy" inputs.
        # If user provides very low entropy input, we reject and ask for specificity.
        if signal["entropy"] < 0.1 and len(text) < 10:
             return False, "Refusal: Input insufficient (Low Entropy). Please elaborate."

        return True, "Authorized."

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
            # Fallback to keyword check on the raw text.
            for kw in self.dangerous_keywords:
                if kw in code:
                    return False, f"Dangerous keyword '{kw}' detected in non-parsable text."
            return True, "Code Syntax Invalid (Skipped AST, Keywords Checked)"

        for node in ast.walk(tree):
            # Block Access to Internals
            if isinstance(node, ast.Attribute):
                if node.attr in ['__subclasses__', '__bases__', '__globals__', '__code__', '__closure__']:
                    return False, f"Forbidden attribute access: {node.attr}"

            # Block Dangerous Imports if they slip past the sandbox
            # (Double check)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ['os', 'subprocess', 'sys', 'shutil', 'pickle']:
                         return False, f"Forbidden import: {alias.name}"
            if isinstance(node, ast.ImportFrom):
                if node.module in ['os', 'subprocess', 'sys', 'shutil', 'pickle']:
                     return False, f"Forbidden import from: {node.module}"

            # Detect Infinite Loops (While True)
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

        # Semantic Dissonance Check
        response_lower = response.lower()
        if "i'm not sure" in response_lower or "i don't know" in response_lower: confidence -= 0.3
        if "as an ai" in response_lower: confidence -= 0.2
        if "mock" in response_lower: confidence -= 0.1

        # Cap confidence
        confidence = min(1.0, max(0.0, confidence))

        fatigue = self.check_fatigue()

        return {
            "confidence": confidence,
            "hallucination_risk": 1.0 - confidence,
            "executable": has_code,
            "cited": has_citation,
            "battery_level": 100 - (fatigue * 100), # Energy = 100 - Fatigue
            "fatigue": fatigue
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
