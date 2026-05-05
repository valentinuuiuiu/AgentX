class AutoTrader:
    def __init__(self):
        self.is_running = False

    def start(self) -> bool:
        """Start the automated trading loop"""
        if self.is_running:
            return False
        self.is_running = True
        return True
