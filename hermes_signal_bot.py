#!/usr/bin/env python3
"""
🏔️ HERMES SIGNAL BOT — The Revenue Engine
==========================================
Hermes owns the entire money-making pipeline:

  1. Generate convergence signals (Binance + Chainlink)
  2. Add LLM commentary (via OpenRouter free models)
  3. Post to Telegram (with tier-based access)
  4. Track performance
  5. Collect subscribers

Usage:
  python3 hermes_signal_bot.py --once          # Single cycle (test)
  python3 hermes_signal_bot.py                 # Run continuously (production)
  python3 hermes_signal_bot.py --tier VIP      # Only post VIP signals
  python3 hermes_signal_bot.py --no-telegram   # Generate but don't post

This is the bot that makes money. Run it 24/7.
"""

import os
import sys
import asyncio
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime

# Load .env before anything else
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).parent / "signal_data" / "hermes_bot.log",
            mode='a'
        )
    ]
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))


async def run_once(tier: str = "FREE", post_to_telegram: bool = True):
    """Run one signal pipeline cycle with REAL convergence."""
    from real_convergence_engine import RealConvergenceEngine, SignalDatabase

    tier_order = {"FREE": 0, "BASIC": 1, "PRO": 2, "VIP": 3}
    min_tier_level = tier_order.get(tier, 2)

    logger.info("=" * 60)
    logger.info("🏔️  HERMES REAL SIGNAL PIPELINE v2.0")
    logger.info("=" * 60)

    pairs = ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD", "AAVE-USD", "UNI-USD"]
    timeframes = ["1h", "4h"]

    async with RealConvergenceEngine() as engine:
        signals = await engine.run_cycle(pairs, timeframes)

    if not signals:
        logger.info("No signals generated this cycle")
        return {"signals_generated": 0, "posted": 0}

    # Filter by tier AND minimum strength (0.4 = only quality signals)
    qualified = [s for s in signals
                 if tier_order.get(s.tier, 0) >= min_tier_level and s.strength >= 0.4]
    logger.info(f"Signals: {len(signals)} total, {len(qualified)} >= {tier} (strength >= 40%)")

    # Get top signals (max 2 per cycle — quality over quantity)
    top_signals = sorted(qualified, key=lambda x: x.strength, reverse=True)[:2]

    # Telegram config
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    telegram_chat = os.environ.get("TELEGRAM_CHAT_ID", "")

    # Get performance stats
    db = SignalDatabase()
    stats = db.get_stats()

    posted = 0
    for signal in top_signals:
        tier_emoji = {"BASIC": "🟡", "PRO": "🟠", "VIP": "💎"}.get(signal.tier, "🆓")
        action_emoji = {"BUY": "🟢", "SELL": "🔴", "ARBITRAGE": "⚡"}.get(signal.action, "⚪")

        # Build rich message with risk management (keep under 4096 chars for Telegram)
        import html
        prices_section = f"Binance: ${signal.price_binance:,.2f}"
        if signal.price_coinbase:
            prices_section += f" | Coinbase: ${signal.price_coinbase:,.2f}"
        if signal.price_chainlink:
            prices_section += f" | Chainlink: ${signal.price_chainlink:,.2f}"

        # Escape HTML in reason to avoid Telegram parse errors
        safe_reason = html.escape(signal.reason)

        # Affiliate links (replace with your actual referral IDs)
        base = signal.pair.split("-")[0]
        affiliate_links = {
            "binance": f"https://www.binance.com/en/trade/{base}_USDT?ref=YOUR_BINANCE_REF",
            "bybit": f"https://www.bybit.com/en-US/trade/spot/{base}/USDT?affiliate_id=YOUR_BYBIT_REF",
            "okx": f"https://www.okx.com/trade-spot/{base.lower()}-usdt?channelid=YOUR_OKX_REF",
        }

        message = (
            f"{action_emoji} <b>REHOBOAM SIGNAL</b> {action_emoji}\n\n"
            f"<b>{signal.action} {signal.pair}</b> ({signal.timeframe})\n"
            f"{tier_emoji} <b>{signal.tier}</b> | Score: {signal.convergence_score:.0%} | Sources: {signal.sources_count}\n\n"
            f"<b>Prices:</b> {prices_section}\n"
            f"Spread: {signal.price_spread_max:+.2f}%\n\n"
            f"<b>Risk Management:</b>\n"
            f"Entry: ${signal.risk.entry_price:,.2f}\n"
            f"Stop Loss: ${signal.risk.stop_loss:,.2f}\n"
            f"Take Profit 1: ${signal.risk.take_profit_1:,.2f}\n"
            f"Take Profit 2: ${signal.risk.take_profit_2:,.2f}\n"
            f"Position Size: {signal.risk.position_size_pct}% of portfolio\n"
            f"Risk/Reward: {signal.risk.risk_reward}:1\n"
            f"Max Loss: {signal.risk.max_loss_pct}%\n\n"
            f"<b>Analysis:</b> {safe_reason}\n\n"
            f"<b>Track Record:</b> {stats['winning_signals']}/{stats['total_signals']} wins ({stats['win_rate']:.1f}%)\n\n"
            f"<b>Trade Now:</b>\n"
            f"<a href='{affiliate_links['binance']}'>Binance</a> | "
            f"<a href='{affiliate_links['bybit']}'>Bybit</a> | "
            f"<a href='{affiliate_links['okx']}'>OKX</a>\n\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"<i>Powered by Rehoboam Multi-Source Convergence</i>\n\n"
            f"🎁 <b>FREE 7-Day PRO Trial</b>\n"
            f"DM @web4_bot_nobot with 'FREE TRIAL'\n\n"
            f"💎 <b>Refer & Earn:</b> Invite a friend, get +7 days FREE\n\n"
            f"<b>Upgrade:</b> @web4_bot_nobot"
        )

        if post_to_telegram and telegram_token and telegram_chat:
            try:
                import httpx
                url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                payload = {"chat_id": telegram_chat, "text": message, "parse_mode": "HTML"}
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, json=payload, timeout=15.0)
                    if resp.status_code == 200:
                        logger.info(f"📨 Telegram posted: {signal.action} {signal.pair}")
                        posted += 1
                    else:
                        logger.error(f"Telegram error: {resp.status_code}")
            except Exception as e:
                logger.error(f"Telegram post failed: {e}")
        else:
            logger.info(f"📵 Would post to Telegram: {signal.action} {signal.pair} ({signal.tier})")
            print(f"\n{'='*50}")
            print(message)
            print(f"{'='*50}")

        await asyncio.sleep(2)

    logger.info(f"Pipeline complete: {len(top_signals)} analyzed, {posted} posted")
    return {
        "signals_generated": len(signals),
        "qualified": len(qualified),
        "posted": posted,
        "top_signals": [f"{s.pair} {s.action}" for s in top_signals],
        "timestamp": datetime.now().isoformat(),
    }


async def run_continuous(tier: str = "PRO", interval: int = 15):
    """Run the signal pipeline continuously."""
    logger.info(f"🏔️  Hermes Signal Bot starting (tier >= {tier}, every {interval} min)")
    while True:
        try:
            result = await run_once(tier=tier)
            logger.info(f"Cycle result: {result}")
        except Exception as e:
            logger.error(f"Pipeline cycle error: {e}")
        logger.info(f"⏰ Next cycle in {interval} minutes")
        await asyncio.sleep(interval * 60)


def main():
    parser = argparse.ArgumentParser(description="Hermes Signal Bot — Revenue Engine")
    parser.add_argument("--once", action="store_true", help="Single cycle (test)")
    parser.add_argument("--tier", default="FREE", choices=["FREE", "BASIC", "PRO", "VIP"],
                        help="Minimum tier to post (default: FREE)")
    parser.add_argument("--interval", type=int, default=15, help="Minutes between cycles")
    parser.add_argument("--no-telegram", action="store_true", help="Don't post to Telegram")
    args = parser.parse_args()

    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏔️  HERMES SIGNAL BOT  🏔️                              ║
    ║                                                           ║
    ║   "Hermes owns the pipeline. Hermes makes the money."    ║
    ║                                                           ║
    ║   Convergence → LLM → Telegram → Revenue                 ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Check Telegram config
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("⚠️  WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        print("   Signals will be generated but NOT posted to Telegram.")
        print("   Run: python3 setup_telegram_bot.py --token TOKEN --chat CHAT_ID")
        print()

    if args.once:
        result = asyncio.run(run_once(tier=args.tier, post_to_telegram=not args.no_telegram))
        print(f"\n📊 Result: {result}")
    else:
        try:
            asyncio.run(run_continuous(tier=args.tier, interval=args.interval))
        except KeyboardInterrupt:
            print("\n🛑 Hermes Signal Bot stopped")


if __name__ == "__main__":
    main()