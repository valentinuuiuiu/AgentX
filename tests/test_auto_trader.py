from core.auto_trader import AutoTrader

def test_auto_trader_start():
    trader = AutoTrader()
    assert not trader.is_running
    result = trader.start()
    assert result is True
    assert trader.is_running is True

def test_auto_trader_start_already_running():
    trader = AutoTrader()
    trader.is_running = True
    result = trader.start()
    assert result is False
    assert trader.is_running is True
