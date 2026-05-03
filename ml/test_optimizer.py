import sys
import unittest.mock as mock
sys.modules['pandas'] = mock.MagicMock()
sys.modules['numpy'] = mock.MagicMock()
sys.modules['aiohttp'] = mock.MagicMock()
import pytest
from ml.optimizer import ParameterOptimizer
from ml.backtest_engine import BacktestResult

def test_get_parameter_space():
    optimizer = ParameterOptimizer()
    param_space = optimizer.get_parameter_space()
    assert isinstance(param_space, dict)
    expected_keys = [
        'strong_rally_threshold', 'moderate_rally_threshold', 'mild_uptrend_threshold',
        'major_dip_threshold', 'moderate_dip_threshold', 'slight_weakness_threshold',
        'confidence_strong', 'confidence_moderate', 'confidence_mild', 'confidence_dip',
        'confidence_support', 'confidence_weak', 'confidence_neutral', 'confidence_low'
    ]
    for key in expected_keys:
        assert key in param_space
        assert isinstance(param_space[key], list)
        assert len(param_space[key]) > 0
