"""
Exchange Engine for Rehoboam - Order routing and execution
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid


class ExchangeEngine:
    """Handles order routing and trade execution"""
    
    def __init__(self, fee_rate: float = 0.001):
        self.fee_rate = fee_rate
        self.orders = {}
        self.trades = []
        
    def submit_order(self, symbol: str, side: str, quantity: float, price: float, order_type: str = "LIMIT") -> Dict:
        """Submit order to exchange"""
        order_id = str(uuid.uuid4())
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side.upper(),
            "quantity": quantity,
            "price": price,
            "order_type": order_type,
            "status": "PENDING",
            "timestamp": datetime.now().isoformat(),
            "fills": []
        }
        self.orders[order_id] = order
        return order
    
    def execute_order(self, order_id: str, fill_price: Optional[float] = None) -> Optional[Dict]:
        """Execute order at given price"""
        if order_id not in self.orders:
            return None
            
        order = self.orders[order_id]
        if order["status"] != "PENDING":
            return None
            
        price = fill_price if fill_price else order["price"]
        fee = price * order["quantity"] * self.fee_rate
        
        trade = {
            "trade_id": str(uuid.uuid4()),
            "order_id": order_id,
            "symbol": order["symbol"],
            "side": order["side"],
            "quantity": order["quantity"],
            "price": price,
            "fee": fee,
            "timestamp": datetime.now().isoformat()
        }
        self.trades.append(trade)
        order["status"] = "FILLED"
        order["fills"].append(trade)
        return trade
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status"""
        return self.orders.get(order_id)
    
    def get_trades(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all trades, optionally filtered by symbol"""
        if symbol:
            return [t for t in self.trades if t["symbol"] == symbol]
        return self.trades
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        if order_id in self.orders and self.orders[order_id]["status"] == "PENDING":
            self.orders[order_id]["status"] = "CANCELED"
            return True
        return False
