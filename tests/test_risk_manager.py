import pytest
from core.risk_manager import RiskManager

def test_check_drawdown_no_drawdown():
    rm = RiskManager(max_drawdown=10.0)
    assert rm.check_drawdown(100.0) == False
    assert rm.peak_value == 100.0

def test_check_drawdown_within_limit():
    rm = RiskManager(max_drawdown=10.0)
    rm.check_drawdown(100.0)
    assert rm.check_drawdown(95.0) == False # 5% drawdown

def test_check_drawdown_exceeds_limit():
    rm = RiskManager(max_drawdown=10.0)
    rm.check_drawdown(100.0)
    assert rm.check_drawdown(85.0) == True # 15% drawdown

def test_check_drawdown_updates_peak():
    rm = RiskManager(max_drawdown=10.0)
    rm.check_drawdown(100.0)
    rm.check_drawdown(110.0) # New peak
    assert rm.peak_value == 110.0
    assert rm.check_drawdown(100.0) == False # (110 - 100) / 110 = 9.09% drawdown
    assert rm.check_drawdown(98.0) == True # (110 - 98) / 110 = 10.9% drawdown

def test_check_drawdown_zero_peak():
    rm = RiskManager(max_drawdown=10.0)
    assert rm.check_drawdown(0.0) == False
    assert rm.check_drawdown(-5.0) == False
