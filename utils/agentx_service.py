import asyncio
import logging
import random
import time
from typing import List, Dict, Any
import yfinance as yf
import ccxt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AgentXService:
    def __init__(self):
        self.symbols = ['^GSPC', 'BTC-USD', 'GC=F', 'SI=F', 'EURUSD=X', 'NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'TSLA']
        self.last_tick = {
            "time": 0,
            "projected": 5000.0,
            "actual": 5000.0,
            "divergence": 0.0,
            "computeLoad": 0.0,
            "confidence": 0.0
        }
        self.exchange = ccxt.binance()

    async def get_market_data(self, range_str: str = '7d') -> Dict[str, Any]:
        try:
            quotes = []

            # Use ccxt for BTC if possible, otherwise yfinance
            for symbol in self.symbols:
                try:
                    if symbol == 'BTC-USD':
                        ticker = await asyncio.to_thread(self.exchange.fetch_ticker, 'BTC/USDT')
                        price = ticker['last']
                        change = ticker['percentage']
                        name = 'Bitcoin'
                    else:
                        t = yf.Ticker(symbol)
                        # fast_info is sometimes buggy, use basic info or history
                        hist = t.history(period='1d')
                        if not hist.empty:
                            price = hist['Close'].iloc[-1]
                            prev_close = hist['Open'].iloc[-1]
                            change = ((price - prev_close) / prev_close) * 100
                        else:
                            price = 0
                            change = 0
                        name = symbol

                    quotes.append({
                        "symbol": symbol,
                        "price": float(price),
                        "change": float(change),
                        "name": name
                    })
                except Exception as e:
                    logger.warning(f"Error fetching quote for {symbol}: {e}")
                    quotes.append({
                        "symbol": symbol,
                        "price": 0,
                        "change": 0,
                        "name": symbol
                    })

            # Fetch history for ^GSPC
            period = '7d'
            interval = '1h'
            if range_str == '1d':
                period = '1d'
                interval = '5m'
            elif range_str == '1mo' or range_str == '1m':
                period = '1mo'
                interval = '1d'
            elif range_str == '1y':
                period = '1y'
                interval = '1d'

            history = await asyncio.to_thread(yf.download, '^GSPC', period=period, interval=interval, progress=False)
            chart_data = []
            if not history.empty:
                for index, row in history.iterrows():
                    # Handle MultiIndex if necessary, but usually with single ticker it's fine
                    close_val = row['Close']
                    if isinstance(close_val, (float, int)):
                        price = float(close_val)
                    else:
                        price = float(close_val.iloc[0]) if not close_val.empty else 0

                    chart_data.append({
                        "time": index.isoformat(),
                        "price": price
                    })

            arbitrage_opps = [
                { "id": 1, "asset": 'ETH', "route": 'Uniswap (Ethereum) -> SushiSwap (Arbitrum)', "spread": '1.2%', "profit": '+$45.20', "time": 'Just now' },
                { "id": 2, "asset": 'USDC', "route": 'Curve (Optimism) -> Aave (Polygon)', "spread": '0.8%', "profit": '+$12.50', "time": '2 mins ago' },
                { "id": 3, "asset": 'WBTC', "route": 'Binance -> GMX (Arbitrum)', "spread": '2.1%', "profit": '+$185.00', "time": '5 mins ago' }
            ]

            return {
                "quotes": quotes,
                "chart": chart_data,
                "arbitrage": arbitrage_opps
            }
        except Exception as e:
            logger.error(f"Error in AgentXService.get_market_data: {e}")
            return {"error": str(e)}

    def generate_rehoboam_tick(self) -> Dict[str, Any]:
        now = int(time.time())

        if self.last_tick["time"] == 0:
            actual = 5000.0
            projected = 5000.0
        else:
            actual = self.last_tick["actual"] + (random.random() - 0.5) * 10
            projected = self.last_tick["actual"] + (random.random() - 0.5) * 5

        divergence = abs(projected - actual)
        compute_load = 85 + random.random() * 10
        confidence = 90 + random.random() * 9

        self.last_tick = {
            "time": now,
            "projected": projected,
            "actual": actual,
            "divergence": divergence,
            "computeLoad": compute_load,
            "confidence": confidence
        }
        return self.last_tick

agentx_service = AgentXService()
