"""
Risk Manager for Rehoboam - Risk validation and position management
"""

from typing import Dict, Optional, List
from datetime import datetime


class RiskManager:
    """Manages trading risk and position limits"""

    def __init__(self, max_position: float = 1000.0, max_loss: float = 100.0):
        self.max_position = max_position
        self.max_loss = max_loss`
        self.positions = {}
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_value = 0.0

    def validate_signal(self, signal: Dict, current_price: Optional[float] = None) -> Dict:
        """Validate trading signal against risk parameters"""
        validated_signal = signal.copy()

        # Check position limits
        symbol = signal.get("symbol")
        current_pos = self.positions.get(symbol, 0.0)

        if signal["action"] == "BUY" and current_pos >= self.max_position:
            validated_signal["action"] = "HOLD"
            validated_signal["reason"] = "Position limit reached"

        # Check daily loss limits
        if self.daily_pnl <= -self.max_loss:
            validated_signal["action"] = "CLOSE"
            validated_signal["reason"] = "Daily loss limit reached"

        return validated_signal

    def update_position(self, symbol: str, quantity: float, price: float, side: str):
        """Update position on trade execution"""
        current = self.positions.get(symbol, 0.0)
        if side.upper() == "BUY":
            self.positions[symbol] = current + quantity
        elif side.upper() == "SELL":
            self.positions[symbol] = current - quantity

    def calculate_pnl(self, position: float, entry_price: float, current_price: float) -> float:
        """Calculate unrealized PnL"""
        return position * (current_price - entry_price)

    def check_drawdown(self, current_value: float) -> bool:
        """Check if max drawdown exceeded"""
        if current_value > self.peak_value:
            self.peak_value = current_value

        drawdown = (self.peak_value - current_value) / self.peak_value * 100
        if drawdown > self.max_drawdown:
            return True
        return False

    def close_trade(self, symbol: str, exit_price: float, entry_price: float, quantity: float):
        """Close a trade and update PnL"""
        pnl = (exit_price - entry_price) * quantity
        self.daily_pnl += pnl
        if symbol in self.positions:
            del self.positions[symbol]
        return pnl
