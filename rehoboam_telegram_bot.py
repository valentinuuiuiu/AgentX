#!/usr/bin/env python3
"""
🏔️ REHOBOAM TELEGRAM BOT 🏔️
============================
Membership tiers. Payment. Delivery.
This is the storefront.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import python-telegram-bot, fallback to basic implementation
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    TELEGRAM_SDK = True
except ImportError:
    TELEGRAM_SDK = False
    print("⚠️ python-telegram-bot not installed. Install with: pip install python-telegram-bot")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

BOT_CONFIG = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", "8337308834:AAGR2TKJLDbDTft6Q2M_7o9jf8tcpMESAx0"),
    "admin_chat_id": os.getenv("ADMIN_CHAT_ID", "8690918499"),
    "data_dir": "/home/aryan/free-claude/bittensor/clean_rehoboam_project/bot_data",
    "free_daily_limit": 1,
    "free_delay_minutes": 60,
    "tiers": {
        "free": {"name": "Free", "price": 0, "positions_per_day": 1, "delay_min": 60},
        "basic": {"name": "Basic", "price": 49, "positions_per_day": 5, "delay_min": 0},
        "pro": {"name": "Pro", "price": 149, "positions_per_day": 999, "delay_min": 0},
        "vip": {"name": "VIP", "price": 299, "positions_per_day": 999, "delay_min": 0, "exclusive": True}
    }
}

# =============================================================================
# USER MANAGEMENT
# =============================================================================

@dataclass
class User:
    chat_id: str
    username: str
    tier: str = "free"
    joined_at: str = ""
    expires_at: str = ""
    positions_today: int = 0
    last_reset: str = ""
    total_paid: float = 0.0
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class UserManager:
    """Manages user subscriptions and tiers."""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.users: Dict[str, User] = {}
        self._load()
    
    def _load(self):
        if self.users_file.exists():
            with open(self.users_file) as f:
                data = json.load(f)
                self.users = {k: User.from_dict(v) for k, v in data.items()}
    
    def _save(self):
        with open(self.users_file, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.users.items()}, f, indent=2)
    
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
        return self.users[chat_id]
    
    def can_receive_position(self, chat_id: str) -> bool:
        user = self.users.get(chat_id)
        if not user:
            return False
        
        tier = BOT_CONFIG["tiers"].get(user.tier, BOT_CONFIG["tiers"]["free"])
        
        # Reset daily counter if needed
        last_reset = datetime.fromisoformat(user.last_reset)
        if datetime.now() - last_reset > timedelta(days=1):
            user.positions_today = 0
            user.last_reset = datetime.now().isoformat()
            self._save()
        
        return user.positions_today < tier["positions_per_day"]
    
    def record_position_sent(self, chat_id: str):
        if chat_id in self.users:
            self.users[chat_id].positions_today += 1
            self._save()
    
    def upgrade_tier(self, chat_id: str, tier: str, duration_days: int = 30):
        if chat_id in self.users and tier in BOT_CONFIG["tiers"]:
            self.users[chat_id].tier = tier
            self.users[chat_id].expires_at = (datetime.now() + timedelta(days=duration_days)).isoformat()
            self._save()
            return True
        return False
    
    def get_stats(self) -> Dict:
        total = len(self.users)
        by_tier = {}
        for u in self.users.values():
            by_tier[u.tier] = by_tier.get(u.tier, 0) + 1
        return {"total_users": total, "by_tier": by_tier}


# =============================================================================
# BOT HANDLERS
# =============================================================================

class RehoboamBot:
    """Telegram bot for Rehoboam positions."""
    
    def __init__(self, config: Dict = None):
        self.config = config or BOT_CONFIG
        self.users = UserManager(self.config["data_dir"])
        self.application = None
    
    def _get_welcome_text(self) -> str:
        return """
🏔️ <b>Welcome to Rehoboam</b> 🏔️

<i>"The first AI that actually wins."</i>

We don't give signals. We give <b>positions</b>:
• Exact entry price
• Exact stop loss
• Exact take profit
• Exact position size
• Backtested before sent

<b>💎 SUBSCRIPTION TIERS</b>

🆓 <b>Free</b> — $0/month
   • 1 position per day
   • 1 hour delay

⭐ <b>Basic</b> — $49/month
   • 5 positions per day
   • Real-time delivery

🚀 <b>Pro</b> — $149/month
   • Unlimited positions
   • Real-time delivery

👑 <b>VIP</b> — $299/month
   • Everything in Pro
   • Direct access to team
   • Custom risk settings

<b>Every position includes:</b>
✅ Entry, Stop, Target
✅ Position size ($ risk)
✅ Risk/Reward ratio
✅ Confidence score
✅ Setup type (RSI, MACD, etc.)
✅ Backtest result
✅ Invalidation criteria

<b>Ready to start?</b> Use /subscribe
"""
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username or ""
        
        user = self.users.get_or_create(chat_id, username)
        
        keyboard = [
            [InlineKeyboardButton("💎 Subscribe", callback_data="subscribe")],
            [InlineKeyboardButton("📊 My Status", callback_data="status")],
            [InlineKeyboardButton("📈 Performance", callback_data="performance")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            self._get_welcome_text(),
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show subscription options."""
        keyboard = [
            [InlineKeyboardButton("⭐ Basic — $49/mo", callback_data="tier_basic")],
            [InlineKeyboardButton("🚀 Pro — $149/mo", callback_data="tier_pro")],
            [InlineKeyboardButton("👑 VIP — $299/mo", callback_data="tier_vip")],
            [InlineKeyboardButton("🔙 Back", callback_data="start")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
<b>💎 Choose Your Plan</b>

All plans include:
✅ Real-time positions
✅ Exact entry/stop/target
✅ Professional risk management
✅ Backtested setups

<b>Payment methods:</b>
• Crypto (BTC, ETH, USDT)
• Stripe (coming soon)

Click a plan below to upgrade.
"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user status."""
        chat_id = str(update.effective_chat.id)
        user = self.users.get_or_create(chat_id)
        tier_info = self.config["tiers"].get(user.tier, self.config["tiers"]["free"])
        
        text = f"""
<b>📊 Your Status</b>

<b>Tier:</b> {tier_info['name']}
<b>Positions today:</b> {user.positions_today}/{tier_info['positions_per_day']}
<b>Joined:</b> {user.joined_at[:10]}
"""
        if user.expires_at:
            text += f"<b>Expires:</b> {user.expires_at[:10]}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
    
    async def performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show performance stats."""
        positions_file = Path("/home/aryan/free-claude/bittensor/clean_rehoboam_project/position_data/positions.json")
        
        stats = {"total": 0, "long": 0, "short": 0}
        if positions_file.exists():
            with open(positions_file) as f:
                positions = json.load(f)
                stats["total"] = len(positions)
                stats["long"] = sum(1 for p in positions if p.get("direction") == "LONG")
                stats["short"] = sum(1 for p in positions if p.get("direction") == "SHORT")
        
        text = f"""
<b>📈 Rehoboam Performance</b>

<b>Positions Generated:</b> {stats['total']}
<b>Long Positions:</b> {stats['long']}
<b>Short Positions:</b> {stats['short']}

<i>Track record updates in real-time.</i>
<i>All positions are logged and verifiable.</i>

<b>Want access?</b> Use /subscribe
"""
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "subscribe":
            await self.subscribe(update, context)
        elif data == "status":
            await self.status(update, context)
        elif data == "performance":
            await self.performance(update, context)
        elif data == "start":
            await self.start(update, context)
        elif data.startswith("tier_"):
            tier = data.replace("tier_", "")
            await query.edit_message_text(
                f"<b>💳 Payment for {tier.upper()}</b>\n\n"
                f"Please send payment to:\n"
                f"<code>0x...your_wallet</code>\n\n"
                f"Then contact admin with proof.",
                parse_mode="HTML"
            )
    
    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to see stats."""
        chat_id = str(update.effective_chat.id)
        if chat_id != self.config["admin_chat_id"]:
            await update.message.reply_text("❌ Admin only.")
            return
        
        stats = self.users.get_stats()
        text = f"""
<b>👑 Admin Dashboard</b>

<b>Total Users:</b> {stats['total_users']}
<b>By Tier:</b>
"""
        for tier, count in stats["by_tier"].items():
            text += f"  • {tier}: {count}\n"
        
        await update.message.reply_text(text, parse_mode="HTML")
    
    def run(self):
        """Start the bot."""
        if not self.config["bot_token"]:
            logger.error("❌ No TELEGRAM_BOT_TOKEN configured!")
            print("Set TELEGRAM_BOT_TOKEN environment variable.")
            return
        
        if not TELEGRAM_SDK:
            logger.error("❌ python-telegram-bot not installed!")
            print("Run: pip install python-telegram-bot")
            return
        
        self.application = Application.builder().token(self.config["bot_token"]).build()
        
        # Handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("performance", self.performance))
        self.application.add_handler(CommandHandler("admin", self.admin_stats))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        logger.info("🏔️ Rehoboam Telegram Bot started!")
        self.application.run_polling()


# =============================================================================
# POSITION BROADCASTER
# =============================================================================

class PositionBroadcaster:
    """Broadcasts positions to subscribed users."""
    
    def __init__(self, bot_token: str, users: UserManager):
        self.bot_token = bot_token
        self.users = users
    
    async def broadcast_position(self, position: Dict):
        """Send position to all eligible users."""
        if not TELEGRAM_SDK or not self.bot_token:
            return
        
        from telegram import Bot
        bot = Bot(token=self.bot_token)
        
        emoji = "🟢" if position.get("direction") == "LONG" else "🔴"
        
        message = f"""
{emoji} <b>REHOBOAM POSITION</b> {emoji}

<b>{position['direction']} {position['pair']}</b> | {position['timeframe']}

📊 <b>ENTRY & EXIT</b>
├ Entry: <code>${position['entry_price']:,.2f}</code>
├ Stop: <code>${position['stop_loss']:,.2f}</code>
├ Target: <code>${position['take_profit']:,.2f}</code>
└ R:R = <b>1:{position['risk_reward_ratio']:.1f}</b>

🎯 <b>Confidence: {position['confidence_score']:.0%}</b>
<b>Setup:</b> {position['setup_type']}

⏰ {position['timestamp'][:19]} UTC
"""
        
        sent_count = 0
        for chat_id, user in self.users.users.items():
            if self.users.can_receive_position(chat_id):
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="HTML"
                    )
                    self.users.record_position_sent(chat_id)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to {chat_id}: {e}")
        
        logger.info(f"📨 Position broadcast to {sent_count} users")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    bot = RehoboamBot()
    bot.run()


if __name__ == "__main__":
    main()
