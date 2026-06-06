#!/usr/bin/env python3
"""
🏥 REHOBOAM HEALTH CHECK
========================
Monitors all services and restarts if needed.
Run this every minute via cron for 24/7 uptime.

Usage:
    python3 health_check.py
    
Add to crontab:
    * * * * * /home/aryan/free-claude/bittensor/clean_rehoboam_project/health_check.py
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
LOG_FILE = PROJECT_DIR / "signal_data" / "health.log"

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def check_process(pid_file, name, start_cmd):
    """Check if process is running, restart if not."""
    pid_path = PROJECT_DIR / pid_file
    
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text().strip())
            result = subprocess.run(['ps', '-p', str(pid)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True
        except:
            pass
    
    # Process not running, restart it
    log(f"⚠️  {name} not running. Restarting...")
    
    # Change to project directory
    os.chdir(PROJECT_DIR)
    
    # Activate venv if exists
    venv = PROJECT_DIR / ".venv" / "bin" / "activate"
    if venv.exists():
        os.environ['PATH'] = str(PROJECT_DIR / ".venv" / "bin") + ":" + os.environ.get('PATH', '')
    
    # Start process
    log_file = PROJECT_DIR / "signal_data" / f"{name.lower().replace(' ', '_')}.log"
    proc = subprocess.Popen(
        start_cmd,
        stdout=open(log_file, 'a'),
        stderr=subprocess.STDOUT,
        cwd=PROJECT_DIR
    )
    
    # Save PID
    pid_path.write_text(str(proc.pid))
    log(f"✅ {name} restarted (PID: {proc.pid})")
    return True

def check_disk_space():
    """Check if disk is getting full."""
    result = subprocess.run(['df', '-h', str(PROJECT_DIR)], 
                          capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    if len(lines) > 1:
        usage = lines[1].split()
        if len(usage) >= 5:
            percent = usage[4].replace('%', '')
            if int(percent) > 90:
                log(f"🚨 DISK SPACE WARNING: {usage[4]} full!")
                return False
    return True

def check_database():
    """Check database integrity."""
    db_path = PROJECT_DIR / "signal_data" / "customers.db"
    if db_path.exists():
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute("SELECT 1 FROM customers LIMIT 1")
            return True
        except:
            log("🚨 Customer database corrupted!")
            return False
    return True

def main():
    LOG_FILE.parent.mkdir(exist_ok=True)
    
    log("🏥 Health check starting...")
    
    # Check signal bot
    check_process(
        "hermes_bot.pid",
        "Signal Bot",
        [sys.executable, str(PROJECT_DIR / "hermes_signal_bot.py")]
    )
    
    # Check interactive bot
    check_process(
        "hermes_interactive_bot.pid",
        "Interactive Bot",
        [sys.executable, str(PROJECT_DIR / "hermes_interactive_bot.py")]
    )
    
    # Check disk space
    check_disk_space()
    
    # Check database
    check_database()
    
    log("✅ Health check complete")

if __name__ == "__main__":
    main()
