#!/bin/bash

cd "$(dirname "$0")"

echo "🏔️  REHOBOAM MONETIZATION STARTUP"
echo "================================="

# Make sure bot_data and signal_data exist
mkdir -p bot_data signal_data logs

# Check dependencies
echo "[1] Checking dependencies..."
python3 -c "import pandas, aiohttp, httpx, telegram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install pandas aiohttp httpx python-telegram-bot python-dotenv
fi

echo "[2] Starting monetization engine..."
echo "Mode: FULL (bot + signals + marketing)"
echo "Interval: 15 minutes"
echo "Tiers: Free, Basic ($49), Pro ($149), VIP ($299)"
echo ""

python3 rehoboam_monetization_bot.py --mode full
