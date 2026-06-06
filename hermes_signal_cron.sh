#!/bin/bash
# Rehoboam Hermes Signal Bot — 5-minute cron job
# Uses REAL convergence engine v2.0 with risk management

PROJECT_DIR="/home/aryan/free-claude/bittensor/clean_rehoboam_project"
LOG_FILE="$PROJECT_DIR/signal_data/cron.log"
PID_FILE="/tmp/hermes_signal_bot.pid"

# Ensure log directory exists
mkdir -p "$PROJECT_DIR/signal_data"

# Check if already running (prevent overlapping executions)
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "[$(date)] Signal bot already running (PID: $OLD_PID). Skipping." >> "$LOG_FILE"
        exit 0
    fi
fi

# Set environment
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment if it exists
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
fi

# Load environment variables
set -a
[ -f "$PROJECT_DIR/.env" ] && source "$PROJECT_DIR/.env"
set +a

# Run the REAL signal bot (single cycle)
echo "[$(date)] Starting Hermes REAL signal cycle..." >> "$LOG_FILE"
python3 "$PROJECT_DIR/hermes_signal_bot.py" --once --tier BASIC >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date)] ✅ Signal cycle completed successfully" >> "$LOG_FILE"
else
    echo "[$(date)] ❌ Signal cycle failed with code $EXIT_CODE" >> "$LOG_FILE"
fi

# Also run lead search every 30 minutes (at :00 and :30)
MINUTE=$(date +%M)
if [ "$MINUTE" = "00" ] || [ "$MINUTE" = "30" ]; then
    echo "[$(date)] 🔍 Running lead search..." >> "$LOG_FILE"
    python3 "$PROJECT_DIR/lead_search_bot.py" >> "$LOG_FILE" 2>&1 || true
fi

exit 0
