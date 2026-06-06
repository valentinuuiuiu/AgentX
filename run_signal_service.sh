#!/bin/bash
# 🏔️ REHOBOAM CRYPTO SIGNAL SERVICE — 24/7 RUNNER
# Usage: ./run_signal_service.sh [start|stop|status|logs]

SERVICE_DIR="/home/aryan/free-claude/bittensor/clean_rehoboam_project"
VENV_PYTHON="$SERVICE_DIR/signal_venv/bin/python"
SCRIPT="$SERVICE_DIR/crypto_signal_service.py"
PIDFILE="$SERVICE_DIR/signal_service.pid"
LOGFILE="$SERVICE_DIR/signal_data/service.log"

case "$1" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
      echo "✅ Signal service already running (PID: $(cat $PIDFILE))"
      exit 0
    fi
    echo "🏔️ Starting Rehoboam Crypto Signal Service..."
    mkdir -p "$SERVICE_DIR/signal_data"
    nohup "$VENV_PYTHON" "$SCRIPT" >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    echo "✅ Started with PID $(cat $PIDFILE)"
    echo "📊 Logs: tail -f $LOGFILE"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      PID=$(cat "$PIDFILE")
      kill "$PID" 2>/dev/null && echo "🛑 Stopped signal service (PID: $PID)" || echo "⚠️ Process not found"
      rm -f "$PIDFILE"
    else
      echo "⚠️ No PID file found. Service may not be running."
    fi
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
      echo "✅ Signal service is RUNNING (PID: $(cat $PIDFILE))"
      echo "📊 Recent signals:"
      ls -la "$SERVICE_DIR/signal_data/signals.json" 2>/dev/null && echo "   $(wc -l < $SERVICE_DIR/signal_data/signals.json) lines in signal history"
    else
      echo "❌ Signal service is NOT running"
    fi
    ;;
  logs)
    tail -n 50 -f "$LOGFILE"
    ;;
  once)
    echo "🔍 Running one cycle..."
    "$VENV_PYTHON" "$SCRIPT" --once
    ;;
  *)
    echo "🏔️ Rehoboam Crypto Signal Service"
    echo "Usage: $0 {start|stop|status|logs|once}"
    exit 1
    ;;
esac
