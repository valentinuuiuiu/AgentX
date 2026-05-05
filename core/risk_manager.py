class RiskManager:
    def __init__(self, max_drawdown: float):
        self.max_drawdown = max_drawdown
        self.peak_value = 0.0

    def check_drawdown(self, current_value: float) -> bool:
        """Check if max drawdown exceeded"""
        if current_value > self.peak_value:
            self.peak_value = current_value

        if self.peak_value == 0.0:
            return False

        drawdown = (self.peak_value - current_value) / self.peak_value * 100
        if drawdown > self.max_drawdown:
            return True
        return False
