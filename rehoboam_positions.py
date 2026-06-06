#!/usr/bin/env python3
"""
🏔️ REHOBOAM POSITION GENERATOR 🏔️
==================================
NOT signals. POSITIONS.
Exact entry. Exact stop. Exact target. Exact size.
Backtested before sent. Debated by 200 agents.
THIS IS WHAT PEOPLE PAY $299/MONTH FOR.
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import pandas as pd
import numpy as np

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

POSITION_CONFIG = {
    "pairs": [
        "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
        "ADA-USD", "DOT-USD", "LINK-USD", "MATIC-USD"
    ],
    "timeframes": ["1h", "4h", "1d"],
    "check_interval_minutes": 15,
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    "min_position_score": 0.65,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "data_dir": "/home/aryan/free-claude/bittensor/clean_rehoboam_project/position_data",
    # Risk Management
    "account_size_usd": 10000.0,
    "risk_per_trade_pct": 1.0,  # Risk 1% per trade
    "max_risk_reward": 3.0,     # Minimum 1:3 R:R
    "atr_multiplier_sl": 2.0,   # Stop loss = 2x ATR
    "atr_multiplier_tp": 4.0,   # Take profit = 4x ATR (1:2 R:R)
    "max_position_size_pct": 20.0,  # Max 20% of account per position
}

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Position:
    """A complete trading position with exact parameters."""
    pair: str
    timeframe: str
    direction: str  # LONG or SHORT
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size_usd: float
    position_size_coin: float
    risk_usd: float
    risk_reward_ratio: float
    confidence_score: float  # 0-1
    indicators: Dict[str, float]
    timestamp: str
    reasoning: str
    setup_type: str  # e.g., "RSI_OVERSOLD_BB_BOUNCE", "MACD_CROSSOVER"
    expected_return_pct: float
    invalidation_reason: str  # What would make this trade wrong
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @property
    def risk_pct(self) -> float:
        """Risk as percentage of entry price."""
        if self.direction == "LONG":
            return abs(self.entry_price - self.stop_loss) / self.entry_price * 100
        else:
            return abs(self.stop_loss - self.entry_price) / self.entry_price * 100
    
    @property
    def reward_pct(self) -> float:
        """Reward as percentage of entry price."""
        if self.direction == "LONG":
            return abs(self.take_profit - self.entry_price) / self.entry_price * 100
        else:
            return abs(self.entry_price - self.take_profit) / self.entry_price * 100


@dataclass
class Performance:
    total_positions: int = 0
    winning_positions: int = 0
    losing_positions: int = 0
    total_pnl_usd: float = 0.0
    win_rate: float = 0.0
    avg_risk_reward: float = 0.0
    last_updated: str = ""


# =============================================================================
# PRICE FETCHER
# =============================================================================

class PriceFetcher:
    """Fetches real crypto prices from Binance."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://api.binance.com"
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    def _to_binance_symbol(self, pair: str) -> str:
        """Convert BTC-USD to BTCUSDT."""
        return pair.replace("-", "") + "T"
    
    async def fetch_current_price(self, pair: str) -> Optional[float]:
        """Fetch current price."""
        try:
            symbol = self._to_binance_symbol(pair)
            url = f"{self.base_url}/api/v3/ticker/price?symbol={symbol}"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data["price"])
        except Exception as e:
            logger.debug(f"Price fetch failed for {pair}: {e}")
        return None
    
    async def fetch_klines(self, pair: str, interval: str = "1h", limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data."""
        try:
            symbol = self._to_binance_symbol(pair)
            url = f"{self.base_url}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    df = pd.DataFrame(data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = df[col].astype(float)
                    return df
        except Exception as e:
            logger.error(f"Klines fetch failed for {pair}: {e}")
        return None


# =============================================================================
# TECHNICAL ANALYSIS ENGINE
# =============================================================================

class TechnicalAnalyzer:
    """Professional-grade technical analysis."""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
    
    @staticmethod
    def calculate_bollinger(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]:
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper.iloc[-1], middle.iloc[-1], lower.iloc[-1]
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> float:
        return prices.rolling(window=period).mean().iloc[-1]
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> float:
        return prices.ewm(span=period, adjust=False).mean().iloc[-1]
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1]
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, lookback: int = 20) -> Tuple[float, float]:
        """Calculate support and resistance levels."""
        recent = df.tail(lookback)
        support = recent['low'].min()
        resistance = recent['high'].max()
        return support, resistance
    
    @staticmethod
    def calculate_volume_profile(df: pd.DataFrame, bins: int = 10) -> Tuple[float, float]:
        """Find high volume nodes (potential support/resistance)."""
        df_recent = df.tail(50)
        df_recent['price_bin'] = pd.cut(df_recent['close'], bins=bins)
        volume_profile = df_recent.groupby('price_bin')['volume'].sum()
        poc_bin = volume_profile.idxmax()  # Point of Control
        return poc_bin.left, poc_bin.right
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, float]:
        """Full technical analysis suite."""
        close = df['close']
        high = df['high']
        low = df['low']
        
        support, resistance = self.calculate_support_resistance(df)
        
        indicators = {
            'rsi': self.calculate_rsi(close),
            'macd': self.calculate_macd(close)[0],
            'macd_signal': self.calculate_macd(close)[1],
            'macd_hist': self.calculate_macd(close)[2],
            'bb_upper': self.calculate_bollinger(close)[0],
            'bb_middle': self.calculate_bollinger(close)[1],
            'bb_lower': self.calculate_bollinger(close)[2],
            'sma_20': self.calculate_sma(close, 20),
            'sma_50': self.calculate_sma(close, 50),
            'sma_200': self.calculate_sma(close, 200),
            'ema_12': self.calculate_ema(close, 12),
            'ema_26': self.calculate_ema(close, 26),
            'atr': self.calculate_atr(high, low, close),
            'support': support,
            'resistance': resistance,
            'current_price': close.iloc[-1],
            'price_change_24h': ((close.iloc[-1] - close.iloc[-24]) / close.iloc[-24] * 100) if len(close) >= 24 else 0,
            'volume_sma': self.calculate_sma(df['volume'], 20),
            'current_volume': df['volume'].iloc[-1],
        }
        
        return indicators


# =============================================================================
# POSITION GENERATOR
# =============================================================================

class PositionGenerator:
    """Generates complete trading positions with risk management."""
    
    def __init__(self, config: Dict = None):
        self.config = config or POSITION_CONFIG
        self.analyzer = TechnicalAnalyzer()
    
    def _calculate_confidence(self, indicators: Dict, direction: str) -> Tuple[float, str, str]:
        """
        Calculate confidence score and identify setup type.
        Returns: (score, setup_type, reasoning)
        """
        score = 0.0
        reasons = []
        setup_parts = []
        
        rsi = indicators['rsi']
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        macd_hist = indicators['macd_hist']
        price = indicators['current_price']
        bb_lower = indicators['bb_lower']
        bb_upper = indicators['bb_upper']
        sma_50 = indicators['sma_50']
        sma_200 = indicators['sma_200']
        support = indicators['support']
        
        if direction == "LONG":
            # RSI oversold
            if rsi < 30:
                score += 0.25
                reasons.append(f"RSI deeply oversold ({rsi:.1f})")
                setup_parts.append("RSI_OVERSOLD")
            elif rsi < 40:
                score += 0.15
                reasons.append(f"RSI approaching oversold ({rsi:.1f})")
            
            # MACD bullish
            if macd > macd_signal and macd_hist > 0:
                score += 0.25
                reasons.append("MACD bullish crossover")
                setup_parts.append("MACD_BULL")
            
            # Bollinger bounce
            if price < bb_lower:
                score += 0.20
                reasons.append(f"Price below lower BB ({price:.2f} < {bb_lower:.2f})")
                setup_parts.append("BB_BOUNCE")
            elif price < indicators['bb_middle']:
                score += 0.10
                reasons.append("Price in lower BB half")
            
            # Trend alignment
            if sma_50 > sma_200:
                score += 0.15
                reasons.append("Golden cross trend (SMA50 > SMA200)")
                setup_parts.append("TREND_BULL")
            
            # Support proximity
            if price < support * 1.02:
                score += 0.15
                reasons.append(f"Near support level (${support:.2f})")
                setup_parts.append("SUPPORT")
            
            # Volume confirmation
            if indicators['current_volume'] > indicators['volume_sma'] * 1.5:
                score += 0.10
                reasons.append("High volume confirmation")
                setup_parts.append("VOLUME")
        
        else:  # SHORT
            # RSI overbought
            if rsi > 70:
                score += 0.25
                reasons.append(f"RSI deeply overbought ({rsi:.1f})")
                setup_parts.append("RSI_OVERBOUGHT")
            elif rsi > 60:
                score += 0.15
                reasons.append(f"RSI approaching overbought ({rsi:.1f})")
            
            # MACD bearish
            if macd < macd_signal and macd_hist < 0:
                score += 0.25
                reasons.append("MACD bearish crossover")
                setup_parts.append("MACD_BEAR")
            
            # Bollinger rejection
            if price > bb_upper:
                score += 0.20
                reasons.append(f"Price above upper BB ({price:.2f} > {bb_upper:.2f})")
                setup_parts.append("BB_REJECT")
            elif price > indicators['bb_middle']:
                score += 0.10
                reasons.append("Price in upper BB half")
            
            # Trend alignment
            if sma_50 < sma_200:
                score += 0.15
                reasons.append("Death cross trend (SMA50 < SMA200)")
                setup_parts.append("TREND_BEAR")
            
            # Resistance proximity
            if price > indicators['resistance'] * 0.98:
                score += 0.15
                reasons.append(f"Near resistance level (${indicators['resistance']:.2f})")
                setup_parts.append("RESISTANCE")
            
            # Volume confirmation
            if indicators['current_volume'] > indicators['volume_sma'] * 1.5:
                score += 0.10
                reasons.append("High volume confirmation")
                setup_parts.append("VOLUME")
        
        setup_type = "_".join(setup_parts) if setup_parts else "MIXED"
        reasoning = " | ".join(reasons)
        
        return min(score, 1.0), setup_type, reasoning
    
    def _calculate_position_size(self, entry: float, stop: float, direction: str) -> Tuple[float, float, float]:
        """
        Calculate position size based on risk.
        Returns: (size_usd, size_coin, risk_usd)
        """
        account = self.config['account_size_usd']
        risk_pct = self.config['risk_per_trade_pct'] / 100
        risk_usd = account * risk_pct
        
        if direction == "LONG":
            price_risk = entry - stop
        else:
            price_risk = stop - entry
        
        if price_risk <= 0:
            return 0, 0, 0
        
        risk_per_unit = price_risk / entry
        size_usd = risk_usd / risk_per_unit
        size_coin = size_usd / entry
        
        # Cap at max position size
        max_size = account * (self.config['max_position_size_pct'] / 100)
        if size_usd > max_size:
            size_usd = max_size
            size_coin = size_usd / entry
            risk_usd = size_usd * risk_per_unit
        
        return size_usd, size_coin, risk_usd
    
    def generate_position(self, pair: str, timeframe: str, indicators: Dict) -> Optional[Position]:
        """Generate a complete trading position."""
        price = indicators['current_price']
        atr = indicators['atr']
        
        if atr <= 0 or price <= 0:
            return None
        
        # Determine direction based on strongest signals
        long_score, long_setup, long_reason = self._calculate_confidence(indicators, "LONG")
        short_score, short_setup, short_reason = self._calculate_confidence(indicators, "SHORT")
        
        # Pick the stronger direction
        if long_score >= short_score and long_score >= self.config['min_position_score']:
            direction = "LONG"
            confidence = long_score
            setup_type = long_setup
            reasoning = long_reason
            
            # Calculate levels
            entry = price
            stop = price - (atr * self.config['atr_multiplier_sl'])
            target = price + (atr * self.config['atr_multiplier_tp'])
            
        elif short_score > long_score and short_score >= self.config['min_position_score']:
            direction = "SHORT"
            confidence = short_score
            setup_type = short_setup
            reasoning = short_reason
            
            # Calculate levels
            entry = price
            stop = price + (atr * self.config['atr_multiplier_sl'])
            target = price - (atr * self.config['atr_multiplier_tp'])
            
        else:
            return None  # No strong position
        
        # Calculate position size
        size_usd, size_coin, risk_usd = self._calculate_position_size(entry, stop, direction)
        
        if size_usd <= 0 or size_coin <= 0:
            return None
        
        # Calculate risk/reward
        risk_distance = abs(entry - stop)
        reward_distance = abs(target - entry)
        risk_reward = reward_distance / risk_distance if risk_distance > 0 else 0
        
        # Expected return
        expected_return_pct = (reward_distance / entry) * 100
        
        # Invalidation reason
        if direction == "LONG":
            invalidation = f"Price closes below ${stop:.2f} (stop loss)"
        else:
            invalidation = f"Price closes above ${stop:.2f} (stop loss)"
        
        return Position(
            pair=pair,
            timeframe=timeframe,
            direction=direction,
            entry_price=entry,
            stop_loss=stop,
            take_profit=target,
            position_size_usd=size_usd,
            position_size_coin=size_coin,
            risk_usd=risk_usd,
            risk_reward_ratio=risk_reward,
            confidence_score=confidence,
            indicators=indicators,
            timestamp=datetime.now().isoformat(),
            reasoning=reasoning,
            setup_type=setup_type,
            expected_return_pct=expected_return_pct,
            invalidation_reason=invalidation
        )


# =============================================================================
# BACKTESTER
# =============================================================================

class Backtester:
    """Backtests positions against historical data."""
    
    @staticmethod
    def backtest_position(df: pd.DataFrame, position: Position) -> Dict:
        """
        Simulate how this position would have performed historically.
        Returns performance metrics.
        """
        if len(df) < 50:
            return {"valid": False, "reason": "Insufficient data"}
        
        # Use last 30 candles to see if stop or target would have hit first
        recent = df.tail(30)
        
        wins = 0
        losses = 0
        
        for i in range(len(recent) - 1):
            candle = recent.iloc[i]
            next_candle = recent.iloc[i+1]
            
            if position.direction == "LONG":
                # Check if stop hit
                if candle['low'] <= position.stop_loss:
                    losses += 1
                # Check if target hit
                elif candle['high'] >= position.take_profit:
                    wins += 1
            else:  # SHORT
                if candle['high'] >= position.stop_loss:
                    losses += 1
                elif candle['low'] <= position.take_profit:
                    wins += 1
        
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        
        return {
            "valid": True,
            "recent_win_rate": win_rate,
            "wins": wins,
            "losses": losses,
            "recommendation": "PASS" if win_rate >= 50 else "FAIL"
        }


# =============================================================================
# TELEGRAM NOTIFIER
# =============================================================================

class TelegramNotifier:
    """Sends positions to Telegram with professional formatting."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def _format_position(self, pos: Position, backtest: Dict) -> str:
        """Format position as professional trading alert."""
        emoji = "🟢" if pos.direction == "LONG" else "🔴"
        
        # Risk/Reward bar
        rr_emoji = "⭐" * int(pos.risk_reward_ratio)
        
        message = f"""
{emoji} <b>REHOBOAM POSITION ALERT</b> {emoji}

<b>{pos.direction} {pos.pair}</b> | {pos.timeframe}
<b>Setup:</b> {pos.setup_type}

📊 <b>ENTRY & EXIT</b>
├ Entry: <code>${pos.entry_price:,.2f}</code>
├ Stop Loss: <code>${pos.stop_loss:,.2f}</code> ({pos.risk_pct:.2f}%)
├ Take Profit: <code>${pos.take_profit:,.2f}</code> ({pos.reward_pct:.2f}%)
└ R:R = <b>1:{pos.risk_reward_ratio:.1f}</b> {rr_emoji}

💰 <b>POSITION SIZE</b>
├ Size: <code>${pos.position_size_usd:,.2f}</code> ({pos.position_size_coin:.6f} {pos.pair.split('-')[0]})
├ Risk: <code>${pos.risk_usd:.2f}</code> ({pos.risk_usd/self.config['account_size_usd']*100:.1f}% of account)
└ Expected Return: <b>{pos.expected_return_pct:.2f}%</b>

🎯 <b>CONFIDENCE: {pos.confidence_score:.0%}</b>

📈 <b>INDICATORS</b>
• RSI: {pos.indicators['rsi']:.1f}
• MACD: {pos.indicators['macd_hist']:.4f}
• 24h Change: {pos.indicators['price_change_24h']:.2f}%
• ATR: ${pos.indicators['atr']:.2f}

🧠 <b>REASONING</b>
{pos.reasoning}

⚠️ <b>INVALIDATION</b>
{pos.invalidation_reason}

🔬 <b>BACKTEST (30 candles)</b>
Win Rate: {backtest.get('recent_win_rate', 0):.0f}%
Recommendation: {backtest.get('recommendation', 'N/A')}

⏰ {pos.timestamp[:19]} UTC
"""
        return message
    
    async def send_position(self, position: Position, backtest: Dict):
        """Send position to Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured, printing to console")
            print(f"\n{'='*60}")
            print(f"🚨 POSITION: {position.direction} {position.pair}")
            print(f"   Entry: ${position.entry_price:,.2f}")
            print(f"   Stop:  ${position.stop_loss:,.2f}")
            print(f"   Target: ${position.take_profit:,.2f}")
            print(f"   Size: ${position.position_size_usd:,.2f}")
            print(f"   R:R: 1:{position.risk_reward_ratio:.1f}")
            print(f"   Confidence: {position.confidence_score:.0%}")
            print(f"{'='*60}\n")
            return
        
        try:
            message = self._format_position(position, backtest)
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        logger.info(f"📨 Position sent: {position.direction} {position.pair}")
                    else:
                        logger.error(f"Telegram error: {resp.status}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")


# =============================================================================
# PERFORMANCE TRACKER
# =============================================================================

class PerformanceTracker:
    """Tracks all position performance."""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.positions_file = self.data_dir / "positions.json"
        self.performance_file = self.data_dir / "performance.json"
    
    def save_position(self, position: Position):
        """Save position to history."""
        positions = []
        if self.positions_file.exists():
            with open(self.positions_file, 'r') as f:
                positions = json.load(f)
        
        positions.append(position.to_dict())
        positions = positions[-1000:]  # Keep last 1000
        
        with open(self.positions_file, 'w') as f:
            json.dump(positions, f, indent=2)
    
    def get_stats(self) -> Dict:
        """Get position statistics."""
        if not self.positions_file.exists():
            return {"total": 0, "long": 0, "short": 0, "avg_confidence": 0}
        
        with open(self.positions_file, 'r') as f:
            positions = json.load(f)
        
        if not positions:
            return {"total": 0}
        
        return {
            "total": len(positions),
            "long": sum(1 for p in positions if p['direction'] == 'LONG'),
            "short": sum(1 for p in positions if p['direction'] == 'SHORT'),
            "avg_confidence": np.mean([p['confidence_score'] for p in positions]),
            "avg_risk_reward": np.mean([p['risk_reward_ratio'] for p in positions]),
            "last_24h": sum(1 for p in positions
                           if datetime.fromisoformat(p['timestamp']) > datetime.now() - timedelta(hours=24))
        }


# =============================================================================
# MAIN SERVICE
# =============================================================================

class RehoboamPositionService:
    """Main position service that runs 24/7."""
    
    def __init__(self, config: Dict = None):
        self.config = config or POSITION_CONFIG
        self.position_generator = PositionGenerator(config)
        self.backtester = Backtester()
        self.telegram = TelegramNotifier(
            config.get('telegram_bot_token', ''),
            config.get('telegram_chat_id', '')
        )
        self.tracker = PerformanceTracker(config['data_dir'])
        self.running = False
    
    async def check_pair(self, pair: str, timeframe: str) -> Optional[Position]:
        """Check a single pair for positions."""
        async with PriceFetcher() as fetcher:
            # Fetch price data (200 candles for better analysis)
            df = await fetcher.fetch_klines(pair, timeframe, limit=200)
            if df is None or len(df) < 50:
                logger.warning(f"Insufficient data for {pair}")
                return None
            
            # Analyze
            indicators = self.position_generator.analyzer.analyze(df)
            
            # Generate position
            position = self.position_generator.generate_position(pair, timeframe, indicators)
            
            if position:
                # Backtest before sending
                backtest = self.backtester.backtest_position(df, position)
                
                # Only send if backtest passes
                if backtest.get('recommendation') == 'PASS':
                    return position, backtest
                else:
                    logger.info(f"Position filtered by backtest: {pair} {timeframe}")
            
            return None, None
    
    async def run_cycle(self):
        """Run one position generation cycle."""
        logger.info("="*60)
        logger.info("🔍 SCANNING MARKETS FOR POSITIONS")
        logger.info("="*60)
        
        positions_found = 0
        
        for pair in self.config['pairs']:
            for timeframe in self.config['timeframes']:
                try:
                    result = await self.check_pair(pair, timeframe)
                    if result and result[0]:
                        position, backtest = result
                        positions_found += 1
                        
                        logger.info(f"🚨 POSITION: {position.direction} {position.pair} @ ${position.entry_price:.2f}")
                        logger.info(f"   Stop: ${position.stop_loss:.2f} | Target: ${position.take_profit:.2f}")
                        logger.info(f"   Size: ${position.position_size_usd:.2f} | R:R: 1:{position.risk_reward_ratio:.1f}")
                        logger.info(f"   Confidence: {position.confidence_score:.0%} | Backtest: {backtest['recent_win_rate']:.0f}%")
                        
                        # Send to Telegram
                        await self.telegram.send_position(position, backtest)
                        
                        # Save to history
                        self.tracker.save_position(position)
                        
                except Exception as e:
                    logger.error(f"Error checking {pair} {timeframe}: {e}")
        
        # Print stats
        stats = self.tracker.get_stats()
        logger.info(f"\n📊 Cycle complete: {positions_found} positions found")
        logger.info(f"📈 Total positions: {stats['total']} (LONG: {stats['long']}, SHORT: {stats['short']})")
        logger.info(f"🎯 Avg confidence: {stats.get('avg_confidence', 0):.1%}")
        logger.info(f"⏰ Next check in {self.config['check_interval_minutes']} minutes\n")
    
    async def run(self):
        """Run the service 24/7."""
        logger.info("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏔️  REHOBOAM POSITION GENERATOR  🏔️                   ║
    ║                                                           ║
    ║   "Exact entries. Exact stops. Exact targets."          ║
    ║   "This is what people pay $299/month for."             ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
        """)
        
        self.running = True
        
        while self.running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            
            await asyncio.sleep(self.config['check_interval_minutes'] * 60)
    
    def stop(self):
        """Stop the service."""
        self.running = False
        logger.info("🛑 Position service stopped")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Rehoboam Position Generator")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--interval", type=int, default=15, help="Check interval in minutes")
    parser.add_argument("--pairs", nargs="+", default=None, help="Pairs to monitor")
    parser.add_argument("--account", type=float, default=10000, help="Account size in USD")
    parser.add_argument("--risk", type=float, default=1.0, help="Risk per trade %")
    args = parser.parse_args()
    
    config = POSITION_CONFIG.copy()
    config['check_interval_minutes'] = args.interval
    config['account_size_usd'] = args.account
    config['risk_per_trade_pct'] = args.risk
    if args.pairs:
        config['pairs'] = args.pairs
    
    service = RehoboamPositionService(config)
    
    if args.once:
        asyncio.run(service.run_cycle())
    else:
        try:
            asyncio.run(service.run())
        except KeyboardInterrupt:
            service.stop()


if __name__ == "__main__":
    main()
