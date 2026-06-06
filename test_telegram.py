#!/usr/bin/env python3
"""Debug script to test Telegram signal sending"""
import os
import sys
import asyncio

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("Environment check:")
print(f"TELEGRAM_BOT_TOKEN: {'SET' if os.getenv('TELEGRAM_BOT_TOKEN') else 'NOT SET'}")
print(f"TELEGRAM_CHAT_ID: {os.getenv('TELEGRAM_CHAT_ID', 'NOT SET')}")

# Now import and test
sys.path.insert(0, '/home/aryan/free-claude/bittensor/clean_rehoboam_project')

from crypto_signal_service import CryptoSignalService, SIGNAL_CONFIG

print("\nSIGNAL_CONFIG check:")
print(f"telegram_bot_token: {'SET' if SIGNAL_CONFIG['telegram_bot_token'] else 'NOT SET'}")
print(f"telegram_chat_id: {SIGNAL_CONFIG['telegram_chat_id']}")

async def test():
    service = CryptoSignalService()
    print("\nService initialized:")
    print(f"telegram.bot_token: {'SET' if service.telegram.bot_token else 'NOT SET'}")
    print(f"telegram.chat_id: {service.telegram.chat_id}")
    
    # Test sending a message
    if service.telegram.bot_token and service.telegram.chat_id:
        print("\nSending test signal...")
        from crypto_signal_service import Signal
        test_signal = Signal(
            pair="BTC-USD",
            timeframe="1h",
            action="BUY",
            strength=0.75,
            price=78350.0,
            indicators={"rsi": 45.2, "macd": 0.05, "price_change_24h": 2.5},
            timestamp="2026-04-23T22:00:00",
            reason="Test signal from Hermes",
            tier="PRO"
        )
        await service.telegram.send_signal(test_signal)
        print("Test signal sent!")
    else:
        print("\n❌ Cannot send - token or chat_id not configured")

asyncio.run(test())
