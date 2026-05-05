import pytest
from core.exchange_engine import ExchangeEngine

def test_execute_order_non_existent():
    engine = ExchangeEngine()
    result = engine.execute_order("non_existent_id")
    assert result is None
