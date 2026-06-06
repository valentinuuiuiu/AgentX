#!/usr/bin/env python3
"""
🤖 HERMES INTERACTIVE BOT — Customer Service & Sales
=====================================================
The face of Rehoboam. Handles conversations, onboarding, and sales.

Features:
- /start — Welcome message + trial offer
- /trial — Start 7-day free PRO trial
- /pricing — Show pricing tiers
- /help — FAQ and support
- /status — Check signal performance
- /referral — Get referral code
- /upgrade — Upgrade to paid tier
- Auto-respond to common questions
- Track all conversations

Usage:
    python3 hermes_interactive_bot.py
"""

import os
import sys
import json
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import telegram bot library
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, 
        CallbackQueryHandler, ContextTypes, filters
    )
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    print("⚠️  python-telegram-bot not installed. Run: pip install python-telegram-bot")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent
DB_PATH = PROJECT_DIR / "signal_data" / "customers.db"
DB_PATH.parent.mkdir(exist_ok=True)

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")


class CustomerDB:
    """Customer database for the bot."""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id TEXT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    status TEXT DEFAULT 'lead',
                    tier TEXT DEFAULT 'FREE',
                    trial_start TEXT,
                    trial_end TEXT,
                    referral_code TEXT UNIQUE,
                    referred_by TEXT,
                    referral_count INTEGER DEFAULT 0,
                    messages_count INTEGER DEFAULT 0,
                    first_contact TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_contact TEXT,
                    notes TEXT
                )
            """)
            conn.commit()
    
    def get_or_create_customer(self, telegram_id: str, username: str = None,
                                first_name: str = None, last_name: str = None) -> Dict:
        """Get or create a customer record."""
        import secrets
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            # Try to get existing
            customer = conn.execute(
                "SELECT * FROM customers WHERE telegram_id = ?",
                (telegram_id,)
            ).fetchone()
            
            if customer:
                # Update last contact
                conn.execute(
                    "UPDATE customers SET last_contact = ?, messages_count = messages_count + 1 WHERE telegram_id = ?",
                    (datetime.now().isoformat(), telegram_id)
                )
                conn.commit()
                return dict(customer)
            
            # Create new
            referral_code = secrets.token_hex(4).upper()
            cursor = conn.execute("""
                INSERT INTO customers (telegram_id, username, first_name, last_name, 
                                       referral_code, last_contact)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (telegram_id, username, first_name, last_name, 
                  referral_code, datetime.now().isoformat()))
            conn.commit()
            
            return {
                'id': cursor.lastrowid,
                'telegram_id': telegram_id,
                'username': username,
                'first_name': first_name,
                'status': 'lead',
                'tier': 'FREE',
                'referral_code': referral_code,
                'messages_count': 1
            }
    
    def start_trial(self, telegram_id: str, days: int = 7) -> bool:
        """Start a free trial."""
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=days)
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("""
                UPDATE customers SET
                    status = 'trial',
                    tier = 'PRO',
                    trial_start = ?,
                    trial_end = ?,
                    last_contact = ?
                WHERE telegram_id = ?
            """, (trial_start.isoformat(), trial_end.isoformat(),
                  datetime.now().isoformat(), telegram_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_customer(self, telegram_id: str) -> Optional[Dict]:
        """Get customer by telegram ID."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            customer = conn.execute(
                "SELECT * FROM customers WHERE telegram_id = ?",
                (telegram_id,)
            ).fetchone()
            return dict(customer) if customer else None
    
    def get_stats(self) -> Dict:
        """Get bot stats."""
        with sqlite3.connect(DB_PATH) as conn:
            total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
            trials = conn.execute("SELECT COUNT(*) FROM customers WHERE status = 'trial'").fetchone()[0]
            paid = conn.execute("SELECT COUNT(*) FROM customers WHERE status = 'paid'").fetchone()[0]
            return {'total_users': total, 'active_trials': trials, 'paid_users': paid}


# ============== COMMAND HANDLERS ==============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    db = CustomerDB()
    
    # Get or create customer
    customer = db.get_or_create_customer(
        str(user.id),
        user.username,
        user.first_name,
        user.last_name
    )
    
    welcome_text = f"""🎉 Welcome to Rehoboam Signals, {user.first_name}!

I'm Hermes, your trading signal assistant. I help traders make better decisions with multi-source convergence signals.

🚀 What I do:
• Cross-reference Binance + Coinbase + Chainlink
• Only alert when 3 sources agree
• Include risk management (SL/TP/position size)
• Track performance automatically

🎁 YOUR FREE GIFT:
7-day PRO trial — no credit card needed!

📊 What you get:
✅ Real-time signals (every 5 min)
✅ 3-source convergence validation
✅ Risk management on every signal
✅ Arbitrage detection
✅ Performance tracking

Ready to start?

⬇️ CHOOSE AN OPTION BELOW ⬇️"""
    
    keyboard = [
        [InlineKeyboardButton("🎁 Start FREE Trial", callback_data='start_trial')],
        [InlineKeyboardButton("💎 View Pricing", callback_data='pricing')],
        [InlineKeyboardButton("❓ How It Works", callback_data='how_it_works')],
        [InlineKeyboardButton("📊 Live Signals", callback_data='live_signals')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    logger.info(f"New user started: @{user.username} ({user.id})")


async def trial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trial command."""
    user = update.effective_user
    db = CustomerDB()
    customer = db.get_customer(str(user.id))
    
    if customer and customer.get('status') == 'trial':
        trial_end = customer.get('trial_end', '')
        if trial_end:
            end_date = datetime.fromisoformat(trial_end)
            days_left = (end_date - datetime.now()).days
            await update.message.reply_text(
                f"⏰ Your trial is already active!\n\n"
                f"Ends in: {days_left} days ({end_date.strftime('%Y-%m-%d')})\n\n"
                f"You're receiving PRO signals right now. Enjoy!"
            )
            return
    
    # Start trial
    if db.start_trial(str(user.id), days=7):
        trial_end = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        await update.message.reply_text(
            f"🎉 TRIAL ACTIVATED!\n\n"
            f"You now have 7 days of FREE PRO access.\n"
            f"Expires: {trial_end}\n\n"
            f"📊 What's happening now:\n"
            f"• Signals posting every 5 minutes\n"
            f"• Full convergence analysis\n"
            f"• Risk management included\n\n"
            f"💰 Want FREE extra days?\n"
            f"Use /referral to get your code. When friends sign up, you get +7 days!\n\n"
            f"Questions? Just ask me anything!"
        )
        logger.info(f"Trial started for: @{user.username}")
    else:
        await update.message.reply_text(
            "❌ Could not start trial. Please contact support."
        )


async def pricing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pricing command."""
    pricing_text = """💎 REHOBOAM PRICING

🆓 FREE TIER
• 1 signal per day (1h delay)
• Basic technical analysis
• Community access
• Cost: $0

🟠 PRO — $49/month
• Unlimited real-time signals
• Full 3-source convergence
• Risk management (SL/TP/position size)
• Arbitrage detection
• Performance tracking
• Telegram alerts

💎 VIP — $149/month
• Everything in PRO
• Whale tracking
• Custom pair monitoring
• 1-on-1 strategy calls
• White-label bot setup
• Priority support

🎁 SPECIAL OFFER:
Start with 7-day FREE PRO trial!
No credit card required.

Use /trial to start now!"""
    
    keyboard = [
        [InlineKeyboardButton("🎁 Start FREE Trial", callback_data='start_trial')],
        [InlineKeyboardButton("💬 Contact Admin", url='https://t.me/web4_bot_nobot')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(pricing_text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """❓ HERMES HELP

Available commands:
/start — Welcome message
/trial — Start 7-day FREE PRO trial
/pricing — View pricing tiers
/status — Check your account status
/referral — Get your referral code
/upgrade — Upgrade to paid tier
/help — This message

💬 COMMON QUESTIONS:

Q: How do signals work?
A: We scan Binance, Coinbase, and Chainlink oracles. Only alert when all 3 agree + technicals confirm.

Q: What's the win rate?
A: Check /status for current stats. We track every signal in our database.

Q: Is this financial advice?
A: No. Always DYOR. We provide data, you make decisions.

Q: How do I cancel?
A: Just stop using the bot. No contracts.

Q: Can I get a refund?
A: We offer 7-day free trial so you can test before paying.

Need more help? Contact @web4_bot_nobot"""
    
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    user = update.effective_user
    db = CustomerDB()
    customer = db.get_customer(str(user.id))
    stats = db.get_stats()
    
    if customer:
        status = customer.get('status', 'lead')
        tier = customer.get('tier', 'FREE')
        trial_end = customer.get('trial_end', '')
        referral_code = customer.get('referral_code', '')
        
        status_text = f"""📊 YOUR STATUS

User: @{customer.get('username', 'N/A')}
Status: {status.upper()}
Tier: {tier}
Referral Code: {referral_code}
"""
        
        if trial_end and status == 'trial':
            end_date = datetime.fromisoformat(trial_end)
            days_left = (end_date - datetime.now()).days
            status_text += f"\nTrial ends: {end_date.strftime('%Y-%m-%d')} ({days_left} days left)"
        
        status_text += f"""

📈 PLATFORM STATS:
Total users: {stats['total_users']}
Active trials: {stats['active_trials']}
Paid users: {stats['paid_users']}
"""
    else:
        status_text = "❌ You haven't started yet. Use /start to begin!"
    
    await update.message.reply_text(status_text)


async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /referral command."""
    user = update.effective_user
    db = CustomerDB()
    customer = db.get_customer(str(user.id))
    
    if not customer:
        await update.message.reply_text("Use /start first!")
        return
    
    referral_code = customer.get('referral_code', '')
    referral_count = customer.get('referral_count', 0)
    
    referral_text = f"""🎁 YOUR REFERRAL PROGRAM

Your code: `{referral_code}`

Friends signed up: {referral_count}

How it works:
1. Share your code with trader friends
2. They DM me with: "REF {referral_code}"
3. They get 7-day FREE trial
4. When they upgrade to paid → YOU get +7 days FREE

Share this message:

---
🚀 Free Crypto Signal Bot (7-day trial)

Multi-source convergence scanner:
✅ Binance + Coinbase + Chainlink
✅ Risk management included
✅ Real-time alerts

DM @web4_bot_nobot with:
REF {referral_code}

---

The more you share, the more free days you earn! 🚀"""
    
    await update.message.reply_text(referral_text, parse_mode='Markdown')


async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upgrade command."""
    upgrade_text = """💎 UPGRADE YOUR ACCOUNT

Current payment methods:
• ETH: 0xa4660Bf26BF89fe073d42E7A4945a3Df6Bd3c407
• BTC: (generate with your wallet)
• USDC (ERC-20): 0xa4660Bf26BF89fe073d42E7A4945a3Df6Bd3c407
• PayPal: Contact admin

To upgrade:
1. Send payment to the wallet above
2. DM @web4_bot_nobot with your TX hash
3. We'll activate your account within 1 hour

🟠 PRO — $49/month
💎 VIP — $149/month

Not ready to pay? Use /trial for 7 days FREE!"""
    
    keyboard = [
        [InlineKeyboardButton("🎁 Start FREE Trial Instead", callback_data='start_trial')],
        [InlineKeyboardButton("💬 Contact Admin", url='https://t.me/web4_bot_nobot')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(upgrade_text, reply_markup=reply_markup)


# ============== CALLBACK HANDLERS ==============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start_trial':
        await trial_command(update, context)
    elif query.data == 'pricing':
        await pricing_command(update, context)
    elif query.data == 'how_it_works':
        how_text = """🔍 HOW REHOBOAM WORKS

1. DATA COLLECTION
   • Binance CEX (real-time)
   • Coinbase CEX (validation)
   • Chainlink oracle (on-chain)

2. CONVERGENCE CHECK
   All 3 sources must agree on direction

3. TECHNICAL ANALYSIS
   • RSI (overbought/oversold)
   • MACD (momentum)
   • Bollinger Bands (volatility)
   • Moving averages (trend)

4. RISK MANAGEMENT
   • Stop loss (2x ATR)
   • Take profit 1 (2.5x risk)
   • Take profit 2 (4.5x risk)
   • Position size (Kelly criterion)

5. ALERT
   Only when score ≥ 40% (3+ sources agree)

This is why our signals are different from basic bots."""
        await query.edit_message_text(how_text)
    elif query.data == 'live_signals':
        await query.edit_message_text(
            "📊 Signals are posted every 5 minutes in this chat!\n\n"
            "Your trial includes ALL real-time signals.\n\n"
            "Use /trial to activate if you haven't already!"
        )


# ============== MESSAGE HANDLER ==============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages."""
    user = update.effective_user
    text = update.message.text.upper()
    db = CustomerDB()
    
    # Track customer
    customer = db.get_or_create_customer(
        str(user.id), user.username, user.first_name, user.last_name
    )
    
    # Check for referral code
    if text.startswith("REF "):
        code = text.split("REF ")[1].strip()
        # Process referral
        await update.message.reply_text(
            f"🎉 Referral code received: {code}\n\n"
            f"Starting your 7-day FREE trial now..."
        )
        db.start_trial(str(user.id), days=7)
        return
    
    # Check for FREE TRIAL request
    if "FREE TRIAL" in text or "TRIAL" in text:
        await trial_command(update, context)
        return
    
    # Check for PRICING question
    if any(word in text for word in ["PRICE", "PRICING", "COST", "HOW MUCH"]):
        await pricing_command(update, context)
        return
    
    # Check for HELP question
    if any(word in text for word in ["HELP", "HOW", "WHAT", "?"]):
        await help_command(update, context)
        return
    
    # Check for SIGNAL question
    if any(word in text for word in ["SIGNAL", "TRADE", "BUY", "SELL"]):
        await update.message.reply_text(
            "📊 Signals are posted automatically every 5 minutes!\n\n"
            "Each signal includes:\n"
            "• Entry price\n"
            "• Stop loss\n"
            "• Take profit targets\n"
            "• Position size\n\n"
            "Use /trial to start receiving signals!"
        )
        return
    
    # Default response
    await update.message.reply_text(
        f"Hey {user.first_name}! 👋\n\n"
        f"I can help you with:\n"
        f"• /trial — Start 7-day FREE PRO\n"
        f"• /pricing — View plans\n"
        f"• /status — Check your account\n"
        f"• /referral — Get referral code\n"
        f"• /help — Full FAQ\n\n"
        f"What would you like to do?"
    )


# ============== ERROR HANDLER ==============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error: {context.error}")


# ============== MAIN ==============

def main():
    """Start the bot."""
    if not TELEGRAM_BOT_AVAILABLE:
        print("❌ python-telegram-bot not installed")
        print("Run: pip install python-telegram-bot")
        return
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        return
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🤖 HERMES INTERACTIVE BOT STARTING 🤖                  ║
    ║                                                           ║
    ║   Ready to talk to customers!                            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("trial", trial_command))
    application.add_handler(CommandHandler("pricing", pricing_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("referral", referral_command))
    application.add_handler(CommandHandler("upgrade", upgrade_command))
    
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🤖 Hermes Interactive Bot is running!")
    logger.info("Send /start to @web4_bot_nobot to test")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
