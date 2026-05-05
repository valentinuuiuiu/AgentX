import pytest
from datetime import datetime
from core.exchange_engine import ExchangeEngine

def test_submit_order_happy_path():
    engine = ExchangeEngine()
    order = engine.submit_order(symbol="BTC/USD", side="buy", quantity=1.5, price=50000.0)

    assert order["symbol"] == "BTC/USD"
    assert order["side"] == "BUY"
    assert order["quantity"] == 1.5
    assert order["price"] == 50000.0
    assert order["order_type"] == "LIMIT"
    assert order["status"] == "PENDING"
    assert order["fills"] == []
    assert "order_id" in order
    assert isinstance(order["order_id"], str)
    assert "timestamp" in order
    assert isinstance(order["timestamp"], str)

    # Ensure it's stored in the engine's orders dict
    assert order["order_id"] in engine.orders
    assert engine.orders[order["order_id"]] == order

def test_submit_order_custom_order_type():
    engine = ExchangeEngine()
    order = engine.submit_order(symbol="ETH/USD", side="SELL", quantity=10.0, price=3000.0, order_type="MARKET")

    assert order["symbol"] == "ETH/USD"
    assert order["side"] == "SELL"
    assert order["quantity"] == 10.0
    assert order["price"] == 3000.0
    assert order["order_type"] == "MARKET"
