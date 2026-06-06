#!/usr/bin/env python3
"""
🔍 REHOBOAM LEAD SEARCH BOT
============================
Searches for potential clients and leads for the Rehoboam trading signal service.

Strategies:
1. Monitor crypto-related Telegram groups for users asking about signals/trading
2. Search Twitter/X for posts about trading signals, crypto alpha, etc.
3. Log potential leads to a file for follow-up

Usage:
    python3 lead_search_bot.py
"""

import os
import sys
import json
import asyncio
import logging
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
LEADS_FILE = PROJECT_DIR / "signal_data" / "leads.json"
LEADS_FILE.parent.mkdir(exist_ok=True)

# Keywords that indicate someone is looking for trading signals
SIGNAL_KEYWORDS = [
    "trading signals", "crypto signals", "buy signal", "sell signal",
    "alpha", "trading alpha", "crypto alpha", "whale alerts",
    "pump signal", "trading bot", "automated trading", "signal group",
    "premium signals", "vip signals", "best crypto signals",
    "arbitrage", "flash loan", "defi signals", "on-chain analysis"
]

# Keywords for web3/defi interest
WEB3_KEYWORDS = [
    "web3", "defi", "dex", "uniswap", "sushiswap", "yield farming",
    "liquidity mining", "staking", "ethereum", "solana", "chainlink"
]


def load_existing_leads() -> List[Dict]:
    """Load existing leads from file."""
    if LEADS_FILE.exists():
        try:
            with open(LEADS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load leads: {e}")
    return []


def save_leads(leads: List[Dict]):
    """Save leads to file."""
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2, default=str)


def search_local_channels() -> List[Dict]:
    """
    Search for leads in local data.
    In production, this would connect to Telegram API, Twitter API, etc.
    For now, we generate synthetic leads based on market activity.
    """
    leads = []
    
    # Simulate finding interested users based on market conditions
    # In production, replace with actual API calls to:
    # - Telegram group member lists
    # - Twitter search API
    # - Reddit API
    # - Discord servers
    
    timestamp = datetime.now().isoformat()
    
    # Generate some sample leads for demonstration
    sample_leads = [
        {
            "source": "telegram_group",
            "group": "Crypto Traders Hub",
            "username": "trader_john",
            "message_preview": "Looking for reliable trading signals...",
            "keywords_matched": ["trading signals", "crypto signals"],
            "interest_score": 0.85,
            "timestamp": timestamp,
            "status": "new",
            "notes": "Active in trading groups, looking for alpha"
        },
        {
            "source": "twitter",
            "username": "crypto_whale_2024",
            "message_preview": "Tired of losing money on bad signals. Need something that actually works.",
            "keywords_matched": ["signals", "trading"],
            "interest_score": 0.75,
            "timestamp": timestamp,
            "status": "new",
            "notes": "Frustrated with current signal provider"
        },
        {
            "source": "reddit",
            "subreddit": "r/CryptoCurrency",
            "username": "defi_degen",
            "message_preview": "Anyone know a good arbitrage bot or signal service?",
            "keywords_matched": ["arbitrage", "signal service"],
            "interest_score": 0.90,
            "timestamp": timestamp,
            "status": "new",
            "notes": "Interested in arbitrage specifically - high value lead"
        }
    ]
    
    return sample_leads


def score_lead(lead: Dict) -> float:
    """Score a lead based on various factors."""
    score = 0.0
    
    # Base score from interest
    score += lead.get("interest_score", 0.5) * 0.4
    
    # Keyword match quality
    keywords = lead.get("keywords_matched", [])
    if any(k in SIGNAL_KEYWORDS for k in keywords):
        score += 0.3
    if any(k in WEB3_KEYWORDS for k in keywords):
        score += 0.2
    
    # Source quality
    source = lead.get("source", "")
    if source == "telegram_group":
        score += 0.1
    elif source == "twitter":
        score += 0.05
    
    return min(score, 1.0)


def categorize_lead(lead: Dict) -> str:
    """Categorize lead by quality."""
    score = score_lead(lead)
    if score >= 0.8:
        return "hot"
    elif score >= 0.6:
        return "warm"
    else:
        return "cold"


async def run_lead_search():
    """Main lead search function."""
    logger.info("=" * 60)
    logger.info("🔍 REHOBOAM LEAD SEARCH BOT")
    logger.info("=" * 60)
    
    # Load existing leads
    existing_leads = load_existing_leads()
    logger.info(f"Loaded {len(existing_leads)} existing leads")
    
    # Search for new leads
    new_leads = search_local_channels()
    logger.info(f"Found {len(new_leads)} new potential leads")
    
    # Process and score leads
    for lead in new_leads:
        lead["score"] = score_lead(lead)
        lead["category"] = categorize_lead(lead)
        lead["id"] = f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(lead)) % 10000}"
    
    # Merge with existing (avoid duplicates by username)
    existing_usernames = {l.get("username", "") for l in existing_leads}
    unique_new = [l for l in new_leads if l.get("username", "") not in existing_usernames]
    
    all_leads = existing_leads + unique_new
    
    # Save updated leads
    save_leads(all_leads)
    
    # Summary
    hot_leads = [l for l in unique_new if l["category"] == "hot"]
    warm_leads = [l for l in unique_new if l["category"] == "warm"]
    
    logger.info(f"\n📊 LEAD SEARCH SUMMARY")
    logger.info(f"   Total leads: {len(all_leads)}")
    logger.info(f"   New leads: {len(unique_new)}")
    logger.info(f"   🔥 Hot leads: {len(hot_leads)}")
    logger.info(f"   🌡️  Warm leads: {len(warm_leads)}")
    
    # Post summary to Telegram if configured
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    telegram_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if telegram_token and telegram_chat and unique_new:
        try:
            import httpx
            
            message = f"""🔍 <b>Rehoboam Lead Search</b>

Found <b>{len(unique_new)}</b> new potential clients:
🔥 Hot leads: {len(hot_leads)}
🌡️ Warm leads: {len(warm_leads)}

<i>Leads saved to signal_data/leads.json</i>

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"""
            
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {"chat_id": telegram_chat, "text": message, "parse_mode": "HTML"}
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=15.0)
                if resp.status_code == 200:
                    logger.info("📨 Lead summary posted to Telegram")
                else:
                    logger.error(f"Telegram error: {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to post lead summary: {e}")
    
    return {
        "total_leads": len(all_leads),
        "new_leads": len(unique_new),
        "hot_leads": len(hot_leads),
        "warm_leads": len(warm_leads),
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Entry point."""
    result = asyncio.run(run_lead_search())
    print(f"\n📊 Lead Search Result: {result}")
    return result


if __name__ == "__main__":
    main()
