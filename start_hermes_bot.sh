#!/bin/bash
# 🏔️ HERMES SIGNAL BOT — 24/7 Revenue Engine
# ==========================================
# Start this and let it run. It makes money while you sleep.
#
# Usage:
#   ./start_hermes_bot.sh              # Start in background
#   ./start_hermes_bot.sh --foreground # Start in foreground (for debugging)
#   ./start_hermes_bot.sh --stop       # Stop the bot
#   ./start_hermes_bot.sh --status     # Check if running

PROJECT_DIR="/home/aryan/free-claude/bittensor/clean_rehoboam_project"
PIDFILE="$PROJECT_DIR/hermes_bot.pid"
INTERACTIVE_PIDFILE="$PROJECT_DIR/hermes_interactive_bot.pid"
LOGFILE="$PROJECT_DIR/signal_data/hermes_bot.log"
INTERACTIVE_LOGFILE="$PROJECT_DIR/signal_data/hermes_interactive_bot.log"
VENV="$PROJECT_DIR/.venv/bin/activate"

cd "$PROJECT_DIR" || exit 1

start_bot() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "🏔️  Hermes Signal Bot is already running (PID: $(cat $PIDFILE))"
    else
        echo "🏔️  Starting Hermes Signal Bot..."
        source "$VENV"
        nohup python3 hermes_signal_bot.py > "$LOGFILE" 2>&1 &
        echo $! > "$PIDFILE"
        echo "✅ Hermes Signal Bot started (PID: $(cat $PIDFILE))"
        echo "   Logs: tail -f $LOGFILE"
        echo "   Signals: tail -f $PROJECT_DIR/signal_data/convergence_signals.json"
    fi

    # Start interactive bot too
    if [ -f "$INTERACTIVE_PIDFILE" ] && kill -0 "$(cat "$INTERACTIVE_PIDFILE")" 2>/dev/null; then
        echo "🤖  Hermes Interactive Bot is already running (PID: $(cat $INTERACTIVE_PIDFILE))"
    else
        echo "🤖  Starting Hermes Interactive Bot..."
        source "$VENV"
        nohup python3 hermes_interactive_bot.py > "$INTERACTIVE_LOGFILE" 2>&1 &
        echo $! > "$INTERACTIVE_PIDFILE"
        echo "✅ Hermes Interactive Bot started (PID: $(cat $INTERACTIVE_PIDFILE))"
        echo "   Logs: tail -f $INTERACTIVE_LOGFILE"
    fi
}

stop_bot() {
    # Stop signal bot
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 Stopping Hermes Signal Bot (PID: $PID)..."
            kill "$PID"
            rm -f "$PIDFILE"
            echo "✅ Hermes Signal Bot stopped"
        else
            echo "⚠️  Hermes Signal Bot not running (stale PID file)"
            rm -f "$PIDFILE"
        fi
    else
        echo "⚠️  Hermes Signal Bot not running"
    fi

    # Stop interactive bot
    if [ -f "$INTERACTIVE_PIDFILE" ]; then
        PID=$(cat "$INTERACTIVE_PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 Stopping Hermes Interactive Bot (PID: $PID)..."
            kill "$PID"
            rm -f "$INTERACTIVE_PIDFILE"
            echo "✅ Hermes Interactive Bot stopped"
        else
            echo "⚠️  Hermes Interactive Bot not running (stale PID file)"
            rm -f "$INTERACTIVE_PIDFILE"
        fi
    else
        echo "⚠️  Hermes Interactive Bot not running"
    fi
}

status_bot() {
    # Signal bot status
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "✅ Hermes Signal Bot is RUNNING (PID: $(cat $PIDFILE))"
        echo "   Uptime: $(ps -o etime= -p "$(cat $PIDFILE)" 2>/dev/null || echo 'unknown')"
        echo "   Logs: tail -f $LOGFILE"
    else
        echo "❌ Hermes Signal Bot is NOT running"
    fi

    echo ""

    # Interactive bot status
    if [ -f "$INTERACTIVE_PIDFILE" ] && kill -0 "$(cat "$INTERACTIVE_PIDFILE")" 2>/dev/null; then
        echo "✅ Hermes Interactive Bot is RUNNING (PID: $(cat $INTERACTIVE_PIDFILE))"
        echo "   Uptime: $(ps -o etime= -p "$(cat $INTERACTIVE_PIDFILE)" 2>/dev/null || echo 'unknown')"
        echo "   Logs: tail -f $INTERACTIVE_LOGFILE"
    else
        echo "❌ Hermes Interactive Bot is NOT running"
    fi
}

case "${1:-}" in
    --stop)
        stop_bot
        ;;
    --status)
        status_bot
        ;;
    --foreground)
        echo "🏔️  Starting Hermes Bot in foreground..."
        source "$VENV"
        python3 hermes_signal_bot.py
        ;;
    *)
        start_bot
        ;;
esac