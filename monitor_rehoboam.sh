#!/bin/bash

# Rehoboam Monitoring Script
# Monitors all services for 72 hours and ensures Bittensor integration works

LOG_FILE="/tmp/rehoboam_monitor.log"
DURATION_HOURS=72
CHECK_INTERVAL=300  # 5 minutes

echo "🚀 Starting Rehoboam Monitor for $DURATION_HOURS hours" | tee -a "$LOG_FILE"
echo "📊 Check interval: $CHECK_INTERVAL seconds" | tee -a "$LOG_FILE"
echo "⏰ Started at: $(date)" | tee -a "$LOG_FILE"

# Function to check service status
check_service() {
    local service=$1
    local url=$2
    local timeout=10

    # Special timeout for TradingAgents during analysis
    if [[ "$service" == "TradingAgents" ]]; then
        timeout=60
    fi

    if curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo "✅ $service: ONLINE"
        return 0
    else
        echo "❌ $service: OFFLINE"
        return 1
    fi
}

# Function to check trading with Ollama
check_trading_analysis() {
    echo "🤖 Testing Trading Analysis with Ollama..."

    # Test with BTC-USD using Ollama
    response=$(curl -s -X POST http://localhost:3700/analyze \
        -H "Content-Type: application/json" \
        -d '{"ticker":"BTC-USD", "llm_provider":"ollama"}' 2>/dev/null)

    if echo "$response" | grep -q '"decision"'; then
        decision=$(echo "$response" | grep -o '"decision":"[^"]*"' | cut -d'"' -f4)
        confidence=$(echo "$response" | grep -o '"confidence":[0-9.]*' | cut -d':' -f2)
        provider=$(echo "$response" | grep -o '"provider":"[^"]*"' | cut -d'"' -f4)

        echo "📈 Trading Analysis: $decision (Confidence: $confidence, Provider: $provider)"
        return 0
    else
        echo "❌ Trading Analysis Failed"
        return 1
    fi
}

# Main monitoring loop
end_time=$(( $(date +%s) + DURATION_HOURS * 3600 ))
check_count=0

while [ $(date +%s) -lt $end_time ]; do
    check_count=$((check_count + 1))
    echo "" | tee -a "$LOG_FILE"
    echo "=== Check #$check_count - $(date) ===" | tee -a "$LOG_FILE"

    # Check all services
    services=(
        "Frontend:http://localhost:5001"
        "API:http://localhost:5002"
        "TradingAgents:http://localhost:3700/health"
        "MCP Registry:http://localhost:3001/health"
        "Consciousness:http://localhost:3600/health"
        "Ollama:http://localhost:11434/api/tags"
    )

    online_count=0
    total_services=${#services[@]}

    for service in "${services[@]}"; do
        name=$(echo "$service" | cut -d':' -f1)
        url=$(echo "$service" | cut -d':' -f2-)

        if check_service "$name" "$url"; then
            online_count=$((online_count + 1))
        fi
    done

    # Check trading analysis if services are up
    if [ $online_count -eq $total_services ]; then
        check_trading_analysis | tee -a "$LOG_FILE"
    else
        echo "⚠️  Skipping trading analysis - not all services online" | tee -a "$LOG_FILE"
    fi

    # Calculate uptime percentage
    uptime_pct=$((online_count * 100 / total_services))
    echo "📊 Uptime: $online_count/$total_services services ($uptime_pct%)" | tee -a "$LOG_FILE"

    # Sleep until next check
    echo "⏳ Next check in $CHECK_INTERVAL seconds..." | tee -a "$LOG_FILE"
    sleep $CHECK_INTERVAL

done

echo "" | tee -a "$LOG_FILE"
echo "🎉 Monitoring completed after $DURATION_HOURS hours" | tee -a "$LOG_FILE"
echo "🕒 Ended at: $(date)" | tee -a "$LOG_FILE"
echo "📋 Final log: $LOG_FILE" | tee -a "$LOG_FILE"