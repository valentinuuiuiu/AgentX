import pytest
from core.risk_manager import RiskManager

def test_validate_signal_buy_exceeds_limit():
    """Test that BUY signal is changed to HOLD when position limit is reached"""
    manager = RiskManager()
    manager.positions = {"BTC": 100.0}
    manager.max_position = 100.0

    signal = {"symbol": "BTC", "action": "BUY"}
    validated = manager.validate_signal(signal)

    assert validated["action"] == "HOLD"
    assert validated["reason"] == "Position limit reached"
    # Ensure original signal is not mutated
    assert signal["action"] == "BUY"

def test_validate_signal_buy_within_limit():
    """Test that BUY signal is unchanged when position is below limit"""
    manager = RiskManager()
    manager.positions = {"BTC": 50.0}
    manager.max_position = 100.0

    signal = {"symbol": "BTC", "action": "BUY"}
    validated = manager.validate_signal(signal)

    assert validated["action"] == "BUY"
    assert "reason" not in validated

def test_validate_signal_buy_no_position():
    """Test that BUY signal is unchanged when there is no existing position"""
    manager = RiskManager()
    manager.positions = {}
    manager.max_position = 100.0

    signal = {"symbol": "BTC", "action": "BUY"}
    validated = manager.validate_signal(signal)

    assert validated["action"] == "BUY"
    assert "reason" not in validated

def test_validate_signal_sell_ignores_limit():
    """Test that SELL signal is unchanged even if position is at limit"""
    manager = RiskManager()
    manager.positions = {"BTC": 100.0}
    manager.max_position = 100.0

    signal = {"symbol": "BTC", "action": "SELL"}
    validated = manager.validate_signal(signal)

    assert validated["action"] == "SELL"
    assert "reason" not in validated

def test_validate_signal_hold_ignores_limit():
    """Test that HOLD signal is unchanged even if position is at limit"""
    manager = RiskManager()
    manager.positions = {"BTC": 100.0}
    manager.max_position = 100.0

    signal = {"symbol": "BTC", "action": "HOLD"}
    validated = manager.validate_signal(signal)

    assert validated["action"] == "HOLD"
    assert "reason" not in validated
