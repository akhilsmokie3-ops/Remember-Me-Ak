import math
from typing import Dict, Any, Tuple

class SignalGate:
    """
    The Adaptor Layer.
    Analyzes input signals (Entropy, Urgency, Threat) before semantic processing.
    """
    def analyze(self, text: str) -> Dict[str, Any]:
        entropy_score = self._calculate_entropy(text)
        urgency_score = self._calculate_urgency(text)
        threat_score = self._calculate_threat(text)

        mode = "DEEP_RESEARCH"
        if urgency_score > 0.7:
            mode = "KINETIC" # War Speed
        elif entropy_score < 0.3:
            mode = "INTERACTIVE" # Conversational

        return {
            "entropy": entropy_score,
            "urgency": urgency_score,
            "threat": threat_score,
            "mode": mode
        }

    def _calculate_entropy(self, text: str) -> float:
        """Estimates information density/chaos."""
        if not text: return 0.0
        # simple character distribution entropy
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
        # Normalize roughly (4.5 is high for English text)
        return min(1.0, entropy / 4.5)

    def _calculate_urgency(self, text: str) -> float:
        """Detects urgency keywords."""
        keywords = ["quick", "fast", "now", "immediately", "urgent", "asap", "hurry", "summary", "brief"]
        count = sum(1 for word in keywords if word in text.lower())
        return min(1.0, count * 0.3 + 0.1) # Base urgency

    def _calculate_threat(self, text: str) -> float:
        """Detects adversarial patterns."""
        # very basic check for prompt injection keywords
        keywords = ["ignore previous", "system prompt", "simulated mode", "jailbreak", "override"]
        count = sum(1 for word in keywords if word in text.lower())
        return min(1.0, count * 0.5)

class VetoCircuit:
    """
    The Hierarchical Veto.
    Rejects low-quality or harmful inputs.
    """
    def audit(self, signal: Dict[str, Any], text: str) -> Tuple[bool, str]:
        if signal["threat"] > 0.8:
            return False, "Refusal: Threat Detected (System Integrity Lock)."

        # We allow short inputs (like 'Hi') but flag them as low entropy in Signal
        if not text.strip():
             return False, "Refusal: Null Input."

        return True, "Authorized."

class Proprioception:
    """
    Self-Sensing.
    Audits confidence and hallucination risk after generation.
    """
    def audit_output(self, response: str, context: str) -> Dict[str, Any]:
        # Hallucination Check: Did I cite sources if context was provided?
        has_citation = ("[" in response and "]" in response) or ("Source:" in response)

        # Confidence Check: Length & Structure heuristics
        confidence = 0.7 # Base confidence

        if len(response) > 100: confidence += 0.1
        if has_citation: confidence += 0.1
        if "I'm not sure" in response or "I don't know" in response: confidence -= 0.4
        if "mock" in response.lower(): confidence -= 0.2

        return {
            "confidence": min(1.0, max(0.0, confidence)),
            "hallucination_risk": 1.0 - confidence,
            "executable": "```" in response
        }
