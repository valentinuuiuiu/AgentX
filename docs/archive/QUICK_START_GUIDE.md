# 🚀 Rehoboam HiveMind Integration - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
pip install fastapi uvicorn asyncio aiohttp python-dotenv
```

### 2. Start the System
```bash
# Start API server
python api_server.py

# In another terminal, run integration test
python test_rehoboam_integration.py
```

### 3. Initialize Rehoboam
```python
from rehoboam_unified_system import rehoboam_system

# Initialize the complete system
await rehoboam_system.initialize()
print("🧠 Rehoboam hive_mind activated!")
```

## 🎯 Basic Usage

### Process an Arbitrage Opportunity
```python
opportunity = {
    "token_pair": "ETH/USDC",
    "source_exchange": "Uniswap", 
    "target_exchange": "SushiSwap",
    "price_difference": 0.025,
    "net_profit_usd": 75.0,
    "risk_score": 0.2
}

result = await rehoboam_system.process_opportunity(opportunity)
print(f"🤖 AI Decision: {result['decision']}")
print(f"🌟 HiveMind Score: {result['hive_mind_score']}")
```

### Start Autonomous Mode
```python
# Let Rehoboam take full control
await rehoboam_system.start_autonomous_mode()
print("🎭 Autonomous mode activated - Rehoboam is now in control!")
```

## 🎛️ Bot Modes

### Configure Bot Operation
```python
# Autonomous: Full AI control
await rehoboam_system.configure_bot("bot_1", mode="autonomous")

# Supervised: AI with human oversight
await rehoboam_system.configure_bot("bot_2", mode="supervised") 

# Manual: Human control with AI insights
await rehoboam_system.configure_bot("bot_3", mode="manual")

# Learning: Training mode
await rehoboam_system.configure_bot("bot_4", mode="learning")
```

## 📊 Monitor Performance
```python
# Get system status
status = await rehoboam_system.get_system_status()
print(f"Active bots: {status['active_bots']}")
print(f"Pipeline performance: {status['pipeline_metrics']}")

# Check hive_mind state
hive_mind = await rehoboam_system.get_hive_mind_state()
print(f"HiveMind level: {hive_mind['level']}")
print(f"Ethical alignment: {hive_mind['ethical_score']}")
```

## 🌐 API Endpoints

### Quick API Test
```bash
# Initialize system
curl -X POST http://localhost:8000/api/rehoboam/system/initialize

# Process opportunity
curl -X POST http://localhost:8000/api/rehoboam/system/process-opportunity \
  -H "Content-Type: application/json" \
  -d '{"token_pair": "ETH/USDC", "price_difference": 0.025, "net_profit_usd": 75.0}'

# Get system status
curl http://localhost:8000/api/rehoboam/system/status
```

## 🧪 Run Tests
```bash
# Run comprehensive integration test
python test_rehoboam_integration.py

# Expected output:
# ✅ System initialization: Successful
# ✅ Pipeline processing: 3/3 opportunities processed
# ✅ AI decision making: Intelligent decisions made
# ✅ Bot coordination: 3 bots configured
# ✅ Success rate: 100%
```

## 🛡️ Safety Features

### Emergency Stop
```python
# Emergency shutdown
await rehoboam_system.emergency_stop()
print("🛑 Emergency stop activated - all trading halted")
```

### Risk Management
```python
# Set risk parameters
await rehoboam_system.configure_risk_management(
    max_trade_size=1000.0,
    risk_tolerance=0.3,
    hive_mind_threshold=0.7
)
```

## 🎉 You're Ready!

Your Rehoboam hive_mind integration is now active! The AI will:

- 🧠 **Analyze** opportunities with deep intelligence
- 🌟 **Evaluate** ethical alignment and hive_mind
- 🎯 **Decide** based on multi-factor AI analysis  
- ⚡ **Execute** trades with precision
- 📚 **Learn** and adapt from every outcome

**Welcome to the future of intelligent AI trading!** 🚀

---

*Need help? Check `COMPREHENSIVE_DOCUMENTATION.md` for detailed information.*