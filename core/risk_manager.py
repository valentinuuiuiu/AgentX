from typing import Dict, Optional

class RiskManager:
    def __init__(self, positions: Optional[Dict[str, float]] = None, max_position: float = 100.0):
        self.positions = positions if positions is not None else {}
        self.max_position = max_position

    def validate_signal(self, signal: Dict) -> Dict:
        """Validate trading signal against risk parameters"""
        validated_signal = signal.copy()

        # Check position limits
        symbol = signal.get("symbol")
        current_pos = self.positions.get(symbol, 0.0)

        if signal["action"] == "BUY" and current_pos >= self.max_position:
            validated_signal["action"] = "HOLD"
            validated_signal["reason"] = "Position limit reached"

        return validated_signal
