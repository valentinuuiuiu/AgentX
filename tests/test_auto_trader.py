import pytest
from core.auto_trader import AutoTrader

def test_auto_trader_start():
    trader = AutoTrader()
    assert trader.is_running is False
    assert trader.start() is True
    assert trader.is_running is True

    # Test that calling start again returns False
    assert trader.start() is False
    assert trader.is_running is True
