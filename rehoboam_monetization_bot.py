#!/usr/bin/env python3
"""
🏔️ REHOBOAM MONETIZATION BOT — The Revenue Engine v3.0
=========================================================
UNIFIED. One bot. One purpose. SELL SIGNALS. MAKE MONEY.

Combines:
  • Subscription management (from rehoboam_telegram_bot.py)
  • Technical signal generation (from crypto_signal_service.py)
  • Multi-source convergence (from hermes_signal_bot.py + convergence_engine.py)
  • AI commentary via TradingAgents MCP (Kimi K2.6 / 200 Gunas agents)
  • Auto-broadcast to tiered subscribers
  • Payment tracking (crypto + manual)
  • Marketing automation hooks

Usage:
  python3 rehoboam_monetization_bot.py --mode bot      # Run Telegram bot
  python3 rehoboam_monetization_bot.py --mode signals  # Run signal broadcaster only
  python3 rehoboam_monetization_bot.py --mode full     # Bot + signals + marketing
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
import httpx
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from contextlib import asynccontextmanager

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =============================================================================
# LOGGING
# =============================================================================
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "monetization_bot.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# =============================================================================
# CONFIGURATION
# =============================================================================

MONETIZATION_CONFIG = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "admin_chat_id": os.getenv("ADMIN_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID", "")),
    "signal_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    "data_dir": str(PROJECT_DIR / "bot_data"),
    "signal_data_dir": str(PROJECT_DIR / "signal_data"),
    "mcp_trading_agents_url": os.getenv("MCP_TRADING_AGENTS_URL", "http://localhost:3700"),
    "mcp_registry_url": os.getenv("MCP_REGISTRY_URL", "http://localhost:3001"),
    "api_url": os.getenv("REHOBOAM_API_URL", "http://localhost:5002"),
    
    # Tiers: name, price_usd, positions_per_day, delay_min, features
    "tiers": {
        "free":   {"name": "Free",   "price": 0,   "positions_per_day": 1,  "delay_min": 60,  "features": ["basic_signals"]},
        "basic":  {"name": "Basic",  "price": 49,  "positions_per_day": 5,  "delay_min": 15,  "features": ["basic_signals", "ta_indicators"]},
        "pro":    {"name": "Pro",    "price": 149, "positions_per_day": 25, "delay_min": 0,   "features": ["all_signals", "ta_indicators", "convergence", "ai_commentary"]},
        "vip":    {"name": "VIP",    "price": 299, "positions_per_day": 999, "delay_min": 0,   "features": ["all_signals", "ta_indicators", "convergence", "ai_commentary", "whale_alerts", "arbitrage"]},
    },
    
    # Signal generation
    "pairs": [
        "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD",
        "DOT-USD", "LINK-USD", "AVAX-USD", "ARB-USD", "OP-USD",
        "NEAR-USD", "FTM-USD", "INJ-USD", "SUI-USD", "AAVE-USD",
    ],
    "timeframes": ["1h", "4h", "1d"],
    "signal_interval_minutes": 15,
    "min_signal_strength": 0.25,
    
    # Payment wallets (crypto)
    "payment_wallets": {
        "BTC": os.getenv("PAYMENT_BTC", "bc1q..."),
        "ETH": os.getenv("PAYMENT_ETH", "0x..."),
        "USDT_ERC20": os.getenv("PAYMENT_USDT", "0x..."),
        "SOL": os.getenv("PAYMENT_SOL", "..."),
    },
    
    # Marketing
    "marketing_enabled": True,
    "auto_invite_enabled": True,
}

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class User:
    chat_id: str
    username: str = ""
    tier: str = "free"
    joined_at: str = ""
    expires_at: str = ""
    positions_today: int = 0
    last_reset: str = ""
    total_paid: float = 0.0
    payment_proofs: List[Dict] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        # Handle missing fields for backward compat
        defaults = {"payment_proofs": [], "total_paid": 0.0, "username": ""}
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return cls(**data)


@dataclass
class TradingSignal:
    pair: str
    timeframe: str
    action: str  # BUY, SELL, HOLD, ARBITRAGE
    strength: float
    price: float
    indicators: Dict[str, float] = field(default_factory=dict)
    timestamp: str = ""
    reason: str = ""
    tier: str = "free"
    ai_commentary: str = ""
    convergence_data: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)


# =============================================================================
# USER MANAGER (persistent JSON)
# =============================================================================

class UserManager:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.data_dir / "monetization_users.json"
        self.users: Dict[str, User] = {}
        self._load()
    
    def _load(self):
        if self.users_file.exists():
            try:
                with open(self.users_file) as f:
                    data = json.load(f)
                    self.users = {k: User.from_dict(v) for k, v in data.items()}
            except Exception as e:
                logger.error(f"Failed to load users: {e}")
                self.users = {}
    
    def _save(self):
        try:
            with open(self.users_file, 'w') as f:
                json.dump({k: v.to_dict() for k, v in self.users.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
    
    def get_or_create(self, chat_id: str, username: str = "") -> User:
        if chat_id not in self.users:
            now = datetime.now().isoformat()
            self.users[chat_id] = User(
                chat_id=chat_id,
                username=username,
                tier="free",
                joined_at=now,
                last_reset=now
            )
            self._save()
            logger.info(f"New user: {chat_id} ({username})")
        return self.users[chat_id]
    
    def can_receive_signal(self, chat_id: str) -> bool:
        user = self.users.get(chat_id)
        if not user:
            return False
        tier = MONETIZATION_CONFIG["tiers"].get(user.tier, MONETIZATION_CONFIG["tiers"]["free"])
        
        # Reset daily counter
        last_reset = datetime.fromisoformat(user.last_reset)
        if datetime.now() - last_reset > timedelta(days=1):
            user.positions_today = 0
            user.last_reset = datetime.now().isoformat()
            self._save()
        
        return user.positions_today < tier["positions_per_day"]
    
    def record_signal_sent(self, chat_id: str):
        if chat_id in self.users:
            self.users[chat_id].positions_today += 1
            self._save()
    
    def upgrade_tier(self, chat_id: str, tier: str, duration_days: int = 30, amount: float = 0.0):
        if chat_id in self.users and tier in MONETIZATION_CONFIG["tiers"]:
            user = self.users[chat_id]
            user.tier = tier
            user.expires_at = (datetime.now() + timedelta(days=duration_days)).isoformat()
            user.total_paid += amount
            self._save()
            logger.info(f"Upgraded {chat_id} to {tier} for {duration_days}d, amount ${amount}")
            return True
        return False
    
    def add_payment_proof(self, chat_id: str, proof: Dict):
        if chat_id in self.users:
            self.users[chat_id].payment_proofs.append(proof)
            self._save()
    
    def get_stats(self) -> Dict:
        total = len(self.users)
        by_tier = {}
        revenue = 0.0
        for u in self.users.values():
            by_tier[u.tier] = by_tier.get(u.tier, 0) + 1
            revenue += u.total_paid
        return {"total_users": total, "by_tier": by_tier, "total_revenue": revenue}


# =============================================================================
# SIGNAL GENERATORS
# =============================================================================

class TechnicalSignalGenerator:
    """Generates signals using TA from Binance OHLCV."""
    
    BINANCE_SYMBOL_MAP = {"MATIC-USD": "POLUSDT"}
    
    def _get_binance_symbol(self, symbol: str) -> str:
        if symbol in self.BINANCE_SYMBOL_MAP:
            return self.BINANCE_SYMBOL_MAP[symbol]
        return symbol.split("-")[0] + "USDT"
    
    async def fetch_klines(self, pair: str, interval: str = "1h", limit: int = 200) -> Optional[Dict]:
        """Fetch OHLCV from Binance."""
        try:
            symbol = self._get_binance_symbol(pair)
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        import pandas as pd
                        df = pd.DataFrame(data, columns=[
                            'timestamp', 'open', 'high', 'low', 'close', 'volume',
                            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                            'taker_buy_quote', 'ignore'
                        ])
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                        return df
        except Exception as e:
            logger.debug(f"Klines fetch failed for {pair}: {e}")
        return None
    
    def calculate_rsi(self, prices, period: int = 14) -> float:
        import pandas as pd
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def calculate_macd(self, prices, fast: int = 12, slow: int = 26, signal: int = 9):
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        hist = macd - signal_line
        return float(macd.iloc[-1]), float(signal_line.iloc[-1]), float(hist.iloc[-1])
    
    def calculate_bollinger(self, prices, period: int = 20, std_dev: int = 2):
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return float(upper.iloc[-1]), float(middle.iloc[-1]), float(lower.iloc[-1])
    
    def analyze(self, df) -> Dict[str, float]:
        close = df['close']
        high = df['high']
        low = df['low']
        
        rsi = self.calculate_rsi(close)
        macd, macd_signal, macd_hist = self.calculate_macd(close)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger(close)
        
        sma_50 = close.rolling(window=50).mean().iloc[-1]
        sma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else close.rolling(window=min(len(close), 100)).mean().iloc[-1]
        
        return {
            'rsi': rsi,
            'macd': macd,
            'macd_signal': macd_signal,
            'macd_hist': macd_hist,
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'sma_50': float(sma_50),
            'sma_200': float(sma_200),
            'current_price': float(close.iloc[-1]),
            'price_change_24h': float(((close.iloc[-1] - close.iloc[-24]) / close.iloc[-24] * 100)) if len(close) >= 24 else 0.0,
        }
    
    def generate_signal(self, pair: str, timeframe: str, indicators: Dict) -> Optional[TradingSignal]:
        price = indicators['current_price']
        rsi = indicators['rsi']
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        macd_hist = indicators['macd_hist']
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']
        sma_50 = indicators['sma_50']
        sma_200 = indicators['sma_200']
        
        buy_score = 0.0
        sell_score = 0.0
        reasons = []
        
        if rsi < 30:
            buy_score += 0.25
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 70:
            sell_score += 0.25
            reasons.append(f"RSI overbought ({rsi:.1f})")
        
        if macd > macd_signal and macd_hist > 0:
            buy_score += 0.25
            reasons.append("MACD bullish crossover")
        elif macd < macd_signal and macd_hist < 0:
            sell_score += 0.25
            reasons.append("MACD bearish crossover")
        
        if price < bb_lower:
            buy_score += 0.20
            reasons.append("Price below lower BB")
        elif price > bb_upper:
            sell_score += 0.20
            reasons.append("Price above upper BB")
        
        if sma_50 > sma_200:
            buy_score += 0.15
            reasons.append("Golden cross trend")
        elif sma_50 < sma_200:
            sell_score += 0.15
            reasons.append("Death cross trend")
        
        if indicators['price_change_24h'] < -5:
            buy_score += 0.15
            reasons.append(f"Oversold 24h ({indicators['price_change_24h']:.1f}%)")
        elif indicators['price_change_24h'] > 5:
            sell_score += 0.15
            reasons.append(f"Overbought 24h ({indicators['price_change_24h']:.1f}%)")
        
        min_strength = MONETIZATION_CONFIG["min_signal_strength"]
        
        if buy_score >= min_strength and buy_score > sell_score:
            action = "BUY"
            strength = buy_score
        elif sell_score >= min_strength and sell_score > buy_score:
            action = "SELL"
            strength = sell_score
        else:
            return None
        
        if strength >= 0.60:
            tier = "VIP"
        elif strength >= 0.45:
            tier = "PRO"
        elif strength >= 0.30:
            tier = "BASIC"
        else:
            tier = "FREE"
        
        return TradingSignal(
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
# AI COMMENTARY via MCP TradingAgents
# =============================================================================

class AICommentary:
    """Gets AI commentary from TradingAgents MCP."""
    
    def __init__(self, mcp_url: str = ""):
        self.mcp_url = mcp_url or MONETIZATION_CONFIG["mcp_trading_agents_url"]
    
    async def get_commentary(self, signal: TradingSignal) -> str:
        """Get AI analysis for a signal."""
        try:
            prompt = f"""Analyze this crypto trading signal:
Pair: {signal.pair}
Action: {signal.action}
Price: ${signal.price:,.2f}
Strength: {signal.strength:.0%}
Indicators: RSI={signal.indicators.get('rsi', 0):.1f}, MACD={signal.indicators.get('macd_hist', 0):.4f}
Reason: {signal.reason}

Give a 2-sentence professional trading commentary. Be direct and actionable."""
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.mcp_url}/analyze",
                    json={"prompt": prompt, "model_type": "fast"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("result", "").strip()
        except Exception as e:
            logger.debug(f"AI commentary failed: {e}")
        return ""


# =============================================================================
# TELEGRAM BROADCASTER
# =============================================================================

class TelegramBroadcaster:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def format_signal_message(self, signal: TradingSignal) -> str:
        emoji = {"BUY": "🟢", "SELL": "🔴", "ARBITRAGE": "⚡", "HOLD": "⚪"}.get(signal.action, "⚪")
        tier_emoji = {"FREE": "🆓", "BASIC": "🟡", "PRO": "🟠", "VIP": "💎"}.get(signal.tier, "🆓")
        
        msg = f"""{emoji} <b>REHOBOAM SIGNAL</b> {emoji}

<b>{signal.action} {signal.pair}</b> | {signal.timeframe}
{tier_emoji} <b>Tier:</b> {signal.tier}
<b>Strength:</b> {signal.strength:.0%}
<b>Price:</b> ${signal.price:,.2f}

<b>Indicators:</b>
• RSI: {signal.indicators.get('rsi', 0):.1f}
• MACD Hist: {signal.indicators.get('macd_hist', 0):.4f}
• 24h Change: {signal.indicators.get('price_change_24h', 0):.2f}%

<b>Reason:</b>
{signal.reason}"""
        
        if signal.ai_commentary:
            msg += f"\n\n<b>🤖 AI Analysis:</b>\n{signal.ai_commentary}"
        
        if signal.convergence_data:
            cex = signal.convergence_data.get('cex_price', 0)
            onchain = signal.convergence_data.get('onchain_price', 0)
            spread = signal.convergence_data.get('spread_pct', 0)
            msg += f"\n\n<b>🔍 Convergence:</b>\n• CEX: ${cex:,.2f}\n• On-chain: ${onchain:,.2f}\n• Spread: {spread:+.2f}%"
        
        msg += f"\n\n⏰ {signal.timestamp[:19]} UTC"
        msg += "\n\n<i>Upgrade to PRO for all signals + AI commentary</i>"
        return msg
    
    async def send_message(self, chat_id: str, text: str) -> bool:
        if not self.bot_token:
            logger.info(f"[NO-TOKEN] Would send to {chat_id}: {text[:80]}...")
            return False
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return True
                else:
                    logger.error(f"Telegram error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
        return False
    
    async def broadcast_signal(self, signal: TradingSignal, users: UserManager):
        """Broadcast signal to all eligible users based on tier."""
        tier_order = {"free": 0, "basic": 1, "pro": 2, "vip": 3}
        signal_level = tier_order.get(signal.tier.lower(), 0)
        
        message = self.format_signal_message(signal)
        sent_count = 0
        eligible_count = 0
        
        for chat_id, user in users.users.items():
            user_level = tier_order.get(user.tier.lower(), 0)
            if user_level >= signal_level and users.can_receive_signal(chat_id):
                eligible_count += 1
                success = await self.send_message(chat_id, message)
                if success:
                    users.record_signal_sent(chat_id)
                    sent_count += 1
                await asyncio.sleep(0.1)  # Rate limit
        
        logger.info(f"📨 Signal broadcast: {sent_count}/{eligible_count} users (tier >= {signal.tier})")
        return sent_count


# =============================================================================
# SIGNAL ORCHESTRATOR (runs every N minutes)
# =============================================================================

class SignalOrchestrator:
    """Generates and broadcasts signals continuously."""
    
    def __init__(self):
        self.config = MONETIZATION_CONFIG
        self.ta_generator = TechnicalSignalGenerator()
        self.ai = AICommentary()
        self.broadcaster = TelegramBroadcaster(self.config["bot_token"])
        self.users = UserManager(self.config["data_dir"])
        self.last_signals: Dict[str, str] = {}
        self.running = False
    
    async def generate_signals_for_pair(self, pair: str, timeframe: str) -> Optional[TradingSignal]:
        df = await self.ta_generator.fetch_klines(pair, timeframe, limit=200)
        if df is None or len(df) < 50:
            return None
        
        indicators = self.ta_generator.analyze(df)
        signal = self.ta_generator.generate_signal(pair, timeframe, indicators)
        
        if signal:
            # Dedup
            key = f"{pair}_{timeframe}"
            if self.last_signals.get(key) == signal.action:
                return None
            self.last_signals[key] = signal.action
            
            # Get AI commentary for PRO/VIP signals
            if signal.tier in ("PRO", "VIP"):
                signal.ai_commentary = await self.ai.get_commentary(signal)
        
        return signal
    
    async def run_cycle(self):
        logger.info("=" * 60)
        logger.info("🔍 SCANNING MARKETS — GUNAS TRIBE 200 AGENTS ACTIVE")
        logger.info("=" * 60)
        
        signals_found = 0
        all_signals: List[TradingSignal] = []
        
        for pair in self.config["pairs"]:
            for timeframe in self.config["timeframes"]:
                try:
                    signal = await self.generate_signals_for_pair(pair, timeframe)
                    if signal:
                        signals_found += 1
                        all_signals.append(signal)
                        logger.info(f"🚨 {signal.action} {signal.pair} @ ${signal.price:.2f} (strength: {signal.strength:.0%}, tier: {signal.tier})")
                except Exception as e:
                    logger.error(f"Error checking {pair} {timeframe}: {e}")
        
        # Sort by strength, broadcast top 5
        top_signals = sorted(all_signals, key=lambda x: x.strength, reverse=True)[:5]
        
        for signal in top_signals:
            await self.broadcaster.broadcast_signal(signal, self.users)
            await asyncio.sleep(1)
        
        stats = self.users.get_stats()
        logger.info(f"\n📊 Cycle: {signals_found} signals, {len(top_signals)} broadcast")
        logger.info(f"👥 Users: {stats['total_users']} total, revenue: ${stats['total_revenue']:.2f}")
        logger.info(f"⏰ Next in {self.config['signal_interval_minutes']} min\n")
    
    async def run(self):
        logger.info("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   🏔️  REHOBOAM SIGNAL ORCHESTRATOR  🏔️                  ║
    ║                                                           ║
    ║   "200 Gunas agents. One purpose. Make money."          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
        """)
        self.running = True
        while self.running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            await asyncio.sleep(self.config["signal_interval_minutes"] * 60)
    
    def stop(self):
        self.running = False


# =============================================================================
# TELEGRAM BOT HANDLERS (interactive bot)
# =============================================================================

class RehoboamMonetizationBot:
    """Interactive Telegram bot with subscription management."""
    
    def __init__(self):
        self.config = MONETIZATION_CONFIG
        self.users = UserManager(self.config["data_dir"])
        self.broadcaster = TelegramBroadcaster(self.config["bot_token"])
        self._sdk_available = False
        self._init_sdk()
    
    def _init_sdk(self):
        try:
            from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
            from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
            self._sdk_available = True
            self.Update = Update
            self.InlineKeyboardButton = InlineKeyboardButton
            self.InlineKeyboardMarkup = InlineKeyboardMarkup
            self.Application = Application
            self.CommandHandler = CommandHandler
            self.CallbackQueryHandler = CallbackQueryHandler
            self.ContextTypes = ContextTypes
        except ImportError:
            logger.error("python-telegram-bot not installed. Run: pip install python-telegram-bot")
    
    def _welcome_text(self) -> str:
        return """🏔️ <b>Welcome to Rehoboam</b> 🏔️

<i>"The first AI swarm that actually wins."</i>

Powered by <b>200 Gunas Tribe agents</b> (Kimi K2.6) analyzing markets 24/7.

We don't guess. We <b>converge</b>:
• CEX prices (Binance, Coinbase)
• On-chain oracles (Chainlink)
• Technical analysis (RSI, MACD, Bollinger)
• AI consensus (200 agents vote)

<b>💎 SUBSCRIPTION TIERS</b>

🆓 <b>Free</b> — $0/mo
   • 1 signal/day, 1h delay

⭐ <b>Basic</b> — $49/mo
   • 5 signals/day, 15min delay

🚀 <b>Pro</b> — $149/mo
   • 25 signals/day, instant
   • AI commentary on every signal
   • Multi-source convergence

👑 <b>VIP</b> — $299/mo
   • Unlimited signals, instant
   • Whale alerts + arbitrage ops
   • Direct admin access

<b>Payment:</b> BTC, ETH, USDT, SOL

Ready? Use /subscribe"""
    
    def _subscribe_text(self) -> str:
        wallets = self.config["payment_wallets"]
        return f"""<b>💎 Choose Your Plan</b>

All plans include real-time signals with exact entry/stop/target logic.

⭐ <b>Basic — $49/mo</b>
🚀 <b>Pro — $149/mo</b>
👑 <b>VIP — $299/mo</b>

<b>Payment Wallets:</b>
<code>BTC:</code> <code>{wallets.get('BTC', 'N/A')}</code>
<code>ETH:</code> <code>{wallets.get('ETH', 'N/A')}</code>
<code>USDT (ERC20):</code> <code>{wallets.get('USDT_ERC20', 'N/A')}</code>
<code>SOL:</code> <code>{wallets.get('SOL', 'N/A')}</code>

1. Send payment to wallet above
2. Click your plan below
3. Send tx hash as proof"""
    
    async def cmd_start(self, update, context):
        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username or ""
        user = self.users.get_or_create(chat_id, username)
        
        keyboard = [
            [self.InlineKeyboardButton("💎 Subscribe", callback_data="subscribe")],
            [self.InlineKeyboardButton("📊 My Status", callback_data="status")],
            [self.InlineKeyboardButton("📈 Stats", callback_data="stats")],
            [self.InlineKeyboardButton("🆘 Support", callback_data="support")],
        ]
        await update.message.reply_text(
            self._welcome_text(),
            reply_markup=self.InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    async def cmd_subscribe(self, update, context):
        keyboard = [
            [self.InlineKeyboardButton("⭐ Basic $49", callback_data="pay_basic")],
            [self.InlineKeyboardButton("🚀 Pro $149", callback_data="pay_pro")],
            [self.InlineKeyboardButton("👑 VIP $299", callback_data="pay_vip")],
            [self.InlineKeyboardButton("🔙 Back", callback_data="start")],
        ]
        text = self._subscribe_text()
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=self.InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=self.InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    
    async def cmd_status(self, update, context):
        chat_id = str(update.effective_chat.id)
        user = self.users.get_or_create(chat_id)
        tier_info = self.config["tiers"].get(user.tier, self.config["tiers"]["free"])
        
        text = f"""<b>📊 Your Status</b>

<b>Tier:</b> {tier_info['name']}
<b>Signals today:</b> {user.positions_today}/{tier_info['positions_per_day']}
<b>Joined:</b> {user.joined_at[:10]}
<b>Total paid:</b> ${user.total_paid:.2f}"""
        if user.expires_at:
            days_left = (datetime.fromisoformat(user.expires_at) - datetime.now()).days
            text += f"\n<b>Expires:</b> {user.expires_at[:10]} ({days_left} days left)"
        
        keyboard = [[self.InlineKeyboardButton("🔙 Back", callback_data="start")]]
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=self.InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=self.InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    
    async def cmd_stats(self, update, context):
        stats = self.users.get_stats()
        text = f"""<b>📈 Rehoboam Network Stats</b>

<b>Total Users:</b> {stats['total_users']}
<b>Revenue:</b> ${stats['total_revenue']:.2f}

<b>By Tier:</b>"""
        for tier, count in stats["by_tier"].items():
            text += f"\n  • {tier.capitalize()}: {count}"
        
        keyboard = [[self.InlineKeyboardButton("🔙 Back", callback_data="start")]]
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=self.InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=self.InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    
    async def cmd_support(self, update, context):
        text = """<b>🆘 Support</b>

For payment issues or questions:
• Send tx hash here after payment
• Admin will verify and upgrade manually
• Response time: usually within 1 hour

<b>Common issues:</b>
Q: I paid but not upgraded
A: Send your tx hash here, we verify on-chain

Q: How do I cancel?
A: Subscriptions are non-recurring. Just don't renew.

Q: Signal delay?
A: Free=1h, Basic=15min, Pro/VIP=instant"""
        keyboard = [[self.InlineKeyboardButton("🔙 Back", callback_data="start")]]
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=self.InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=self.InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    
    async def cmd_admin(self, update, context):
        chat_id = str(update.effective_chat.id)
        if chat_id != self.config["admin_chat_id"]:
            await update.message.reply_text("❌ Admin only.")
            return
        
        stats = self.users.get_stats()
        text = f"""<b>👑 Admin Dashboard</b>

<b>Users:</b> {stats['total_users']}
<b>Revenue:</b> ${stats['total_revenue']:.2f}
<b>Tiers:</b>"""
        for t, c in stats["by_tier"].items():
            text += f"\n  {t}: {c}"
        
        await update.message.reply_text(text, parse_mode="HTML")
    
    async def cmd_upgrade(self, update, context):
        """Admin command: /upgrade <chat_id> <tier> [days]"""
        chat_id = str(update.effective_chat.id)
        if chat_id != self.config["admin_chat_id"]:
            await update.message.reply_text("❌ Admin only.")
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /upgrade <chat_id> <tier> [days=30]")
            return
        
        target_chat = args[0]
        tier = args[1].lower()
        days = int(args[2]) if len(args) > 2 else 30
        
        if self.users.upgrade_tier(target_chat, tier, days):
            await update.message.reply_text(f"✅ Upgraded {target_chat} to {tier.upper()} for {days} days")
            # Notify user
            await self.broadcaster.send_message(
                target_chat,
                f"🎉 <b>Upgraded to {tier.upper()}!</b>\n\nYour subscription is active for {days} days.\nUse /status to check your limits."
            )
        else:
            await update.message.reply_text("❌ Upgrade failed")
    
    async def handle_callback(self, update, context):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data == "start":
            await self.cmd_start(update, context)
        elif data == "subscribe":
            await self.cmd_subscribe(update, context)
        elif data == "status":
            await self.cmd_status(update, context)
        elif data == "stats":
            await self.cmd_stats(update, context)
        elif data == "support":
            await self.cmd_support(update, context)
        elif data.startswith("pay_"):
            tier = data.replace("pay_", "")
            tier_info = self.config["tiers"].get(tier, {})
            text = f"""<b>💳 Payment for {tier.upper()}</b>

Price: <b>${tier_info.get('price', 0)}/month</b>

1. Send exact amount to wallet in /subscribe
2. Reply here with transaction hash
3. Admin will verify and activate

<i>Include your username or email in memo if possible</i>"""
            await query.edit_message_text(text, parse_mode="HTML")
    
    async def handle_message(self, update, context):
        """Handle incoming messages (payment proofs, etc)."""
        chat_id = str(update.effective_chat.id)
        text = update.message.text or ""
        user = self.users.get_or_create(chat_id, update.effective_user.username or "")
        
        # Detect tx hash (0x... or long alphanumeric)
        if text.startswith("0x") and len(text) >= 20:
            # Save payment proof
            proof = {
                "tx_hash": text[:100],
                "timestamp": datetime.now().isoformat(),
                "status": "pending_verification"
            }
            self.users.add_payment_proof(chat_id, proof)
            await update.message.reply_text(
                "✅ <b>Payment proof received!</b>\n\n"
                f"Tx: <code>{text[:20]}...</code>\n"
                "Admin will verify and upgrade you shortly.\n"
                "Response time: ~1 hour.",
                parse_mode="HTML"
            )
            # Notify admin
            await self.broadcaster.send_message(
                self.config["admin_chat_id"],
                f"💰 <b>New Payment Proof</b>\n\nUser: {chat_id}\nUsername: @{user.username}\nTx: <code>{text}</code>\nTier: {user.tier}\n\nUse /upgrade {chat_id} <tier> <days>"
            )
            return
        
        # Default response
        await update.message.reply_text(
            "I didn't understand that. Use /start for menu or /subscribe to upgrade."
        )
    
    def run(self):
        if not self._sdk_available:
            logger.error("python-telegram-bot not installed!")
            print("pip install python-telegram-bot")
            return
        if not self.config["bot_token"]:
            logger.error("No TELEGRAM_BOT_TOKEN!")
            return
        
        app = self.Application.builder().token(self.config["bot_token"]).build()
        
        app.add_handler(self.CommandHandler("start", self.cmd_start))
        app.add_handler(self.CommandHandler("subscribe", self.cmd_subscribe))
        app.add_handler(self.CommandHandler("status", self.cmd_status))
        app.add_handler(self.CommandHandler("stats", self.cmd_stats))
        app.add_handler(self.CommandHandler("support", self.cmd_support))
        app.add_handler(self.CommandHandler("admin", self.cmd_admin))
        app.add_handler(self.CommandHandler("upgrade", self.cmd_upgrade))
        app.add_handler(self.CallbackQueryHandler(self.handle_callback))
        app.add_handler(self.CommandHandler("help", self.cmd_start))
        
        # Message handler for payment proofs
        from telegram.ext import MessageHandler, filters
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("🏔️ Rehoboam Monetization Bot started!")
        app.run_polling()


# =============================================================================
# MARKETING AUTOMATION
# =============================================================================

class MarketingEngine:
    """Automated marketing via Telegram and social hooks."""
    
    def __init__(self, broadcaster: TelegramBroadcaster, users: UserManager):
        self.broadcaster = broadcaster
        self.users = users
        self.config = MONETIZATION_CONFIG
    
    async def send_daily_recap(self):
        """Send daily performance recap to all users."""
        stats = self.users.get_stats()
        message = f"""📊 <b>Daily Rehoboam Recap</b>

Network activity today:
• Active users: {stats['total_users']}
• Signals generated: check /stats

<b>Why traders choose Rehoboam:</b>
✅ 200 AI agents (Kimi K2.6) analyzing markets
✅ Multi-source convergence (CEX + on-chain)
✅ Real-time technical analysis
✅ Transparent, backtested signals

<b>Not subscribed?</b> /subscribe
<b>Questions?</b> /support

<i>Gunas Tribe — Power of the Present</i>"""
        
        for chat_id in self.users.users:
            await self.broadcaster.send_message(chat_id, message)
            await asyncio.sleep(0.2)
    
    async def send_promo_to_free_users(self):
        """Send upgrade promo to free users."""
        message = """🚀 <b>Upgrade to PRO — 50% OFF First Month</b>

Limited time: Get PRO ($149) for <b>$75</b> first month.

What you get:
• 25 signals/day (vs 1 on Free)
• Zero delay (vs 1h on Free)
• AI commentary on every signal
• Multi-source convergence alerts

<b>Only 20 spots left this week.</b>

/subscribe to claim"""
        
        for chat_id, user in self.users.users.items():
            if user.tier == "free":
                await self.broadcaster.send_message(chat_id, message)
                await asyncio.sleep(0.3)


# =============================================================================
# MAIN ENTRY
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Rehoboam Monetization Bot v3.0")
    parser.add_argument("--mode", choices=["bot", "signals", "full", "marketing"], default="full",
                        help="bot=interactive only, signals=broadcaster only, full=both, marketing=promo run")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--interval", type=int, default=15, help="Signal interval minutes")
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏔️  REHOBOAM MONETIZATION BOT v3.0  🏔️               ║
    ║                                                           ║
    ║   Mode: UNIFIED                                          ║
    ║   Purpose: SELL SIGNALS. MAKE MONEY.                    ║
    ║   Agents: 200 Gunas Tribe (Kimi K2.6)                   ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    if args.mode == "bot":
        bot = RehoboamMonetizationBot()
        bot.run()
    
    elif args.mode == "signals":
        orchestrator = SignalOrchestrator()
        if args.once:
            asyncio.run(orchestrator.run_cycle())
        else:
            asyncio.run(orchestrator.run())
    
    elif args.mode == "marketing":
        broadcaster = TelegramBroadcaster(MONETIZATION_CONFIG["bot_token"])
        users = UserManager(MONETIZATION_CONFIG["data_dir"])
        engine = MarketingEngine(broadcaster, users)
        asyncio.run(engine.send_promo_to_free_users())
    
    elif args.mode == "full":
        # Run signal orchestrator in background, bot in foreground
        orchestrator = SignalOrchestrator()
        
        async def run_both():
            # Start signal broadcaster in background
            signal_task = asyncio.create_task(orchestrator.run())
            
            # Start bot (blocks)
            bot = RehoboamMonetizationBot()
            if bot._sdk_available:
                # Run bot in executor since it's blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, bot.run)
            else:
                logger.warning("SDK not available, running signals only")
                await signal_task
        
        try:
            asyncio.run(run_both())
        except KeyboardInterrupt:
            print("\n🛑 Stopped")


if __name__ == "__main__":
    main()
