#!/usr/bin/env python3
"""
Rehoboam Sepolia ETH Miner — Automated PoW Faucet
Uses pk910.de PoW faucet to mine Sepolia ETH via browser automation
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import os

WALLET = os.getenv("FLASH_ARB_MASTER", "0x8FD8EAB1954BC0d581E9ab9eE6b217985b031Bd5")
FAUCET_URL = "https://sepolia-faucet.pk910.de"

async def mine_sepolia_eth():
    """Mine Sepolia ETH using PoW faucet with Playwright"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright")
        print("   Then: python3 -m playwright install chromium")
        sys.exit(1)
    
    print(f"🚀 Starting Sepolia ETH miner for wallet: {WALLET}")
    print(f"🔗 Faucet: {FAUCET_URL}")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()
        
        # Navigate to faucet
        await page.goto(FAUCET_URL)
        print("✅ Opened faucet page")
        
        # Fill wallet address
        await page.wait_for_selector("input[name='address']", timeout=10000)
        await page.fill("input[name='address']", WALLET)
        print(f"📝 Filled wallet address: {WALLET}")
        
        # Start mining
        await page.click("button[type='submit']")
        print("⛏️  Mining started! Let it run...")
        print("="*60)
        print("💡 The faucet mines ETH using your browser's CPU.")
        print("💡 Typical yield: 0.05-0.5 ETH per hour depending on CPU.")
        print("💡 Keep this window open. Press Ctrl+C to stop.")
        print("="*60)
        
        # Monitor mining progress
        try:
            while True:
                await asyncio.sleep(30)
                try:
                    # Try to read the hashrate or balance
                    hashrate = await page.inner_text("#hashrate", timeout=5000)
                    balance = await page.inner_text("#balance", timeout=5000)
                    print(f"⛏️  Hashrate: {hashrate.strip()} | Balance: {balance.strip()}")
                except:
                    # Check if we got a success message
                    content = await page.content()
                    if "success" in content.lower() or "claimed" in content.lower():
                        print("🎉 ETH claimed successfully!")
                        break
        except KeyboardInterrupt:
            print("\n🛑 Stopping miner...")
        
        await browser.close()
        print("✅ Browser closed")

if __name__ == "__main__":
    asyncio.run(mine_sepolia_eth())
