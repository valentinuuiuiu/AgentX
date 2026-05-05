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

class TestRiskManagerPnL:
    @pytest.fixture
    def risk_manager(self):
        return RiskManager(max_drawdown=10.0)

    def test_calculate_pnl_long_profit(self, risk_manager):
        """Test a long position (positive amount) where the current price is higher than the entry price."""
        position = 10.0
        entry_price = 100.0
        current_price = 110.0
        # Expected: 10 * (110 - 100) = 100
        assert risk_manager.calculate_pnl(position, entry_price, current_price) == 100.0

    def test_calculate_pnl_long_loss(self, risk_manager):
        """Test a long position where the current price is lower than the entry price."""
        position = 10.0
        entry_price = 100.0
        current_price = 90.0
        # Expected: 10 * (90 - 100) = -100
        assert risk_manager.calculate_pnl(position, entry_price, current_price) == -100.0

    def test_calculate_pnl_short_profit(self, risk_manager):
        """Test a short position (negative amount) where the current price is lower than the entry price."""
        position = -10.0
        entry_price = 100.0
        current_price = 90.0
        # Expected: -10 * (90 - 100) = 100
        assert risk_manager.calculate_pnl(position, entry_price, current_price) == 100.0

    def test_calculate_pnl_short_loss(self, risk_manager):
        """Test a short position where the current price is higher than the entry price."""
        position = -10.0
        entry_price = 100.0
        current_price = 110.0
        # Expected: -10 * (110 - 100) = -100
        assert risk_manager.calculate_pnl(position, entry_price, current_price) == -100.0

    def test_calculate_pnl_zero_position(self, risk_manager):
        """Test PnL calculation when there is no position."""
        position = 0.0
        entry_price = 100.0
        current_price = 150.0
        # Expected: 0
        assert risk_manager.calculate_pnl(position, entry_price, current_price) == 0.0

    def test_calculate_pnl_no_price_change(self, risk_manager):
        """Test PnL calculation when the price hasn't changed."""
        position = 10.0
        entry_price = 100.0
        current_price = 100.0
        # Expected: 0
        assert risk_manager.calculate_pnl(position, entry_price, current_price) == 0.0

    def test_calculate_pnl_fractional_values(self, risk_manager):
        """Test PnL calculation with fractional positions and prices."""
        position = 1.5
        entry_price = 100.5
        current_price = 110.75
        # Expected: 1.5 * (110.75 - 100.5) = 1.5 * 10.25 = 15.375
        assert risk_manager.calculate_pnl(position, entry_price, current_price) == 15.375
