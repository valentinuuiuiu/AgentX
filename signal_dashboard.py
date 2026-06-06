#!/usr/bin/env python3
"""
🏔️ REHOBOAM SIGNAL DASHBOARD
Quick view of signal performance and current status.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

DATA_DIR = Path("/home/aryan/free-claude/bittensor/clean_rehoboam_project/signal_data")
SIGNALS_FILE = DATA_DIR / "signals.json"

def show_dashboard():
    print("\n" + "="*60)
    print("🏔️  REHOBOAM CRYPTO SIGNAL DASHBOARD")
    print("="*60)
    
    # Check if service is running
    pidfile = Path("/home/aryan/free-claude/bittensor/clean_rehoboam_project/signal_service.pid")
    if pidfile.exists():
        pid = pidfile.read_text().strip()
        print(f"\n✅ Service RUNNING (PID: {pid})")
    else:
        print(f"\n❌ Service NOT RUNNING")
    
    # Signal stats
    if not SIGNALS_FILE.exists():
        print("\n📭 No signals generated yet.")
        print("   The service checks every 15 minutes.")
        print("   Signals appear when market conditions meet criteria.")
        return
    
    with open(SIGNALS_FILE) as f:
        signals = json.load(f)
    
    if not signals:
        print("\n📭 No signals in history.")
        return
    
    df = pd.DataFrame(signals)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"\n📊 SIGNAL STATISTICS")
    print(f"   Total signals: {len(df)}")
    print(f"   BUY signals: {len(df[df['action'] == 'BUY'])}")
    print(f"   SELL signals: {len(df[df['action'] == 'SELL'])}")
    print(f"   Average strength: {df['strength'].mean():.1%}")
    
    # Last 24h
    last_24h = df[df['timestamp'] > datetime.now() - timedelta(hours=24)]
    print(f"   Signals (last 24h): {len(last_24h)}")
    
    # Recent signals
    print(f"\n🚨 RECENT SIGNALS (last 10)")
    recent = df.tail(10).sort_values('timestamp', ascending=False)
    for _, row in recent.iterrows():
        emoji = "🟢" if row['action'] == 'BUY' else "🔴"
        print(f"   {emoji} {row['action']} {row['pair']} @ ${row['price']:,.2f} | "
              f"Strength: {row['strength']:.0%} | {row['timeframe']} | "
              f"{row['timestamp'].strftime('%m-%d %H:%M')}")
        print(f"      Reason: {row['reason'][:60]}...")
    
    # Pairs with most signals
    print(f"\n📈 MOST ACTIVE PAIRS")
    pair_counts = df['pair'].value_counts().head(5)
    for pair, count in pair_counts.items():
        print(f"   {pair}: {count} signals")
    
    print("\n" + "="*60)
    print("Next check: Every 15 minutes")
    print("Logs: tail -f /home/aryan/free-claude/bittensor/clean_rehoboam_project/signal_data/service.log")
    print("="*60 + "\n")

if __name__ == "__main__":
    show_dashboard()
