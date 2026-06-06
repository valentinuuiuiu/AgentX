#!/usr/bin/env python3
"""
🏔️ REHOBOAM CRYPTO SIGNAL SERVICE 🏔️
=====================================
End-to-end trading signal generator.
Uses real price feeds, generates actionable signals, posts to Telegram.

THIS IS THE PRODUCT. This makes money.
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

SIGNAL_CONFIG = {
    "pairs": [
        "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", 
        "ADA-USD", "DOT-USD", "LINK-USD", "MATIC-USD",
        "AVAX-USD", "ARB-USD", "OP-USD", "NEAR-USD",
        "FTM-USD", "INJ-USD", "SUI-USD",
    ],
    # Map pair symbols to Binance trading pairs (override for non-standard names)
    "binance_symbols": {
        "MATIC-USD": "POLUSDT", # MATIC rebranded to POL on Binance
    },
    "timeframes": ["1h", "4h", "1d"],
    "check_interval_minutes": 15,
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    "min_signal_strength": 0.30, # Lowered from 0.6 — more signals = more value for subscribers
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "data_dir": "/home/aryan/free-claude/bittensor/clean_rehoboam_project/signal_data",
}


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Signal:
    pair: str
    timeframe: str
    action: str  # BUY, SELL, HOLD
    strength: float  # 0-1
    price: float
    indicators: Dict[str, float]
    timestamp: str
    reason: str
    tier: str = "FREE"  # FREE, BASIC, PRO, VIP — for monetization
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass  
class Performance:
    total_signals: int = 0
    correct_signals: int = 0
    profit_pips: float = 0.0
    last_updated: str = ""


# =============================================================================
# PRICE FETCHER
# =============================================================================

class PriceFetcher:
    """Fetches real crypto prices from multiple sources."""
    
    # Override mapping for coins with non-standard Binance symbols
    BINANCE_SYMBOL_MAP = {
        "MATIC-USD": "POLUSDT",  # MATIC rebranded to POL
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _get_binance_symbol(self, symbol: str) -> str:
        """Convert pair symbol to Binance format. E.g. BTC-USD → BTCUSDT"""
        if symbol in self.BINANCE_SYMBOL_MAP:
            return self.BINANCE_SYMBOL_MAP[symbol]
        base = symbol.split("-")[0]
        return base + "USDT"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def fetch_binance_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from Binance."""
        try:
            # Use mapping if available, else convert BTC-USD → BTCUSDT
            binance_symbol = self._get_binance_symbol(symbol)
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}"
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data["price"])
        except Exception as e:
            logger.debug(f"Binance fetch failed for {symbol}: {e}")
        return None
    
    async def fetch_coinbase_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from Coinbase."""
        try:
            url = f"https://api.coinbase.com/v2/exchange-rates?currency={symbol.split('-')[0]}"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data["data"]["rates"]["USD"])
        except Exception as e:
            logger.debug(f"Coinbase fetch failed for {symbol}: {e}")
        return None
    
    async def fetch_klines(self, symbol: str, interval: str = "1h", limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from Binance."""
        try:
            binance_symbol = self._get_binance_symbol(symbol)
            url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={interval}&limit={limit}"
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    df = pd.DataFrame(data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                    return df
        except Exception as e:
            logger.error(f"Klines fetch failed for {symbol}: {e}")
        return None
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get price from best available source."""
        price = await self.fetch_binance_price(symbol)
        if price:
            return price
        return await self.fetch_coinbase_price(symbol)


# =============================================================================
# TECHNICAL ANALYSIS
# =============================================================================

class TechnicalAnalyzer:
    """Calculates technical indicators for signal generation."""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD. Returns (macd, signal, histogram)."""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
    
    @staticmethod
    def calculate_bollinger(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands. Returns (upper, middle, lower)."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper.iloc[-1], middle.iloc[-1], lower.iloc[-1]
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=period).mean().iloc[-1]
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1]
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, float]:
        """Run full technical analysis on price data."""
        close = df['close']
        high = df['high']
        low = df['low']
        
        indicators = {
            'rsi': self.calculate_rsi(close),
            'macd': self.calculate_macd(close)[0],
            'macd_signal': self.calculate_macd(close)[1],
            'macd_hist': self.calculate_macd(close)[2],
            'bb_upper': self.calculate_bollinger(close)[0],
            'bb_middle': self.calculate_bollinger(close)[1],
            'bb_lower': self.calculate_bollinger(close)[2],
            'sma_50': self.calculate_sma(close, 50),
            'sma_200': self.calculate_sma(close, 200) if len(close) >= 200 else self.calculate_sma(close, min(len(close), 100)),
            'atr': self.calculate_atr(high, low, close),
            'current_price': close.iloc[-1],
            'price_change_24h': ((close.iloc[-1] - close.iloc[-24]) / close.iloc[-24] * 100) if len(close) >= 24 else 0,
        }
        
        return indicators


# =============================================================================
# SIGNAL GENERATOR
# =============================================================================

class SignalGenerator:
    """Generates trading signals from technical indicators."""
    
    def __init__(self, config: Dict = None):
        self.config = config or SIGNAL_CONFIG
        self.analyzer = TechnicalAnalyzer()
    
    def generate_signal(self, pair: str, timeframe: str, indicators: Dict) -> Optional[Signal]:
        """Generate signal from indicators."""
        price = indicators['current_price']
        rsi = indicators['rsi']
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        macd_hist = indicators['macd_hist']
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']
        sma_50 = indicators['sma_50']
        sma_200 = indicators['sma_200']
        
        # Scoring system
        buy_score = 0.0
        sell_score = 0.0
        reasons = []
        
        # RSI signals
        if rsi < 30:
            buy_score += 0.25
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 70:
            sell_score += 0.25
            reasons.append(f"RSI overbought ({rsi:.1f})")
        
        # MACD signals
        if macd > macd_signal and macd_hist > 0:
            buy_score += 0.25
            reasons.append("MACD bullish crossover")
        elif macd < macd_signal and macd_hist < 0:
            sell_score += 0.25
            reasons.append("MACD bearish crossover")
        
        # Bollinger Bands
        if price < bb_lower:
            buy_score += 0.20
            reasons.append("Price below lower BB")
        elif price > bb_upper:
            sell_score += 0.20
            reasons.append("Price above upper BB")
        
        # Moving Average trend
        if sma_50 > sma_200:
            buy_score += 0.15
            reasons.append("Golden cross trend")
        elif sma_50 < sma_200:
            sell_score += 0.15
            reasons.append("Death cross trend")
        
        # Price momentum
        if indicators['price_change_24h'] < -5:
            buy_score += 0.15
            reasons.append(f"Oversold 24h ({indicators['price_change_24h']:.1f}%)")
        elif indicators['price_change_24h'] > 5:
            sell_score += 0.15
            reasons.append(f"Overbought 24h ({indicators['price_change_24h']:.1f}%)")
        
        # Determine action
        if buy_score >= self.config['min_signal_strength'] and buy_score > sell_score:
            action = "BUY"
            strength = buy_score
        elif sell_score >= self.config['min_signal_strength'] and sell_score > buy_score:
            action = "SELL"
            strength = sell_score
        else:
            return None  # No strong signal
        
        # Assign tier for monetization
        if strength >= 0.60:
            tier = "VIP"
        elif strength >= 0.45:
            tier = "PRO"
        elif strength >= 0.30:
            tier = "BASIC"
        else:
            tier = "FREE"
        
        return Signal(
            pair=pair,
            timeframe=timeframe,
            action=action,
            strength=strength,
            price=price,
            indicators=indicators,
            timestamp=datetime.now().isoformat(),
            reason=" | ".join(reasons),
            tier=tier
        )


# =============================================================================
# TELEGRAM NOTIFIER
# =============================================================================

class TelegramNotifier:
    """Sends signals to Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_signal(self, signal: Signal):
        """Send formatted signal to Telegram."""
        if not self.bot_token or not self.chat_id:
            tier_emoji = {"FREE": "🆓", "BASIC": "🟡", "PRO": "🟠", "VIP": "💎"}.get(signal.tier, "🆓")
            logger.info(f"\n🚨 SIGNAL: {signal.action} {signal.pair} @ ${signal.price:.2f}")
            logger.info(f"   Strength: {signal.strength:.0%} | Tier: {tier_emoji} {signal.tier}")
            logger.info(f"   Reason: {signal.reason}")
            return
        
        emoji = "🟢" if signal.action == "BUY" else "🔴"
        tier_emoji = {"FREE": "🆓", "BASIC": "🟡", "PRO": "🟠", "VIP": "💎"}.get(signal.tier, "🆓")
        
        message = f"""
{emoji} <b>REHOBOAM SIGNAL</b> {emoji}

<b>Action:</b> {signal.action}
<b>Pair:</b> {signal.pair}
<b>Price:</b> ${signal.price:,.2f}
<b>Strength:</b> {signal.strength:.0%}
<b>Tier:</b> {tier_emoji} {signal.tier}
<b>Timeframe:</b> {signal.timeframe}

<b>Indicators:</b>
• RSI: {signal.indicators['rsi']:.1f}
• MACD: {signal.indicators['macd']:.4f}
• 24h Change: {signal.indicators['price_change_24h']:.2f}%

<b>Reason:</b>
{signal.reason}

⏰ {signal.timestamp[:19]}
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        logger.info(f"📨 Signal sent to Telegram: {signal.action} {signal.pair}")
                    else:
                        logger.error(f"Telegram error: {resp.status}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")


# =============================================================================
# PERFORMANCE TRACKER
# =============================================================================

class PerformanceTracker:
    """Tracks signal performance over time."""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.signals_file = self.data_dir / "signals.json"
        self.performance_file = self.data_dir / "performance.json"
    
    def save_signal(self, signal: Signal):
        """Save signal to history."""
        signals = []
        if self.signals_file.exists():
            with open(self.signals_file, 'r') as f:
                signals = json.load(f)
        
        signals.append(signal.to_dict())
        
        # Keep last 1000 signals
        signals = signals[-1000:]
        
        with open(self.signals_file, 'w') as f:
            json.dump(signals, f, indent=2)
    
    def get_stats(self) -> Dict:
        """Get signal statistics."""
        if not self.signals_file.exists():
            return {"total": 0, "buy": 0, "sell": 0}
        
        with open(self.signals_file, 'r') as f:
            signals = json.load(f)
        
        return {
            "total": len(signals),
            "buy": sum(1 for s in signals if s['action'] == 'BUY'),
            "sell": sum(1 for s in signals if s['action'] == 'SELL'),
            "avg_strength": np.mean([s['strength'] for s in signals]) if signals else 0,
            "last_24h": sum(1 for s in signals 
                           if datetime.fromisoformat(s['timestamp']) > datetime.now() - timedelta(hours=24))
        }


# =============================================================================
# MAIN SERVICE
# =============================================================================

class CryptoSignalService:
    """Main signal service that runs 24/7."""
    
    def __init__(self, config: Dict = None):
        self.config = config or SIGNAL_CONFIG
        self.price_fetcher: Optional[PriceFetcher] = None
        self.signal_generator = SignalGenerator(self.config)
        self.analyzer = self.signal_generator.analyzer
        self.telegram = TelegramNotifier(
            self.config.get('telegram_bot_token', ''),
            self.config.get('telegram_chat_id', '')
        )
        self.tracker = PerformanceTracker(self.config['data_dir'])
        self.running = False
        self.last_signals: Dict[str, str] = {}  # pair+tf → last action, for dedup
    
    async def check_pair(self, pair: str, timeframe: str) -> Optional[Signal]:
        """Check a single pair for signals."""
        async with PriceFetcher() as fetcher:
            # Fetch price data
            df = await fetcher.fetch_klines(pair, timeframe, limit=200)
            if df is None or len(df) < 50:
                logger.warning(f"Insufficient data for {pair}")
                return None
            
            # Analyze
            indicators = self.analyzer.analyze(df)
            
            # Generate signal
            signal = self.signal_generator.generate_signal(pair, timeframe, indicators)
            
            # Dedup: skip if same action as last signal for this pair+tf
            if signal:
                key = f"{pair}_{timeframe}"
                last_action = self.last_signals.get(key)
                if last_action == signal.action:
                    logger.debug(f"Dedup: {pair} {timeframe} still {signal.action}, skipping")
                    return None
                self.last_signals[key] = signal.action
            
            return signal
    
    async def run_cycle(self):
        """Run one signal generation cycle."""
        logger.info("="*60)
        logger.info("🔍 SCANNING MARKETS FOR SIGNALS")
        logger.info("="*60)
        
        signals_found = 0
        
        for pair in self.config['pairs']:
            for timeframe in self.config['timeframes']:
                try:
                    signal = await self.check_pair(pair, timeframe)
                    if signal:
                        signals_found += 1
                        logger.info(f"🚨 SIGNAL: {signal.action} {signal.pair} @ ${signal.price:.2f} (strength: {signal.strength:.0%})")
                        
                        # Send to Telegram
                        await self.telegram.send_signal(signal)
                        
                        # Save to history
                        self.tracker.save_signal(signal)
                        
                except Exception as e:
                    logger.error(f"Error checking {pair} {timeframe}: {e}")
        
        # Print stats
        stats = self.tracker.get_stats()
        logger.info(f"\n📊 Cycle complete: {signals_found} signals found")
        logger.info(f"📈 Total signals: {stats['total']} (BUY: {stats['buy']}, SELL: {stats['sell']})")
        logger.info(f"⏰ Next check in {self.config['check_interval_minutes']} minutes\n")
    
    async def run(self):
        """Run the service 24/7."""
        logger.info("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏔️  REHOBOAM CRYPTO SIGNAL SERVICE  🏔️                ║
    ║                                                           ║
    ║   "One product. One purpose. Make money."               ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
        """)
        
        self.running = True
        
        while self.running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            
            # Wait for next check
            await asyncio.sleep(self.config['check_interval_minutes'] * 60)
    
    def stop(self):
        """Stop the service."""
        self.running = False
        logger.info("🛑 Signal service stopped")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Rehoboam Crypto Signal Service")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--interval", type=int, default=15, help="Check interval in minutes")
    parser.add_argument("--pairs", nargs="+", default=None, help="Pairs to monitor")
    args = parser.parse_args()
    
    config = SIGNAL_CONFIG.copy()
    config['check_interval_minutes'] = args.interval
    if args.pairs:
        config['pairs'] = args.pairs
    
    service = CryptoSignalService(config)
    
    if args.once:
        asyncio.run(service.run_cycle())
    else:
        try:
            asyncio.run(service.run())
        except KeyboardInterrupt:
            service.stop()


if __name__ == "__main__":
    main()
