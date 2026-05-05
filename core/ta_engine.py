"""
Rehoboam Trading Engine - Core TA Engine with risk integration
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class TAEngine:
    """Technical Analysis Engine for crypto trading"""

    def __init__(self, risk_manager=None):
        self.risk_manager = risk_manager
        self.indicators = {}

    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return None

        deltas = np.diff(prices)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gain[-period:])
        avg_loss = np.mean(loss[-period:])

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def calculate_moving_average(self, prices: List[float], period: int = 20) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        return np.mean(prices[-period:])

    def generate_signal(self, symbol: str, prices: List[float]) -> Dict:
        """Generate trading signal based on TA indicators"""
        rsi = self.calculate_rsi(prices)
        ma = self.calculate_moving_average(prices)

        signal = {"symbol": symbol, "timestamp": datetime.now().isoformat(), "action": "HOLD"}

        if rsi and rsi < 30:
            signal["action"] = "BUY"
        elif rsi and rsi > 70:
            signal["action"] = "SELL"

        if self.risk_manager:
            signal = self.risk_manager.validate_signal(signal, ma)

        return signal
