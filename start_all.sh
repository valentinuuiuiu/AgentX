#!/bin/bash
# 🚀 REHOBOAM MASTER STARTUP
# ============================
# Starts ALL services with one command

PROJECT_DIR="/home/aryan/free-claude/bittensor/clean_rehoboam_project"
cd "$PROJECT_DIR" || exit 1

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    🚀 REHOBOAM STARTING 🚀                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Start signal bot + interactive bot
echo "🤖 Starting Hermes bots..."
bash start_hermes_bot.sh

# 2. Start landing page server
echo ""
echo "🌐 Starting landing page server..."
if ! lsof -i :8080 > /dev/null 2>&1; then
    python3 -m http.server 8080 > /dev/null 2>&1 &
    echo "   ✅ Landing page: http://localhost:8080/landing_page.html"
else
    echo "   ✅ Landing page already running on port 8080"
fi

# 3. Show status
echo ""
echo "📊 System Status:"
echo "───────────────────────────────────────────────────────────────────"
sleep 2
python3 status_dashboard.py

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ REHOBOAM IS LIVE ✅                         ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║                                                                  ║"
echo "║  🤖 Signal Bot:        Posting every 5 minutes                   ║"
echo "║  💬 Interactive Bot:   Ready for customer conversations          ║"
echo "║  🌐 Landing Page:      http://localhost:8080                     ║"
echo "║  📊 Dashboard:         python3 status_dashboard.py               ║"
echo "║                                                                  ║"
echo "║  📱 Telegram:          @web4_bot_nobot                           ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🎯 GO GET CUSTOMERS:"
echo "   python3 quick_start_customer_acquisition.py"
