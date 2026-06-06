#!/bin/bash
# 🏔️ REHOBOAM UNIFIED LAUNCHER
# Starts: Position Generator + Telegram Bot
# This is the money machine.

SERVICE_DIR="/home/aryan/free-claude/bittensor/clean_rehoboam_project"
VENV_PYTHON="$SERVICE_DIR/signal_venv/bin/python"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

case "$1" in
  start)
    echo -e "${GREEN}🏔️  Starting Rehoboam Money Machine...${NC}"
    
    # Start Position Generator
    if [ ! -f "$SERVICE_DIR/position_generator.pid" ]; then
      echo -e "${YELLOW}📈 Starting Position Generator...${NC}"
      cd "$SERVICE_DIR"
      nohup "$VENV_PYTHON" "$SERVICE_DIR/rehoboam_positions.py" >> "$SERVICE_DIR/position_data/service.log" 2>&1 &
      echo $! > "$SERVICE_DIR/position_generator.pid"
      echo -e "${GREEN}✅ Position Generator started (PID: $(cat $SERVICE_DIR/position_generator.pid))${NC}"
    else
      echo -e "${YELLOW}⚠️  Position Generator already running${NC}"
    fi
    
    # Start Telegram Bot (if token configured)
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
      if [ ! -f "$SERVICE_DIR/telegram_bot.pid" ]; then
        echo -e "${YELLOW}📱 Starting Telegram Bot...${NC}"
        cd "$SERVICE_DIR"
        nohup "$VENV_PYTHON" "$SERVICE_DIR/rehoboam_telegram_bot.py" >> "$SERVICE_DIR/bot_data/bot.log" 2>&1 &
        echo $! > "$SERVICE_DIR/telegram_bot.pid"
        echo -e "${GREEN}✅ Telegram Bot started (PID: $(cat $SERVICE_DIR/telegram_bot.pid))${NC}"
      else
        echo -e "${YELLOW}⚠️  Telegram Bot already running${NC}"
      fi
    else
      echo -e "${RED}❌ TELEGRAM_BOT_TOKEN not set. Bot not started.${NC}"
      echo -e "${YELLOW}   Set it with: export TELEGRAM_BOT_TOKEN=your_token${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}🏔️  REHOBOAM IS LIVE${NC}"
    echo -e "${GREEN}   Position Generator: tail -f $SERVICE_DIR/position_data/service.log${NC}"
    echo -e "${GREEN}   Telegram Bot: tail -f $SERVICE_DIR/bot_data/bot.log${NC}"
    ;;
    
  stop)
    echo -e "${RED}🛑 Stopping Rehoboam...${NC}"
    
    if [ -f "$SERVICE_DIR/position_generator.pid" ]; then
      kill $(cat "$SERVICE_DIR/position_generator.pid") 2>/dev/null
      rm -f "$SERVICE_DIR/position_generator.pid"
      echo -e "${GREEN}✅ Position Generator stopped${NC}"
    fi
    
    if [ -f "$SERVICE_DIR/telegram_bot.pid" ]; then
      kill $(cat "$SERVICE_DIR/telegram_bot.pid") 2>/dev/null
      rm -f "$SERVICE_DIR/telegram_bot.pid"
      echo -e "${GREEN}✅ Telegram Bot stopped${NC}"
    fi
    
    echo -e "${GREEN}🏔️  Rehoboam stopped.${NC}"
    ;;
    
  status)
    echo -e "${YELLOW}🏔️  REHOBOAM STATUS${NC}"
    echo "====================="
    
    if [ -f "$SERVICE_DIR/position_generator.pid" ] && kill -0 $(cat "$SERVICE_DIR/position_generator.pid") 2>/dev/null; then
      echo -e "${GREEN}📈 Position Generator: RUNNING${NC}"
    else
      echo -e "${RED}📈 Position Generator: STOPPED${NC}"
    fi
    
    if [ -f "$SERVICE_DIR/telegram_bot.pid" ] && kill -0 $(cat "$SERVICE_DIR/telegram_bot.pid") 2>/dev/null; then
      echo -e "${GREEN}📱 Telegram Bot: RUNNING${NC}"
    else
      echo -e "${RED}📱 Telegram Bot: STOPPED${NC}"
    fi
    
    # Show stats
    if [ -f "$SERVICE_DIR/position_data/positions.json" ]; then
      TOTAL=$(python3 -c "import json; print(len(json.load(open('$SERVICE_DIR/position_data/positions.json'))))" 2>/dev/null || echo "0")
      echo -e "${GREEN}📊 Total Positions Generated: $TOTAL${NC}"
    fi
    
    if [ -f "$SERVICE_DIR/bot_data/users.json" ]; then
      USERS=$(python3 -c "import json; print(len(json.load(open('$SERVICE_DIR/bot_data/users.json'))))" 2>/dev/null || echo "0")
      echo -e "${GREEN}👥 Total Users: $USERS${NC}"
    fi
    ;;
    
  test)
    echo -e "${YELLOW}🔍 Running one position cycle...${NC}"
    cd "$SERVICE_DIR"
    "$VENV_PYTHON" "$SERVICE_DIR/rehoboam_positions.py" --once --pairs BTC-USD ETH-USD
    ;;
    
  install)
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    cd "$SERVICE_DIR"
    source signal_venv/bin/activate
    pip install python-telegram-bot pandas numpy aiohttp
    echo -e "${GREEN}✅ Dependencies installed${NC}"
    ;;
    
  *)
    echo "🏔️  REHOBOAM UNIFIED LAUNCHER"
    echo ""
    echo "Usage: $0 {start|stop|status|test|install}"
    echo ""
    echo "Commands:"
    echo "  start   - Start Position Generator + Telegram Bot"
    echo "  stop    - Stop all services"
    echo "  status  - Check service status"
    echo "  test    - Run one position cycle"
    echo "  install - Install dependencies"
    echo ""
    echo "Environment variables:"
    echo "  TELEGRAM_BOT_TOKEN  - Required for Telegram bot"
    echo "  TELEGRAM_CHAT_ID    - Default channel for positions"
    ;;
esac
