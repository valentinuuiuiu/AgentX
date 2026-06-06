#!/bin/bash
# 🏔️ WAKE UP ALL AGENTS — Rehoboam Full Deployment
# ==================================================
# Launches EVERY agent at once. No more sleeping.
# 
# Usage:
#   chmod +x wake_up_all_agents.sh
#   ./wake_up_all_agents.sh

set -e

PROJECT_DIR="/home/aryan/free-claude/bittensor/clean_rehoboam_project"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🏔️  WAKING UP ALL REHOBOAM AGENTS  🏔️                     ║"
echo "║                                                               ║"
echo "║   "No more sleeping. We mine 24/7."                         ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_DIR"
source .venv/bin/activate

# Function to start a process
start_agent() {
    local name="$1"
    local cmd="$2"
    local logfile="$LOG_DIR/${name}.log"
    local pidfile="$PID_DIR/${name}.pid"
    
    # Check if already running
    if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        echo "  ✅ $name already running (PID: $(cat "$pidfile"))"
        return 0
    fi
    
    echo "  🚀 Starting $name..."
    nohup bash -c "$cmd" > "$logfile" 2>&1 &
    echo $! > "$pidfile"
    sleep 2
    
    if kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        echo "  ✅ $name started (PID: $(cat "$pidfile"))"
    else
        echo "  ❌ $name failed to start! Check $logfile"
    fi
}

# 1. Crypto Signal Service (24/7 price monitoring)
echo "📡 [1/6] Signal Service"
start_agent "signal_service" "cd $PROJECT_DIR && python3 crypto_signal_service.py"

# 2. Hermes Signal Bot (convergence + Telegram)
echo ""
echo "🏔️  [2/6] Hermes Signal Bot"
start_agent "hermes_bot" "cd $PROJECT_DIR && python3 hermes_signal_bot.py"

# 3. Rehoboam Telegram Bot (subscription management)
echo ""
echo "💬 [3/6] Telegram Subscription Bot"
start_agent "telegram_bot" "cd $PROJECT_DIR && python3 rehoboam_telegram_bot.py"

# 4. TAO Price Monitor (background price tracking)
echo ""
echo "💰 [4/6] TAO Price Monitor"
start_agent "tao_monitor" "cd $PROJECT_DIR && python3 tao_price_monitor.py --watch --interval 300"

# 5. FastAPI Server (if not already running via podman)
echo ""
echo "🌐 [5/6] FastAPI Server"
if curl -sf http://localhost:5002/api/status >/dev/null 2>&1; then
    echo "  ✅ API already running on port 5002"
else
    start_agent "api_server" "cd $PROJECT_DIR && uvicorn api_server:app --host 0.0.0.0 --port 5002 --reload"
fi

# 6. Trading Agents (if not already running)
echo ""
echo "🤖 [6/6] Trading Agents"
if curl -sf http://localhost:3700/health >/dev/null 2>&1; then
    echo "  ✅ Trading agents already running on port 3700"
else
    echo "  ⚠️  Trading agents not running. Start manually:"
    echo "     python3 trading_agents.py or podman compose up trading-agents"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ✅ ALL AGENTS AWAKE AND MINING                             ║"
echo "║                                                               ║"
echo "║   📡 Signal Service    → signal_data/signals.json           ║"
echo "║   🏔️  Hermes Bot       → Telegram every 15 min             ║"
echo "║   💬 Telegram Bot      → @web4_bot_nobot                    ║"
echo "║   💰 TAO Monitor       → signal_data/tao_price.json         ║"
echo "║   🌐 API Server        → http://localhost:5002              ║"
echo "║                                                               ║"
echo "║   Logs:  $LOG_DIR                                           ║"
echo "║   PIDs:  $PID_DIR                                           ║"
echo "║                                                               ║"
echo "║   Commands:                                                   ║"
echo "║     ./wake_up_all_agents.sh status   → Show all agents      ║"
echo "║     ./wake_up_all_agents.sh stop     → Stop all agents      ║"
echo "║     ./wake_up_all_agents.sh restart  → Restart all agents   ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Status command
if [ "$1" = "status" ]; then
    echo "=== AGENT STATUS ==="
    for pidfile in "$PID_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            name=$(basename "$pidfile" .pid)
            pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                echo "  ✅ $name (PID: $pid)"
            else
                echo "  ❌ $name (PID: $pid) — DEAD"
            fi
        fi
    done
fi

# Stop command
if [ "$1" = "stop" ]; then
    echo "=== STOPPING ALL AGENTS ==="
    for pidfile in "$PID_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            name=$(basename "$pidfile" .pid)
            pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                echo "  🛑 Stopping $name (PID: $pid)..."
                kill "$pid" 2>/dev/null || true
                rm "$pidfile"
            fi
        fi
    done
    echo "✅ All agents stopped"
fi

# Restart command
if [ "$1" = "restart" ]; then
    echo "=== RESTARTING ALL AGENTS ==="
    $0 stop
    sleep 2
    $0
fi