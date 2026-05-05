from typing import Dict, Optional

class RiskManager:
    def __init__(self):
        self.positions = {}
        self.max_position = 100.0

    def validate_signal(self, signal: Dict, current_price: Optional[float] = None) -> Dict:
        """Validate trading signal against risk parameters"""
        validated_signal = signal.copy()

        # Check position limits
        symbol = signal.get("symbol")
        current_pos = self.positions.get(symbol, 0.0)

        if signal["action"] == "BUY" and current_pos >= self.max_position:
            validated_signal["action"] = "HOLD"
            validated_signal["reason"] = "Position limit reached"

        return validated_signal
