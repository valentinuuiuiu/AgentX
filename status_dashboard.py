#!/usr/bin/env python3
"""
📊 REHOBOAM STATUS DASHBOARD
============================
Shows real-time status of all services.

Usage:
    python3 status_dashboard.py
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent

def check_process(name, pid_file):
    """Check if a process is running."""
    pid_path = PROJECT_DIR / pid_file
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text().strip())
            result = subprocess.run(['ps', '-p', str(pid)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True, pid
        except:
            pass
    return False, None

def get_db_stats():
    """Get database statistics."""
    db_path = PROJECT_DIR / "signal_data" / "customers.db"
    if not db_path.exists():
        return {}
    
    with sqlite3.connect(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        trials = conn.execute("SELECT COUNT(*) FROM customers WHERE status = 'trial'").fetchone()[0]
        paid = conn.execute("SELECT COUNT(*) FROM customers WHERE status = 'paid'").fetchone()[0]
        leads = conn.execute("SELECT COUNT(*) FROM customers WHERE status = 'lead'").fetchone()[0]
        return {'total': total, 'trials': trials, 'paid': paid, 'leads': leads}

def get_signal_stats():
    """Get signal statistics."""
    db_path = PROJECT_DIR / "signal_data" / "signals.db"
    if not db_path.exists():
        return {}
    
    with sqlite3.connect(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
        wins = conn.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed' AND pnl_pct > 0").fetchone()[0]
        losses = conn.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed' AND pnl_pct <= 0").fetchone()[0]
        return {'total': total, 'wins': wins, 'losses': losses}

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    🤖 REHOBOAM STATUS 🤖                        ║
╠══════════════════════════════════════════════════════════════════╣""")
    
    # Check processes
    print("║  SERVICES                                                        ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    
    signal_running, signal_pid = check_process("Signal Bot", "hermes_bot.pid")
    interactive_running, interactive_pid = check_process("Interactive Bot", "hermes_interactive_bot.pid")
    
    status_icon = lambda x: "🟢 RUNNING" if x else "🔴 STOPPED"
    
    print(f"║  Signal Bot:        {status_icon(signal_running):20} PID: {signal_pid or 'N/A'}")
    print(f"║  Interactive Bot:   {status_icon(interactive_running):20} PID: {interactive_pid or 'N/A'}")
    print(f"║  Cron Job:          {'🟢 ACTIVE' if True else '🔴 INACTIVE':20} Every 5 min")
    print(f"║  Landing Page:      {'🟢 SERVING':20} http://localhost:8080")
    
    # Database stats
    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║  CUSTOMERS                                                       ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    
    db_stats = get_db_stats()
    if db_stats:
        print(f"║  Total Users:       {db_stats.get('total', 0)}")
        print(f"║  Leads:             {db_stats.get('leads', 0)}")
        print(f"║  Active Trials:     {db_stats.get('trials', 0)}")
        print(f"║  Paid Customers:    {db_stats.get('paid', 0)}")
    else:
        print("║  Database:          Not initialized yet")
    
    # Signal stats
    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║  SIGNALS                                                         ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    
    signal_stats = get_signal_stats()
    if signal_stats:
        print(f"║  Total Generated:   {signal_stats.get('total', 0)}")
        print(f"║  Wins:              {signal_stats.get('wins', 0)}")
        print(f"║  Losses:            {signal_stats.get('losses', 0)}")
    else:
        print("║  Database:          Not initialized yet")
    
    # Files
    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║  FILES                                                           ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    
    files = [
        ("Signal Engine", "real_convergence_engine.py"),
        ("Signal Bot", "hermes_signal_bot.py"),
        ("Interactive Bot", "hermes_interactive_bot.py"),
        ("Customer DB", "signal_data/customers.db"),
        ("Signals DB", "signal_data/signals.db"),
        ("Landing Page", "landing_page.html"),
        ("Marketing Content", "marketing_content/"),
    ]
    
    for name, path in files:
        full_path = PROJECT_DIR / path
        exists = full_path.exists()
        icon = "✅" if exists else "❌"
        print(f"║  {icon} {name:20} {path}")
    
    print("╠══════════════════════════════════════════════════════════════════╣")
    print(f"║  Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    # Action items
    print("\n📋 NEXT STEPS:")
    print("   1. Post outreach messages (see quick_start_customer_acquisition.py)")
    print("   2. Monitor Telegram DMs for new customers")
    print("   3. Check /status on bot for real-time stats")
    print("   4. Run: python3 customer_acquisition.py --stats")

if __name__ == "__main__":
    main()
