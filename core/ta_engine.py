from typing import List, Optional

class TAEngine:
    def calculate_moving_average(self, prices: List[float], period: int = 20) -> Optional[float]:
        """Calculate Moving Average"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
