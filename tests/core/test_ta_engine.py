import pytest
from core.ta_engine import TAEngine

def test_calculate_moving_average_basic():
    engine = TAEngine()
    prices = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = engine.calculate_moving_average(prices, period=3)
    assert result == 4.0  # (3+4+5)/3

def test_calculate_moving_average_insufficient_data():
    engine = TAEngine()
    prices = [1.0, 2.0]
    result = engine.calculate_moving_average(prices, period=3)
    assert result is None

def test_calculate_moving_average_exact_period():
    engine = TAEngine()
    prices = [1.0, 2.0, 3.0]
    result = engine.calculate_moving_average(prices, period=3)
    assert result == 2.0  # (1+2+3)/3

def test_calculate_moving_average_zero_period():
    engine = TAEngine()
    prices = [1.0, 2.0, 3.0]
    with pytest.raises(ZeroDivisionError):
        engine.calculate_moving_average(prices, period=0)
