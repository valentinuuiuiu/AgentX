#!/usr/bin/env python3
"""
🏔️ REHOBOAM TELEGRAM BOT SETUP
================================
Creates a Telegram bot and configures it for the signal service.

PREREQUISITES:
1. Create a bot via @BotFather on Telegram
   - Send /newbot
   - Choose a name (e.g., "Rehoboam Signals")
   - Choose a username (e.g., "rehoboam_signals_bot")
   - Copy the bot token

2. Get your chat ID:
   - Send /start to @userinfobot
   - Copy your chat ID

3. Run this script:
   python3 setup_telegram_bot.py --token YOUR_BOT_TOKEN --chat YOUR_CHAT_ID

This will:
- Validate the bot token
- Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env
- Test sending a message to your chat
"""

import os
import sys
import argparse
import asyncio
import aiohttp
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"


async def validate_token(token: str) -> dict:
    """Validate a Telegram bot token."""
    url = f"https://api.telegram.org/bot{token}/getMe"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if data.get("ok"):
                return data["result"]
            else:
                raise ValueError(f"Invalid bot token: {data.get('description', 'Unknown error')}")


async def test_send_message(token: str, chat_id: str) -> bool:
    """Test sending a message to the chat."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🏔️ Rehoboam Signal Service Connected!\n\nYour bot is ready to receive trading signals.\n\nUse /start in the bot to see available commands.",
        "parse_mode": "HTML"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            return data.get("ok", False)


def update_env_file(token: str, chat_id: str):
    """Add Telegram vars to .env file."""
    lines = []
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()
    
    # Remove existing TELEGRAM lines
    lines = [l for l in lines if not l.startswith('TELEGRAM_BOT_TOKEN=') and not l.startswith('TELEGRAM_CHAT_ID=')]
    
    # Add new lines
    lines.append(f"\nTELEGRAM_BOT_TOKEN={token}\n")
    lines.append(f"TELEGRAM_CHAT_ID={chat_id}\n")
    
    with open(ENV_FILE, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated {ENV_FILE}")


async def main():
    parser = argparse.ArgumentParser(description="Setup Rehoboam Telegram Bot")
    parser.add_argument("--token", help="Telegram bot token from @BotFather")
    parser.add_argument("--chat", help="Your Telegram chat ID")
    parser.add_argument("--test-only", action="store_true", help="Only test existing config")
    args = parser.parse_args()
    
    # Try loading from .env if not provided
    token = args.token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = args.chat or os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Try loading from .env file directly
    if not token and ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.strip().split("=", 1)[1]
                elif line.startswith("TELEGRAM_CHAT_ID="):
                    chat_id = line.strip().split("=", 1)[1]
    
    print("=" * 60)
    print("🏔️  REHOBOAM TELEGRAM BOT SETUP")
    print("=" * 60)
    
    if not token:
        print("""
❌ No bot token found!

To set up your Telegram bot:

1. Open Telegram and search for @BotFather
2. Send /newbot
3. Choose a name: "Rehoboam Signals"
4. Choose a username: "rehoboam_signals_bot"
5. Copy the token (looks like: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)
6. Get your chat ID by messaging @userinfobot
7. Run: python3 setup_telegram_bot.py --token YOUR_TOKEN --chat YOUR_CHAT_ID
""")
        sys.exit(1)
    
    if not chat_id:
        print("❌ No chat ID found! Use --chat YOUR_CHAT_ID")
        sys.exit(1)
    
    # Validate token
    print(f"\n🔍 Validating bot token...")
    try:
        bot_info = await validate_token(token)
        print(f"✅ Bot validated: @{bot_info.get('username', 'unknown')} ({bot_info.get('first_name', '')})")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Test sending message
    print(f"\n📨 Testing message delivery to chat {chat_id}...")
    success = await test_send_message(token, chat_id)
    if success:
        print(f"✅ Message delivered successfully!")
    else:
        print(f"❌ Failed to deliver message. Make sure you've sent /start to the bot first.")
        sys.exit(1)
    
    # Update .env
    if not args.test_only:
        update_env_file(token, chat_id)
    
    print(f"\n🎉 SETUP COMPLETE!")
    print(f"\nNext steps:")
    print(f"  1. Start signal service: python3 crypto_signal_service.py")
    print(f"  2. Start Telegram bot:   python3 rehoboam_telegram_bot.py")
    print(f"  3. Share bot link:        t.me/{bot_info.get('username', 'your_bot')}")
    print(f"\n💰 Revenue tiers:")
    print(f"  🆓 FREE  — 1 signal/day, 60min delay")
    print(f"  🟡 BASIC — $49/mo, 5 signals/day, no delay")
    print(f"  🟠 PRO   — $149/mo, unlimited signals, all timeframes")
    print(f"  💎 VIP   — $299/mo, unlimited + exclusive analysis")


if __name__ == "__main__":
    asyncio.run(main())