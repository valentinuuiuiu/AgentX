#!/usr/bin/env python3
"""
🏔️ REHOBOAM SIGNAL LAUNCHER
============================
Starts the signal service + Telegram bot together.
This is the money maker.

Usage:
  python3 run_signal_service.py              # Run both services
  python3 run_signal_service.py --signals     # Only signal service
  python3 run_signal_service.py --bot         # Only Telegram bot
  python3 run_signal_service.py --once        # Single signal cycle (for testing)
"""

import os
import sys
import asyncio
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).parent / "signal_data" / "service.log",
            mode='a'
        )
    ]
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent


async def run_signal_service(once=False):
    """Run the crypto signal service."""
    from crypto_signal_service import CryptoSignalService, SIGNAL_CONFIG
    
    config = SIGNAL_CONFIG.copy()
    # Load from env
    config['telegram_bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN', '')
    config['telegram_chat_id'] = os.getenv('TELEGRAM_CHAT_ID', '')
    
    service = CryptoSignalService(config)
    
    if once:
        logger.info("🔄 Running single signal cycle...")
        await service.run_cycle()
        return
    
    logger.info("🏔️ Starting Rehoboam Signal Service (24/7 mode)")
    await service.run()


async def run_telegram_bot():
    """Run the Telegram bot for subscriptions."""
    try:
        from rehoboam_telegram_bot import RehoboamBot, BOT_CONFIG
        import os
        
        config = BOT_CONFIG.copy()
        config['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN', '')
        config['admin_chat_id'] = os.getenv('TELEGRAM_CHAT_ID', '')
        
        if not config['bot_token']:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set. Telegram bot disabled.")
            logger.warning("   Run: python3 setup_telegram_bot.py --token YOUR_TOKEN --chat YOUR_CHAT_ID")
            return
        
        bot = RehoboamBot(config)
        logger.info("🤖 Starting Telegram bot...")
        bot.run()
    except Exception as e:
        logger.error(f"❌ Telegram bot failed: {e}")
        logger.info("   Signal service will continue without Telegram bot.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Rehoboam Signal Launcher")
    parser.add_argument("--signals", action="store_true", help="Only run signal service")
    parser.add_argument("--bot", action="store_true", help="Only run Telegram bot")
    parser.add_argument("--once", action="store_true", help="Single signal cycle (test)")
    args = parser.parse_args()
    
    # Ensure data directory exists
    (PROJECT_DIR / "signal_data").mkdir(exist_ok=True)
    (PROJECT_DIR / "bot_data").mkdir(exist_ok=True)
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏔️  REHOBOAM SIGNAL SERVICE  🏔️                       ║
    ║                                                           ║
    ║   "One product. One purpose. Make money."                ║
    ║                                                           ║
    ║   Signals → Telegram → Subscribers → Revenue            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    if args.once:
        asyncio.run(run_signal_service(once=True))
    elif args.signals:
        asyncio.run(run_signal_service())
    elif args.bot:
        asyncio.run(run_telegram_bot())
    else:
        # Run both — signal service in background, bot in foreground
        # Signal service runs as a subprocess
        logger.info("🚀 Starting both Signal Service and Telegram Bot")
        logger.info("   Signal service: background process")
        logger.info("   Telegram bot: foreground")
        
        # Start signal service as subprocess
        signal_proc = subprocess.Popen(
            [sys.executable, str(PROJECT_DIR / "crypto_signal_service.py")],
            cwd=str(PROJECT_DIR),
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        
        # Write PID
        pid_file = PROJECT_DIR / "signal_service.pid"
        pid_file.write_text(str(signal_proc.pid))
        logger.info(f"   Signal service PID: {signal_proc.pid}")
        
        try:
            # Run Telegram bot in foreground
            asyncio.run(run_telegram_bot())
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
            signal_proc.terminate()
            signal_proc.wait(timeout=5)
            pid_file.unlink(missing_ok=True)
            logger.info("✅ Stopped.")


if __name__ == "__main__":
    main()