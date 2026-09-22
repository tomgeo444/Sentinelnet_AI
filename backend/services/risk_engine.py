"""
SentinelNet AI - Transparent Risk Engine
Evaluates risk severity level based on deep learning predictions and confidence metrics.
"""

from backend.config import settings


class RiskEngine:
    """
    Classifies detection severity into: NORMAL, LOW, MEDIUM, HIGH, CRITICAL.
    Designed for SOC visualization and automated triage.
    """
    @staticmethod
    def evaluate_risk(prediction: str, confidence: float, is_attack: bool) -> str:
        """
        Determines the risk classification.
        
        Rules:
        - BENIGN / Normal traffic:
          - If confidence >= 0.60: NORMAL
          - If confidence < 0.60 (uncertain benign): LOW
        - ATTACK traffic:
          - DoS_DDoS: CRITICAL (if conf >= 0.80), else HIGH
          - Bot_Infiltration: CRITICAL (if conf >= 0.80), else HIGH
          - BruteForce: HIGH (if conf >= 0.75), else MEDIUM
          - PortScan: MEDIUM (if conf >= 0.70), else LOW
          - Other / Low confidence attack: LOW
        """
        if not is_attack or prediction == "BENIGN":
            if confidence >= 0.60:
                return "NORMAL"
            return "LOW"

        # Attack classification hierarchy
        pred_upper = prediction.upper()
        if "DOS" in pred_upper or "DDOS" in pred_upper:
            return "CRITICAL" if confidence >= 0.80 else "HIGH"

        if "BOT" in pred_upper or "INFILTRATION" in pred_upper:
            return "CRITICAL" if confidence >= 0.80 else "HIGH"

        if "BRUTE" in pred_upper:
            return "HIGH" if confidence >= 0.75 else "MEDIUM"

        if "SCAN" in pred_upper or "PORTSCAN" in pred_upper:
            return "MEDIUM" if confidence >= 0.70 else "LOW"

        # General confidence thresholds for any other attack types
        if confidence >= settings.RISK_THRESHOLD_CRITICAL:
            return "CRITICAL"
        elif confidence >= settings.RISK_THRESHOLD_HIGH:
            return "HIGH"
        elif confidence >= settings.RISK_THRESHOLD_MEDIUM:
            return "MEDIUM"
        else:
            return "LOW"
