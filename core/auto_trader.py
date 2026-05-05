"""
Auto Trader for Rehoboam - Automated trading with risk management
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random


class AutoTrader:
    """Automated trading bot with risk checks"""

    def __init__(self, ta_engine, risk_manager, exchange_engine, symbols: List[str] = None):
        self.ta_engine = ta_engine
        self.risk_manager = risk_manager`
        self.exchange_engine = exchange_engine
        self.symbols = symbols or ["BTC-USD", "ETH-USD"]
        self.is_running = False
        self.trade_history = []

    def start(self) -> bool:
        """Start auto trading"""
        self.is_running = True
        return True

    def stop(self) -> bool:
        """Stop auto trading"""
        self.is_running = False
        return True

    def execute_trade_cycle(self, market_data: Dict[str, List[float]]) -> List[Dict]:
        """Execute one trading cycle"""
        if not self.is_running:
            return []

        trades = []
        for symbol in self.symbols:
            if symbol not in market_data:
                continue

            prices = market_data[symbol]
            if len(prices) < 15:
                continue

            signal = self.ta_engine.generate_signal(symbol, prices)
            validated = self.risk_manager.validate_signal(signal, prices[-1])

            if validated["action"] in ["BUY", "SELL"]:
                order = self.exchange_engine.submit_order(
                    symbol=symbol,
                    side=validated["action"],
                    quantity=1.0,
                    price=prices[-1]
                )
                if order:
                    trade = self.exchange_engine.execute_order(order["order_id"])
                    if trade:
                        trades.append(trade)
                        self.trade_history.append(trade)

        return trades

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        total_trades = len(self.trade_history)
        profitable = len([t for t in self.trade_history if t.get("price", 0) > 0])

        return {
            "total_trades": total_trades,
            "profitable_trades": profitable,
            "is_running": self.is_running,
            "symbols": self.symbols,
            "open_positions": len(self.risk_manager.positions)
        }

    def set_symbols(self, symbols: List[str]):
        """Update trading symbols"""
        self.symbols = symbols
