#!/usr/bin/env python3
"""
🚀 REHOBOAM OUTREACH BOT
=========================
Automated outreach to crypto communities to get first paying customers.

Strategies:
1. Post in crypto Telegram groups (with value-first approach)
2. DM active traders who ask about signals
3. Post on crypto subreddits
4. Comment on Twitter/X crypto posts

Usage:
    python3 outreach_bot.py --dry-run    # Preview messages
    python3 outreach_bot.py              # Send real outreach
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent

# Outreach messages (value-first, no spam)
OUTREACH_TEMPLATES = {
    "telegram_group": [
        "I've been running a multi-source convergence scanner (Binance + Coinbase + Chainlink oracles) for the past week. Found some interesting divergences on {pair}. Happy to share the setup if anyone's building their own signal system.",
        "Built a free signal bot that cross-references CEX prices with on-chain oracles. Caught a 0.3% spread on {pair} earlier. DM if you want the alerts — no cost, just testing the system.",
        "Question for the group: Do you trust single-source signals? I've been comparing Binance vs Chainlink prices and the divergence is wild sometimes. Built a tool to track it — free to use while I'm testing.",
    ],
    "reddit": [
        "[Free Tool] I built a convergence scanner that checks Binance, Coinbase, and Chainlink oracles before generating a signal. Here's what I learned after 100 signals...",
        "Signal services charge $100+/mo for basic Binance alerts. I built a free alternative that adds on-chain confirmation and risk management. Looking for beta testers.",
    ],
    "twitter_reply": [
        "Have you tried cross-referencing with Chainlink oracles? I built a free tool that does this automatically — catches a lot of false signals from single-source bots.",
        "If you're looking for signal validation, I built a free convergence scanner. Checks 3 sources before alerting. DM me if you want access.",
    ],
    "dm_trader": [
        "Hey, saw your post about trading signals. I built a free convergence scanner (Binance + Coinbase + Chainlink) with risk management. Want to try it? No cost, just looking for feedback.",
        "Hi! I noticed you're active in trading discussions. I built a signal bot that validates across multiple exchanges + on-chain oracles. It's free while I test it. Interested?",
    ]
}

# Target communities (add your own)
TARGET_COMMUNITIES = {
    "telegram_groups": [
        "CryptoSignals",
        "DeFiTraders",
        "AltcoinDiscussion",
        "CryptoAlpha",
    ],
    "subreddits": [
        "CryptoCurrency",
        "CryptoMarkets",
        "altcoin",
        "Daytrading",
    ],
    "twitter_hashtags": [
        "#CryptoSignals",
        "#TradingBot",
        "#DeFi",
        "#Altcoin",
    ]
}


def generate_outreach(campaign_type: str, pair: str = "ETH") -> str:
    """Generate a value-first outreach message."""
    import random
    templates = OUTREACH_TEMPLATES.get(campaign_type, OUTREACH_TEMPLATES["telegram_group"])
    template = random.choice(templates)
    return template.format(pair=pair)


def save_outreach_log(message: str, platform: str, status: str):
    """Log all outreach attempts."""
    log_file = PROJECT_DIR / "signal_data" / "outreach_log.json"
    log_file.parent.mkdir(exist_ok=True)
    
    logs = []
    if log_file.exists():
        try:
            with open(log_file) as f:
                logs = json.load(f)
        except:
            pass
    
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "message": message,
        "status": status,
    })
    
    # Keep last 1000
    logs = logs[-1000:]
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)


async def run_outreach_campaign(dry_run: bool = True):
    """Run outreach campaign."""
    logger.info("=" * 60)
    logger.info("🚀 REHOBOAM OUTREACH CAMPAIGN")
    logger.info("=" * 60)
    
    # Generate sample messages for each platform
    campaigns = []
    
    for platform, templates in OUTREACH_TEMPLATES.items():
        for template in templates[:2]:  # Use first 2 templates per platform
            message = template.format(pair="ETH")
            campaigns.append({"platform": platform, "message": message})
    
    logger.info(f"Generated {len(campaigns)} outreach messages")
    
    if dry_run:
        logger.info("\n📋 DRY RUN — Messages that WOULD be sent:")
        for i, campaign in enumerate(campaigns, 1):
            logger.info(f"\n{i}. [{campaign['platform']}]")
            logger.info(f"   {campaign['message'][:100]}...")
        logger.info(f"\n✅ Dry run complete. {len(campaigns)} messages ready.")
        logger.info("Run without --dry-run to see full messages.")
        return
    
    # In a real implementation, this would:
    # 1. Connect to Telegram API and post in groups
    # 2. Use Reddit API to post in subreddits
    # 3. Use Twitter API to reply to posts
    # For now, we log and provide manual copy-paste
    
    logger.info("\n📋 OUTREACH MESSAGES (Copy-paste these manually):")
    print("\n" + "="*70)
    for i, campaign in enumerate(campaigns, 1):
        print(f"\n{i}. [{campaign['platform'].upper()}]")
        print("-" * 50)
        print(campaign['message'])
        print("-" * 50)
        save_outreach_log(campaign['message'], campaign['platform'], "manual")
    
    print("\n" + "="*70)
    logger.info(f"\n✅ {len(campaigns)} outreach messages generated!")
    logger.info("Copy-paste these into crypto communities.")
    logger.info("Track responses in signal_data/outreach_log.json")


def generate_affiliate_guide():
    """Generate affiliate signup guide."""
    guide = """
╔══════════════════════════════════════════════════════════════════╗
║                    AFFILIATE SIGNUP GUIDE                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1. BINANCE (20-40% commission)                                  ║
║     → https://www.binance.com/en/activity/referral               ║
║     → Get your referral ID                                       ║
║     → Replace YOUR_BINANCE_REF in hermes_signal_bot.py           ║
║                                                                  ║
║  2. BYBIT (up to 50% commission)                                 ║
║     → https://www.bybit.com/en-US/affiliates                     ║
║     → Apply for affiliate program                                ║
║     → Replace YOUR_BYBIT_REF in hermes_signal_bot.py             ║
║                                                                  ║
║  3. OKX (30-50% commission)                                      ║
║     → https://www.okx.com/affiliates                             ║
║     → Sign up as affiliate                                       ║
║     → Replace YOUR_OKX_REF in hermes_signal_bot.py               ║
║                                                                  ║
║  4. COINBASE ($10 per referral)                                  ║
║     → https://www.coinbase.com/affiliates                        ║
║                                                                  ║
║  5. LEDGER (10% commission)                                      ║
║     → https://affiliates.ledger.com                             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(guide)
    
    # Save to file
    guide_file = PROJECT_DIR / "AFFILIATE_GUIDE.txt"
    with open(guide_file, 'w') as f:
        f.write(guide)
    logger.info(f"Affiliate guide saved to {guide_file}")


def generate_pricing_page():
    """Generate pricing page content."""
    pricing = """
╔══════════════════════════════════════════════════════════════════╗
║                    REHOBOAM PRICING                              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  🆓 FREE TIER                                                    ║
║  • 1 signal per day (delayed 1 hour)                            ║
║  • Basic technical analysis                                      ║
║  • Email alerts                                                  ║
║  • Cost: $0                                                      ║
║                                                                  ║
║  🟡 BASIC — $19/month                                           ║
║  • 3 signals per day (real-time)                                ║
║  • Multi-source convergence (2 sources)                        ║
║  • Risk management included                                    ║
║  • Telegram alerts                                             ║
║  • Payment: Crypto (ETH, BTC, USDC)                             ║
║                                                                  ║
║  🟠 PRO — $49/month                                             ║
║  • Unlimited signals (real-time)                                ║
║  • Full convergence (Binance + Coinbase + Chainlink)            ║
║  • Arbitrage detection                                         ║
║  • Portfolio tracking                                          ║
║  • Priority support                                            ║
║  • Payment: Crypto + PayPal                                     ║
║                                                                  ║
║  💎 VIP — $149/month                                            ║
║  • Everything in PRO                                            ║
║  • Whale tracking                                              ║
║  • Custom pair monitoring                                      ║
║  • 1-on-1 strategy calls                                       ║
║  • White-label bot setup                                       ║
║  • Payment: Wire transfer + Crypto                              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

PAYMENT METHODS:
• ETH: 0xa4660Bf26BF89fe073d42E7A4945a3Df6Bd3c407
• BTC: bc1q... (generate with your wallet)
• USDC (ERC-20): 0xa4660Bf26BF89fe073d42E7A4945a3Df6Bd3c407
• PayPal: your-paypal@email.com

To upgrade: DM @web4_bot_nobot with your desired tier.
"""
    print(pricing)
    
    pricing_file = PROJECT_DIR / "PRICING.txt"
    with open(pricing_file, 'w') as f:
        f.write(pricing)
    logger.info(f"Pricing page saved to {pricing_file}")


def main():
    parser = argparse.ArgumentParser(description="Rehoboam Outreach Bot")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--affiliate-guide", action="store_true", help="Show affiliate guide")
    parser.add_argument("--pricing", action="store_true", help="Show pricing")
    args = parser.parse_args()
    
    if args.affiliate_guide:
        generate_affiliate_guide()
        return
    
    if args.pricing:
        generate_pricing_page()
        return
    
    asyncio.run(run_outreach_campaign(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
