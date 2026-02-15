import math
import re
import time
from typing import Dict, Any, Tuple

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
        elif entropy_score < 0.6 and len(text) < 100:
            mode = "INTERACTIVE"

        # Specific overrides
        if "generate image" in text.lower() or "draw" in text.lower():
            mode = "CANVAS_PAINTER"

        return {
            "entropy": entropy_score,
            "urgency": urgency_score,
            "threat": threat_score,
            "mode": mode,
            "timestamp": time.time()
        }

    def _calculate_entropy(self, text: str) -> float:
        """Estimates information density/chaos (Shannon Entropy)."""
        if not text: return 0.0

        length = len(text)
        counts = {}
        for char in text:
            counts[char] = counts.get(char, 0) + 1

        entropy = 0.0
        for count in counts.values():
            p = count / length
            entropy -= p * math.log(p, 2)

        # Normalize: English text ~4.5 bits/char. Random ~6-7 bits.
        return min(1.0, entropy / 6.0)

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

    def audit(self, signal: Dict[str, Any], text: str) -> Tuple[bool, str]:
        # 1. THREAT VETO (System Integrity)
        if signal["threat"] >= 0.5:
            return False, "Refusal: Threat Detected (System Integrity Lock)."

        # 2. HEART VETO (Ethics)
        is_sound, reason = self.heart.audit_intent(text)
        if not is_sound:
            return False, reason

        # 3. DANGEROUS CODE VETO (Anti-Sabotage)
        # Check for code execution patterns that bypass the sandbox or are malicious
        dangerous_patterns = ["os.system", "subprocess", "rm -rf", "eval(", "exec(", "open(", "write("]
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                # We block these to prevent the LLM from generating code that will inevitably fail
                # or is unsafe, even if the user is just asking about it.
                # This aligns with "Sound Heart" -> "Do not harm".
                return False, f"Refusal: Dangerous Code Pattern Detected ({pattern})."

        # 4. QUALITY VETO (Lazy Prompting)
        if not text.strip():
             return False, "Refusal: Null Input."

        # Reject "Lazy" inputs.
        # If user provides very low entropy input, we reject and ask for specificity.
        # "Hi." entropy is ~0.49. "help" ~0.33. "aaaa" ~0.
        if signal["entropy"] < 0.25 and len(text) < 20:
             return False, "Refusal: Input insufficient (Low Entropy). Please elaborate."

        return True, "Authorized."

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

        return {
            "confidence": confidence,
            "hallucination_risk": 1.0 - confidence,
            "executable": has_code,
            "cited": has_citation,
            "battery_level": 100 # Simulated 'Energy' (could be token limit based)
        }
