import asyncio
import os
import json
import logging
from binance import AsyncClient, BinanceSocketManager
from datetime import datetime

# Configure logging for the Binance Tunnel
logging.basicConfig(level=logging.INFO, format='%(asctime)s - BINANCE-TUNNEL - %(message)s')
logger = logging.getLogger(__name__)

class BinanceRealTimeTunnel:
    """
    A real-time data tunnel for Binance market data.
    "Connecting Prana to the heartbeat of the market."
    """
    
    def __init__(self):
        self.client = None
        self.bsm = None
        self.symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "MATICUSDT", "SOLUSDT"]
        self.current_prices = {}
        self.is_running = False
        
    async def start(self):
        """Start the real-time tunnel"""
        logger.info("⚡ OPENING BINANCE REAL-TIME TUNNEL...")
        self.client = await AsyncClient.create()
        self.bsm = BinanceSocketManager(self.client)
        self.is_running = True
        
        # Create a multiplex socket for multiple symbols
        # We use klines (1m) for trend and ticker for real-time price
        streams = [f"{s.lower()}@ticker" for s in self.symbols]
        
        async with self.bsm.multiplex_socket(streams) as ms:
            logger.info(f"✅ TUNNEL ESTABLISHED for: {', '.join(self.symbols)}")
            
            while self.is_running:
                res = await ms.recv()
                if res:
                    data = res['data']
                    symbol = data['s']
                    price = float(data['c']) # Current price
                    
                    self.current_prices[symbol] = {
                        "price": price,
                        "change_24h": data['p'],
                        "change_pct_24h": data['P'],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Log heartbeat occasionally
                    if symbol == "BTCUSDT" and int(datetime.now().second) % 30 == 0:
                        logger.info(f"💓 HEARTBEAT | BTC: ${price:,.2f} | Status: REAL")

    async def get_price(self, symbol):
        """Get the latest price from the tunnel cache"""
        pair = f"{symbol.upper()}USDT" if "USDT" not in symbol.upper() else symbol.upper()
        return self.current_prices.get(pair)

    async def stop(self):
        """Close the tunnel"""
        logger.info("🛑 CLOSING BINANCE REAL-TIME TUNNEL...")
        self.is_running = False
        if self.client:
            await self.client.close_connection()

async def main():
    tunnel = BinanceRealTimeTunnel()
    try:
        await tunnel.start()
    except KeyboardInterrupt:
        await tunnel.stop()

if __name__ == "__main__":
    asyncio.run(main())
