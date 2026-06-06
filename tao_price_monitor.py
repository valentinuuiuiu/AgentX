"""
🏔️ Bittensor TAO Price Monitor & Earnings Calculator
=======================================================

Track TAO price and calculate potential mining earnings.
Even 0.001 TAO/day = money when TAO is $300+.

Usage:
    python3 tao_price_monitor.py --watch
    python3 tao_price_monitor.py --calc --daily-signals 100
"""

import os
import sys
import json
import time
import argparse
import logging
import requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger("TAOPrice")

# APIs
COINGECKO_API = "https://api.coingecko.com/api/v3"
COINCAP_API = "https://api.coincap.io/v2"

# Cache
CACHE_FILE = Path("signal_data/tao_price.json")
CACHE_FILE.parent.mkdir(exist_ok=True)


class TAOPriceMonitor:
    """Monitor TAO price and calculate earnings."""
    
    def __init__(self):
        self.price_usd = 0.0
        self.price_btc = 0.0
        self.market_cap = 0.0
        self.volume_24h = 0.0
        self.price_change_24h = 0.0
        self.last_update = None
    
    def fetch_price(self) -> bool:
        """Fetch current TAO price from CoinGecko."""
        try:
            # Try CoinGecko first
            url = f"{COINGECKO_API}/coins/bittensor"
            r = requests.get(url, timeout=15)
            
            if r.status_code == 200:
                data = r.json()
                market = data.get("market_data", {})
                
                self.price_usd = market.get("current_price", {}).get("usd", 0)
                self.price_btc = market.get("current_price", {}).get("btc", 0)
                self.market_cap = market.get("market_cap", {}).get("usd", 0)
                self.volume_24h = market.get("total_volume", {}).get("usd", 0)
                self.price_change_24h = market.get("price_change_percentage_24h", 0)
                self.last_update = datetime.now().isoformat()
                
                self._save_cache()
                return True
                
        except Exception as e:
            logger.warning(f"CoinGecko failed: {e}")
        
        # Fallback: CoinCap
        try:
            url = f"{COINCAP_API}/assets/bittensor"
            r = requests.get(url, timeout=15)
            
            if r.status_code == 200:
                data = r.json().get("data", {})
                self.price_usd = float(data.get("priceUsd", 0))
                self.market_cap = float(data.get("marketCapUsd", 0))
                self.volume_24h = float(data.get("volumeUsd24Hr", 0))
                self.price_change_24h = float(data.get("changePercent24Hr", 0))
                self.last_update = datetime.now().isoformat()
                
                self._save_cache()
                return True
                
        except Exception as e:
            logger.warning(f"CoinCap failed: {e}")
        
        # Try cache
        return self._load_cache()
    
    def _save_cache(self):
        """Save price to cache."""
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump({
                    "price_usd": self.price_usd,
                    "price_btc": self.price_btc,
                    "market_cap": self.market_cap,
                    "volume_24h": self.volume_24h,
                    "price_change_24h": self.price_change_24h,
                    "last_update": self.last_update,
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    def _load_cache(self) -> bool:
        """Load price from cache."""
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE) as f:
                    data = json.load(f)
                self.price_usd = data.get("price_usd", 0)
                self.price_btc = data.get("price_btc", 0)
                self.market_cap = data.get("market_cap", 0)
                self.volume_24h = data.get("volume_24h", 0)
                self.price_change_24h = data.get("price_change_24h", 0)
                self.last_update = data.get("last_update")
                logger.info("Loaded price from cache")
                return True
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
        return False
    
    def display(self):
        """Display current price info."""
        print("\n" + "="*60)
        print("🏔️  TAO (Bittensor) Price Monitor")
        print("="*60)
        print(f"💰 Price:        ${self.price_usd:,.2f}")
        print(f"₿  BTC Price:    {self.price_btc:.8f} BTC")
        print(f"📊 Market Cap:   ${self.market_cap:,.0f}")
        print(f"📈 Volume 24h:   ${self.volume_24h:,.0f}")
        
        change_emoji = "🟢" if self.price_change_24h >= 0 else "🔴"
        print(f"{change_emoji}  Change 24h:   {self.price_change_24h:+.2f}%")
        
        if self.last_update:
            print(f"🕐 Updated:      {self.last_update}")
        print("="*60)
    
    def calculate_earnings(
        self,
        daily_signals: int = 100,
        tao_per_signal: float = 0.0001,
        uptime_days: int = 30,
    ):
        """Calculate potential mining earnings."""
        
        daily_tao = daily_signals * tao_per_signal
        monthly_tao = daily_tao * uptime_days
        yearly_tao = daily_tao * 365
        
        daily_usd = daily_tao * self.price_usd
        monthly_usd = monthly_tao * self.price_usd
        yearly_usd = yearly_tao * self.price_usd
        
        print("\n" + "="*60)
        print("⛏️  TAO Mining Earnings Projection")
        print("="*60)
        print(f"Assumptions:")
        print(f"  Daily signals served:    {daily_signals}")
        print(f"  TAO per signal:          {tao_per_signal:.6f}")
        print(f"  TAO price:               ${self.price_usd:,.2f}")
        print(f"  Uptime:                  {uptime_days} days (month)")
        print("-"*60)
        print(f"📊 DAILY Earnings:")
        print(f"   TAO:  {daily_tao:.6f} TAO")
        print(f"   USD:  ${daily_usd:.2f}")
        print(f"📊 MONTHLY Earnings:")
        print(f"   TAO:  {monthly_tao:.6f} TAO")
        print(f"   USD:  ${monthly_usd:.2f}")
        print(f"📊 YEARLY Earnings:")
        print(f"   TAO:  {yearly_tao:.6f} TAO")
        print(f"   USD:  ${yearly_usd:.2f}")
        print("="*60)
        print("💡 Even 0.001 TAO/day = ${:.2f}/month".format(0.001 * 30 * self.price_usd))
        print("   Every query = potential TAO reward")
        print("   Quality signals = higher rank = more TAO")
        print("="*60)
    
    def watch(self, interval: int = 60):
        """Watch price continuously."""
        print("🏔️ Watching TAO price... Press Ctrl+C to stop\n")
        
        try:
            while True:
                if self.fetch_price():
                    self.display()
                else:
                    print("❌ Failed to fetch price")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped watching")


def main():
    parser = argparse.ArgumentParser(description="TAO Price Monitor")
    parser.add_argument("--watch", action="store_true", help="Watch price continuously")
    parser.add_argument("--calc", action="store_true", help="Calculate earnings")
    parser.add_argument("--daily-signals", type=int, default=100, help="Daily signals served")
    parser.add_argument("--tao-per-signal", type=float, default=0.0001, help="TAO per signal")
    parser.add_argument("--interval", type=int, default=60, help="Watch interval (seconds)")
    
    args = parser.parse_args()
    
    monitor = TAOPriceMonitor()
    
    if args.watch:
        monitor.watch(args.interval)
    
    elif args.calc:
        monitor.fetch_price()
        monitor.calculate_earnings(
            daily_signals=args.daily_signals,
            tao_per_signal=args.tao_per_signal,
        )
    
    else:
        if monitor.fetch_price():
            monitor.display()
        else:
            print("❌ Failed to fetch TAO price")
            print("   Try: python3 tao_price_monitor.py --watch")


if __name__ == "__main__":
    main()