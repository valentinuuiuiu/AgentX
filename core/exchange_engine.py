import uuid
from datetime import datetime
from typing import Dict

class ExchangeEngine:
    def __init__(self):
        self.orders = {}

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
