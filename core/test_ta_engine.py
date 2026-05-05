import pytest
import numpy as np
from core.ta_engine import TAEngine

def test_calculate_moving_average_happy_path():
    engine = TAEngine()
    prices = [10.0, 20.0, 30.0, 40.0, 50.0]
    # period of 3: avg of last 3 (30, 40, 50) = 40.0
    assert engine.calculate_moving_average(prices, period=3) == pytest.approx(40.0)

def test_calculate_moving_average_exact_period():
    engine = TAEngine()
    prices = [10.0, 20.0, 30.0]
    # period of 3: avg of 10, 20, 30 = 20.0
    assert engine.calculate_moving_average(prices, period=3) == pytest.approx(20.0)

def test_calculate_moving_average_less_than_period():
    engine = TAEngine()
    prices = [10.0, 20.0]
    assert engine.calculate_moving_average(prices, period=3) is None

def test_calculate_moving_average_default_period():
    engine = TAEngine()
    # default period is 20
    prices = [float(i) for i in range(1, 21)] # 1 to 20
    # avg of 1..20 is 10.5
    assert engine.calculate_moving_average(prices) == pytest.approx(10.5)

def test_calculate_moving_average_larger_than_default_period():
    engine = TAEngine()
    # 25 prices
    prices = [float(i) for i in range(1, 26)] # 1 to 25
    # Last 20 prices are 6..25
    # avg of 6..25 is 15.5
    assert engine.calculate_moving_average(prices) == pytest.approx(15.5)
