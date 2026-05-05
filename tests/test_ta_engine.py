import pytest
from core.ta_engine import TAEngine

class TestTAEngineRSI:
    def setup_method(self):
        self.engine = TAEngine()

    def test_calculate_rsi_insufficient_data(self):
        """Test RSI calculation with fewer prices than required period + 1."""
        prices = [10.0, 11.0, 12.0]
        # By default period is 14, so it requires at least 15 prices
        result = self.engine.calculate_rsi(prices)
        assert result is None

        # Custom period of 3 requires 4 prices
        result = self.engine.calculate_rsi(prices, period=3)
        assert result is None

    def test_calculate_rsi_all_gains(self):
        """Test RSI when there are only gains in the calculation period."""
        # period=3, need 4 prices. All increasing.
        prices = [10.0, 11.0, 12.0, 13.0]
        result = self.engine.calculate_rsi(prices, period=3)
        # avg_loss should be 0, returning 100.0
        assert result == 100.0

    def test_calculate_rsi_all_losses(self):
        """Test RSI when there are only losses in the calculation period."""
        # period=3, need 4 prices. All decreasing.
        prices = [13.0, 12.0, 11.0, 10.0]
        result = self.engine.calculate_rsi(prices, period=3)
        # avg_gain should be 0. rs = 0 / avg_loss = 0.
        # rsi = 100 - (100 / (1 + 0)) = 0.0
        assert result == 0.0

    def test_calculate_rsi_mixed(self):
        """Test RSI with a mix of gains and losses."""
        # Let's create a known sequence.
        # Prices: 10, 12 (+2), 11 (-1), 14 (+3), 12 (-2)
        prices = [10.0, 12.0, 11.0, 14.0, 12.0]
        # Period = 4, so it looks at the last 4 deltas.
        # Deltas: +2, -1, +3, -2
        # Gains: 2, 0, 3, 0 -> Avg Gain = (2+0+3+0)/4 = 1.25
        # Losses: 0, 1, 0, 2 -> Avg Loss = (0+1+0+2)/4 = 0.75
        # RS = 1.25 / 0.75 = 1.666...
        # RSI = 100 - (100 / (1 + 1.666...)) = 100 - (100 / 2.666...) = 100 - 37.5 = 62.5
        result = self.engine.calculate_rsi(prices, period=4)
        assert result is not None
        assert pytest.approx(result, 0.01) == 62.5

    def test_calculate_rsi_with_more_than_period_data(self):
        """Test RSI when there are more prices than the period requires."""
        # We only care about the last `period` deltas.
        prices = [100.0, 100.0, 100.0, 10.0, 12.0, 11.0, 14.0, 12.0]
        # The last 5 prices match our previous test: 10, 12, 11, 14, 12
        # Deltas: 0, 0, -90, +2, -1, +3, -2
        # For period=4, it looks at the last 4 deltas: +2, -1, +3, -2
        # It should yield the same result: 62.5
        result = self.engine.calculate_rsi(prices, period=4)
        assert result is not None
        assert pytest.approx(result, 0.01) == 62.5

    def test_calculate_rsi_no_change(self):
        """Test RSI when prices are flat in the period."""
        prices = [10.0, 10.0, 10.0, 10.0, 10.0]
        # deltas: 0, 0, 0, 0
        # avg_gain = 0, avg_loss = 0
        # Given the code, if avg_loss == 0, it returns 100.0
        result = self.engine.calculate_rsi(prices, period=4)
        assert result == 100.0
