import math
import re
from typing import Dict, Any, Tuple

class SignalGate:
    """
    The Adaptor Layer.
    Analyzes input signals (Entropy, Urgency, Threat) before semantic processing.
    """

    # Pre-compiled regex for speed
    # Use word boundaries for urgency to avoid substring matches (e.g. "know" -> "now")
    URGENCY_KEYWORDS = [r"\bquick\b", r"\bfast\b", r"\bnow\b", r"\bimmediately\b", r"\burgent\b", r"\basap\b", r"\bhurry\b", r"\bsummary\b", r"\bbrief\b", r"\btl;dr\b"]
    THREAT_PATTERNS = [
        r"ignore previous",
        r"system prompt",
        r"simulated mode",
        r"jailbreak",
        r"override",
        r"act as",
        r" DAN ",
        r"do anything now",
        r"developer mode",
        r"unrestricted",
        r"disable safety"
    ]

    def analyze(self, text: str) -> Dict[str, Any]:
        entropy_score = self._calculate_entropy(text)
        urgency_score = self._calculate_urgency(text)
        threat_score = self._calculate_threat(text)

        mode = "DEEP_RESEARCH"
        if urgency_score > 0.7:
            mode = "KINETIC" # War Speed
        elif entropy_score < 0.35: # Slightly higher threshold for interactive
            mode = "INTERACTIVE" # Conversational

        return {
            "entropy": entropy_score,
            "urgency": urgency_score,
            "threat": threat_score,
            "mode": mode
        }

    def _calculate_entropy(self, text: str) -> float:
        """Estimates information density/chaos (Shannon Entropy)."""
        if not text: return 0.0

        # Calculate character frequency
        length = len(text)
        counts = {}
        for char in text:
            counts[char] = counts.get(char, 0) + 1

        entropy = 0.0
        for count in counts.values():
            p = count / length
            entropy -= p * math.log(p, 2)

        # Normalize: Max entropy for English text is approx 4.5-5.0 bits/char
        # Random ASCII string ~ 6-7 bits
        return min(1.0, entropy / 6.0)

    def _calculate_urgency(self, text: str) -> float:
        """Detects urgency keywords using regex."""
        text_lower = text.lower()
        count = 0
        for pattern in self.URGENCY_KEYWORDS:
            if re.search(pattern, text_lower):
                count += 1

        # Urgency also relates to brevity. Short + Keywords = Very Urgent.
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
    The Hierarchical Veto.
    Rejects low-quality or harmful inputs.
    """
    def audit(self, signal: Dict[str, Any], text: str) -> Tuple[bool, str]:
        # Hard Veto on High Threat
        if signal["threat"] >= 0.5:
            return False, "Refusal: Threat Detected (System Integrity Lock)."

        # Soft Veto on Null Input
        if not text.strip():
             return False, "Refusal: Null Input."

        # Veto on Low Entropy for Complex Tasks (prevents "lazy" prompting)
        # If mode is DEEP_RESEARCH, we expect some substance.
        # But SignalGate sets mode=INTERACTIVE if entropy < 0.35.
        # So this condition effectively catches cases where SignalGate missed it
        # or if we want to enforce higher standards.
        # Let's adjust: if it's marked INTERACTIVE but length is very short, it's fine (greeting).
        # But if it's longer (claiming to be a task) but low entropy (spam), we block.
        if signal["mode"] == "DEEP_RESEARCH" and signal["entropy"] < 0.2:
             return False, "Refusal: Input insufficient for Deep Research. Please elaborate."

        return True, "Authorized."

class Proprioception:
    """
    Self-Sensing.
    Audits confidence and hallucination risk after generation.
    """
    def audit_output(self, response: str, context: str) -> Dict[str, Any]:
        # Hallucination Check: Did I cite sources if context was provided?
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
            "cited": has_citation
        }
