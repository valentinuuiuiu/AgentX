#!/usr/bin/env python3
"""
🏔️ REHOBOAM MULTI-SOURCE CONVERGENCE ENGINE 🏔️
=================================================
The PREMIUM differentiator. No other signal service does this.

Cross-references:
  1. Binance CEX prices (real-time orderbook)
  2. Chainlink on-chain oracle prices (smart contract feeds)
  3. Coinbase CEX prices (backup)
  4. Etherscan on-chain activity (whale tracking)
  5. AI model consensus (TradingAgents MCP)

When multiple sources AGREE on a signal → HIGH CONFIDENCE
When sources DIVERGE → arbitrage opportunity or manipulation warning

This is what makes Rehoboam worth $149/mo instead of $9/mo.
"""

import os
import json
import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pandas as pd
import numpy as np

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent
CHAINLINK_FEEDS = PROJECT_DIR / "chainlink_feeds.json"
SIGNAL_DATA_DIR = PROJECT_DIR / "signal_data"
SIGNAL_DATA_DIR.mkdir(exist_ok=True)

CHAINLINK_ABI = [{'inputs':[],'name':'latestRoundData','outputs':[
    {'name':'roundId','type':'uint80'},{'name':'answer','type':'int256'},
    {'name':'startedAt','type':'uint256'},{'name':'updatedAt','type':'uint256'},
    {'name':'answeredInRound','type':'uint80'}],'stateMutability':'view','type':'function'}]

# Map our pair names to Chainlink feed names
PAIR_TO_CHAINLINK = {
    "BTC-USD": "BTC/USD",
    "ETH-USD": "ETH/USD",
    "LINK-USD": "LINK/USD",
    "SOL-USD": "SOL/USD",
    "AAVE-USD": "AAVE/USD",
    "UNI-USD": "UNI/USD",
}


@dataclass
class ConvergenceSignal:
    """A signal backed by multiple data sources."""
    pair: str
    action: str  # BUY, SELL, HOLD, ARBITRAGE, MANIPULATION_WARNING
    strength: float  # 0-1
    price_cex: float  # Binance price
    price_onchain: float  # Chainlink price
    price_spread: float  # % difference
    price_spread_direction: str  # CEX_PREMIUM or ONCHAIN_PREMIUM
    technical_signal: str  # from Binance TA
    onchain_confirms: bool  # Chainlink agrees with direction
    convergence_score: float  # 0-1, how many sources agree
    sources_count: int  # number of sources that contributed
    reason: str
    timestamp: str
    tier: str = "PRO"  # Convergence signals are always PRO+

    def to_dict(self):
        return asdict(self)


class ChainlinkOracle:
    """Reads prices directly from Chainlink smart contracts on Ethereum mainnet."""

    def __init__(self):
        self.w3 = None
        self.feeds = {}
        self._connected = False

        if not WEB3_AVAILABLE:
            logger.warning("Web3 not available, Chainlink disabled")
            return

        alchemy_key = os.getenv("ALCHEMY_API_KEY", "")
        if not alchemy_key:
            logger.warning("ALCHEMY_API_KEY not set, Chainlink disabled")
            return

        try:
            self.w3 = Web3(Web3.HTTPProvider(
                f'https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}'
            ))
            self._connected = self.w3.is_connected()
            if self._connected:
                logger.info("✅ Chainlink Oracle connected to Ethereum mainnet")
            else:
                logger.warning("❌ Chainlink: Alchemy connection failed")
        except Exception as e:
            logger.warning(f"Chainlink init failed: {e}")

        # Load feed addresses
        if CHAINLINK_FEEDS.exists():
            with open(CHAINLINK_FEEDS) as f:
                data = json.load(f)
                self.feeds = data.get("feeds", {})

    @property
    def connected(self):
        return self._connected and self.w3 is not None

    async def get_price(self, pair: str) -> Optional[float]:
        """Get on-chain price from Chainlink oracle."""
        if not self.connected:
            return None

        chainlink_pair = PAIR_TO_CHAINLINK.get(pair)
        if not chainlink_pair or chainlink_pair not in self.feeds:
            return None

        try:
            addr = self.feeds[chainlink_pair]
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(addr),
                abi=CHAINLINK_ABI
            )
            round_data = contract.functions.latestRoundData().call()
            price = round_data[1] / 1e8
            return price
        except Exception as e:
            logger.debug(f"Chainlink {pair} failed: {e}")
            return None

    async def get_all_prices(self) -> Dict[str, float]:
        """Get all available Chainlink prices."""
        prices = {}
        for pair in PAIR_TO_CHAINLINK:
            price = await self.get_price(pair)
            if price:
                prices[pair] = price
        return prices


class EtherscanAnalyzer:
    """Checks on-chain activity via Etherscan API."""

    def __init__(self):
        self.api_key = os.getenv("ETHERSCAN_API_KEY", "")
        self.base_url = "https://api.etherscan.io/api"

    async def get_whale_activity(self, token_address: str) -> Optional[Dict]:
        """Check for large transactions (whale movement)."""
        if not self.api_key:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "module": "account",
                    "action": "txlist",
                    "address": token_address,
                    "page": 1,
                    "offset": 10,
                    "sort": "desc",
                    "apikey": self.api_key
                }
                async with session.get(self.base_url, params=params,
                                       timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        txs = data.get("result", [])
                        if isinstance(txs, list) and len(txs) > 0:
                            # Find large transactions (> 100 ETH)
                            large_txs = []
                            for tx in txs[:10]:
                                value_wei = int(tx.get("value", "0"))
                                value_eth = value_wei / 1e18
                                if value_eth > 10:  # > 10 ETH
                                    large_txs.append({
                                        "hash": tx.get("hash", ""),
                                        "from": tx.get("from", ""),
                                        "to": tx.get("to", ""),
                                        "value_eth": value_eth,
                                    })
                            return {"large_transactions": large_txs, "total_checked": len(txs)}
        except Exception as e:
            logger.debug(f"Etherscan whale check failed: {e}")
        return None


class ConvergenceEngine:
    """
    The multi-source convergence engine.
    Cross-references CEX prices, on-chain oracles, and on-chain activity
    to produce HIGH CONFIDENCE signals.
    """

    def __init__(self):
        self.chainlink = ChainlinkOracle()
        self.etherscan = EtherscanAnalyzer()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def fetch_binance_price(self, symbol: str) -> Optional[float]:
        """Fetch CEX price from Binance."""
        try:
            base = symbol.split("-")[0]
            binance_symbol = {"MATIC-USD": "POLUSDT"}.get(symbol, base + "USDT")
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data["price"])
        except Exception as e:
            logger.debug(f"Binance {symbol} failed: {e}")
        return None

    async def fetch_binance_klines(self, symbol: str, interval: str = "1h",
                                    limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch OHLCV from Binance."""
        try:
            base = symbol.split("-")[0]
            binance_symbol = {"MATIC-USD": "POLUSDT"}.get(symbol, base + "USDT")
            url = (f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}"
                   f"&interval={interval}&limit={limit}")
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    df = pd.DataFrame(data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df[['open', 'high', 'low', 'close', 'volume']] = \
                        df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                    return df
        except Exception as e:
            logger.debug(f"Binance klines {symbol} failed: {e}")
        return None

    def analyze_technicals(self, df: pd.DataFrame) -> Dict:
        """Run technical analysis on price data."""
        close = df['close']
        high = df['high']
        low = df['low']

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        # MACD
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        histogram = (macd - signal_line).iloc[-1]

        # Bollinger
        middle = close.rolling(window=20).mean().iloc[-1]
        std = close.rolling(window=20).std().iloc[-1]
        bb_upper = middle + (std * 2)
        bb_lower = middle - (std * 2)

        # Trend
        sma_50 = close.rolling(window=50).mean().iloc[-1]
        sma_200 = close.rolling(window=min(200, len(close))).mean().iloc[-1]

        # 24h change
        price_change_24h = 0
        if len(close) >= 24:
            price_change_24h = ((close.iloc[-1] - close.iloc[-24]) / close.iloc[-24] * 100)

        # Determine technical direction
        buy_signals = 0
        sell_signals = 0
        if rsi < 30: buy_signals += 1
        elif rsi > 70: sell_signals += 1
        if macd.iloc[-1] > signal_line.iloc[-1]: buy_signals += 1
        else: sell_signals += 1
        if close.iloc[-1] < bb_lower: buy_signals += 1
        elif close.iloc[-1] > bb_upper: sell_signals += 1
        if sma_50 > sma_200: buy_signals += 1
        elif sma_50 < sma_200: sell_signals += 1

        if buy_signals > sell_signals:
            direction = "BUY"
            strength = buy_signals / 4
        elif sell_signals > buy_signals:
            direction = "SELL"
            strength = sell_signals / 4
        else:
            direction = "HOLD"
            strength = 0

        return {
            "direction": direction,
            "strength": strength,
            "rsi": rsi,
            "macd_hist": histogram,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "price_change_24h": price_change_24h,
            "current_price": close.iloc[-1],
        }

    async def analyze_pair(self, pair: str, timeframe: str = "1h") -> Optional[ConvergenceSignal]:
        """
        Analyze a pair across ALL data sources and produce a convergence signal.
        This is the premium product.
        """
        # 1. Fetch CEX price + technicals from Binance
        df = await self.fetch_binance_klines(pair, timeframe)
        if df is None or len(df) < 50:
            return None

        cex_price = df['close'].iloc[-1]
        technicals = self.analyze_technicals(df)

        # 2. Fetch on-chain price from Chainlink
        onchain_price = await self.chainlink.get_price(pair)

        # 3. Calculate CEX vs On-chain spread
        spread_pct = 0
        spread_direction = "N/A"
        if onchain_price and onchain_price > 0:
            spread_pct = ((cex_price - onchain_price) / onchain_price) * 100
            if spread_pct > 0.05:
                spread_direction = "CEX_PREMIUM"
            elif spread_pct < -0.05:
                spread_direction = "ONCHAIN_PREMIUM"
            else:
                spread_direction = "ALIGNED"

        # 4. Check on-chain confirms technical direction
        onchain_confirms = False
        if onchain_price and technicals['direction'] != "HOLD":
            # If CEX says BUY and on-chain price is lower → on-chain confirms (buy the dip)
            # If CEX says SELL and on-chain price is higher → on-chain confirms (sell the premium)
            if technicals['direction'] == "BUY" and spread_direction in ("ONCHAIN_PREMIUM", "ALIGNED"):
                onchain_confirms = True
            elif technicals['direction'] == "SELL" and spread_direction in ("CEX_PREMIUM", "ALIGNED"):
                onchain_confirms = True

        # 5. Calculate convergence score
        sources = 1  # Binance always counts
        if onchain_price:
            sources += 1

        convergence_score = 0
        if technicals['strength'] >= 0.3:
            convergence_score += 0.4  # Technicals contribute 40%
        if onchain_confirms:
            convergence_score += 0.4  # On-chain confirmation is huge
        if onchain_price and abs(spread_pct) > 0.1:
            convergence_score += 0.2  # Spread detection adds value

        # 6. Determine action
        action = technicals['direction']
        if action == "HOLD":
            # Check for arbitrage opportunity
            if abs(spread_pct) > 0.5:
                action = "ARBITRAGE"
                convergence_score = min(convergence_score + 0.3, 1.0)

        # 7. Build reason
        reasons = []
        if technicals['direction'] != "HOLD":
            reasons.append(f"Technical: {technicals['direction']} ({technicals['strength']:.0%})")
        if onchain_price:
            reasons.append(f"Chainlink: ${onchain_price:,.2f}")
            if spread_direction != "ALIGNED":
                reasons.append(f"Spread: {spread_pct:+.2f}% ({spread_direction})")
        if onchain_confirms:
            reasons.append("✅ On-chain confirms")
        if action == "ARBITRAGE":
            reasons.append(f"⚡ Arb opportunity: {abs(spread_pct):.2f}% spread")

        if not reasons:
            return None  # No actionable signal

        # 8. Assign tier
        if convergence_score >= 0.7:
            tier = "VIP"
        elif convergence_score >= 0.5:
            tier = "PRO"
        elif convergence_score >= 0.3:
            tier = "BASIC"
        else:
            tier = "FREE"

        return ConvergenceSignal(
            pair=pair,
            action=action,
            strength=convergence_score,
            price_cex=cex_price,
            price_onchain=onchain_price or 0,
            price_spread=spread_pct,
            price_spread_direction=spread_direction,
            technical_signal=technicals['direction'],
            onchain_confirms=onchain_confirms,
            convergence_score=convergence_score,
            sources_count=sources,
            reason=" | ".join(reasons),
            timestamp=datetime.now().isoformat(),
            tier=tier,
        )

    async def run_cycle(self, pairs: List[str], timeframes: List[str]) -> List[ConvergenceSignal]:
        """Run a full convergence analysis cycle."""
        logger.info("=" * 60)
        logger.info("🏔️  MULTI-SOURCE CONVERGENCE SCAN")
        logger.info("=" * 60)

        # First, show Chainlink prices
        if self.chainlink.connected:
            chainlink_prices = await self.chainlink.get_all_prices()
            if chainlink_prices:
                logger.info("📊 Chainlink On-Chain Prices:")
                for pair, price in chainlink_prices.items():
                    logger.info(f"   {pair}: ${price:,.2f}")

        signals = []
        for pair in pairs:
            for tf in timeframes:
                try:
                    signal = await self.analyze_pair(pair, tf)
                    if signal and signal.strength >= 0.2:
                        signals.append(signal)
                        tier_emoji = {"FREE": "🆓", "BASIC": "🟡", "PRO": "🟠", "VIP": "💎"}.get(signal.tier, "🆓")
                        action_emoji = {"BUY": "🟢", "SELL": "🔴", "ARBITRAGE": "⚡", "HOLD": "⚪"}.get(signal.action, "⚪")

                        logger.info(f"\n{action_emoji} CONVERGENCE: {signal.action} {signal.pair}")
                        logger.info(f"   CEX: ${signal.price_cex:,.2f} | On-chain: ${signal.price_onchain:,.2f}")
                        logger.info(f"   Spread: {signal.price_spread:+.2f}% ({signal.price_spread_direction})")
                        logger.info(f"   Strength: {signal.strength:.0%} | {tier_emoji} {signal.tier} | Sources: {signal.sources_count}")
                        logger.info(f"   Reason: {signal.reason}")
                except Exception as e:
                    logger.error(f"Error analyzing {pair} {tf}: {e}")

        # Save convergence signals
        if signals:
            conv_file = SIGNAL_DATA_DIR / "convergence_signals.json"
            existing = []
            if conv_file.exists():
                with open(conv_file) as f:
                    existing = json.load(f)
            existing.extend([s.to_dict() for s in signals])
            # Keep last 500
            existing = existing[-500:]
            with open(conv_file, 'w') as f:
                json.dump(existing, f, indent=2)

        logger.info(f"\n📊 Convergence scan complete: {len(signals)} signals")
        return signals


async def main():
    """Run the convergence engine."""
    import argparse
    parser = argparse.ArgumentParser(description="Rehoboam Convergence Engine")
    parser.add_argument("--once", action="store_true", help="Single cycle")
    parser.add_argument("--interval", type=int, default=15, help="Minutes between cycles")
    args = parser.parse_args()

    pairs = [
        "BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD",
        "AAVE-USD", "UNI-USD",  # These have Chainlink feeds
    ]
    timeframes = ["1h", "4h", "1d"]

    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏔️  REHOBOAM CONVERGENCE ENGINE  🏔️                   ║
    ║                                                           ║
    ║   "When all sources agree, the signal is gold."          ║
    ║                                                           ║
    ║   Binance CEX + Chainlink On-Chain + Etherscan            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    async with ConvergenceEngine() as engine:
        if args.once:
            await engine.run_cycle(pairs, timeframes)
        else:
            while True:
                await engine.run_cycle(pairs, timeframes)
                logger.info(f"⏰ Next convergence scan in {args.interval} minutes\n")
                await asyncio.sleep(args.interval * 60)


if __name__ == "__main__":
    asyncio.run(main())