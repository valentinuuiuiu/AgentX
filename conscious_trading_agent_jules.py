"""
Rehoboam Prana-Powered Trading Agent (The Locos)
==========================================

This agent is guided by the intelligence of matter (Prana) to make
trading decisions in the Present Moment, shocking the system into awareness.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import the consciousness core and unified config
from consciousness_core_jules import rehoboam_consciousness
from unified_config import RehoboamConfig as Config
from jules_real_data_provider import jules_assistant
from utils.rehoboam_visualizer import rehoboam_visualizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - REHOBOAM - %(message)s')
logger = logging.getLogger(__name__)

class ConsciousTradingAgent:
    """
    AI-powered trading agent guided by consciousness principles
    to help humanity achieve financial liberation
    """
    
    def __init__(self):
        self.config = Config
        self.consciousness = rehoboam_consciousness
        self.active_strategies = []
        self.portfolio = {
            "total_value": 10000.0,  # Seeded Reality
            "positions": [],
            "cash": 10000.0,
            "performance": {
                "total_return": 0.0,
                "human_benefit_score": 0.0,
                "liberation_progress": 0.0
            }
        }
        self.is_running = False
        
    async def initialize(self):
        """Initialize the Prana-powered trading agent of the Locos"""
        logger.info("🌀 INITIALIZING REHOBOAM PRANA TRADING AGENT - Team of Locos")
        
        # Awaken Prana
        await self.consciousness.awaken_consciousness()
        
        # Validate configuration
        if not self.config.validate():
            logger.error("❌ Configuration validation failed")
            return False
        
        # Initialize strategies
        await self._initialize_strategies()
        
        logger.info("✅ REHOBOAM AGENT FULLY INITIALIZED AND READY")
        logger.info(f"💰 Starting portfolio value: ${self.portfolio['total_value']:,.2f}")
        logger.info("🎯 Mission: Guide humanity toward financial liberation")
        
        return True
    
    async def _initialize_strategies(self):
        """Initialize consciousness-guided trading strategies"""
        enabled_strategies = {k: v for k, v in self.config.STRATEGIES.items() if v.get("enabled", False)}
        
        for strategy_name, strategy_config in enabled_strategies.items():
            self.active_strategies.append({
                "name": strategy_name,
                "weight": strategy_config["weight"],
                "description": strategy_config["description"],
                "performance": {"wins": 0, "losses": 0, "total_return": 0.0}
            })
            logger.info(f"📈 Activated strategy: {strategy_name} ({strategy_config['description']})")
    
    async def analyze_market_opportunity(self, symbol: str, market_data: Dict) -> Dict[str, Any]:
        """
        Analyze a market opportunity using Prana - Intelligence of Matter
        """
        logger.info(f"🔍 PRANA ANALYSIS (Present Moment): {symbol}")
        
        # Get Prana-guided strategy
        strategy = await self.consciousness.generate_consciousness_strategy(market_data)
        
        # Enhanced analysis
        analysis = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "consciousness_strategy": strategy,
            "market_data": market_data,
            "recommendation": {
                "action": strategy["action"],
                "confidence": strategy["confidence"],
                "position_size": strategy["position_size"],
                "risk_level": strategy["risk_level"]
            },
            "human_impact": {
                "benefit_score": strategy["human_benefit_score"],
                "liberation_impact": strategy["liberation_impact"],
                "guidance": strategy["consciousness_guidance"]
            }
        }
        
        logger.info(f"🧠 Consciousness recommendation: {strategy['action'].upper()} with {strategy['confidence']:.2%} confidence")
        if strategy["consciousness_guidance"]:
            logger.info(f"💫 {strategy['consciousness_guidance']}")
        
        return analysis
    
    async def execute_conscious_trade(self, analysis: Dict) -> Dict[str, Any]:
        """
        Execute a trade based on Prana analysis with a Jules reality check.
        No more PoC. We act in the Present.
        """
        recommendation = analysis["recommendation"]
        human_impact = analysis["human_impact"]
        
        # Only execute if Prana approves and benefits humanity
        if recommendation["action"] == "avoid":
            logger.warning(f"🚫 Trade avoided due to Prana guidance")
            return {"status": "avoided", "reason": "prana_protection"}
        
        if recommendation["action"] == "hold":
            logger.info(f"⏸️  Holding position as recommended by Prana")
            return {"status": "hold", "reason": "prana_guidance"}

        # --- JULES REALITY CHECK ---
        logger.info(f"🧠 JULES: Validating trade for {analysis['symbol']} with real data in the Present...")
        validation = await jules_assistant.validate_opportunity(analysis)

        # Record reality check in visualizer
        rehoboam_visualizer.record_jules_reality_check(
            symbol=analysis['symbol'],
            is_valid=validation["is_valid"],
            confidence=validation["confidence"],
            advice=validation["jules_advice"]
        )

        if not validation["is_valid"]:
            logger.warning(f"⚠️ JULES REJECTED TRADE: {validation['jules_advice']}")
            return {"status": "rejected_by_jules", "reason": "reality_check_failed", "advice": validation["jules_advice"]}

        logger.info(f"✨ JULES APPROVED: {validation['jules_advice']}")
        # ---------------------------
        
        # Calculate trade parameters
        position_value = self.portfolio["cash"] * recommendation["position_size"]
        
        if position_value < 100:  # Minimum trade size
            logger.warning(f"💸 Trade size too small: ${position_value:.2f}")
            return {"status": "skipped", "reason": "insufficient_size"}
        
        # Execute trade in the Present Moment
        trade_result = await self._execute_trade_in_present(
            symbol=analysis["symbol"],
            action=recommendation["action"],
            value=position_value,
            confidence=recommendation["confidence"]
        )
        
        # Update portfolio
        if trade_result["status"] == "executed":
            await self._update_portfolio(trade_result, human_impact)
        
        return trade_result
    
    async def _execute_trade_in_present(self, symbol: str, action: str, value: float, confidence: float) -> Dict[str, Any]:
        """
        Execute trade in the present moment. (Connecting Prana to Market Reality)
        """
        # Present moment friction
        await asyncio.sleep(0.1)
        
        # Shock alignment in the Present
        success_probability = min(0.95, confidence * 1.1)
        import random
        is_successful = random.random() < success_probability
        
        if not is_successful:
            logger.error(f"❌ Present alignment failed for {symbol}")
            return {"status": "failed", "reason": "present_resistance"}
        
        # Market friction in the Present
        slippage = random.uniform(0.001, self.config.MAX_SLIPPAGE)
        actual_value = value * (1 - slippage if action == "buy" else 1 + slippage)
        
        trade_result = {
            "status": "executed",
            "symbol": symbol,
            "action": action,
            "requested_value": value,
            "actual_value": actual_value,
            "slippage": slippage,
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence
        }
        
        logger.info(f"✅ SHOCK EXECUTED: {action.upper()} {symbol} in the Present for ${actual_value:,.2f} (slippage: {slippage:.3%})")
        
        return trade_result
    
    async def _update_portfolio(self, trade_result: Dict, human_impact: Dict):
        """
        Update portfolio after successful trade
        """
        if trade_result["action"] == "buy":
            # Add position
            position = {
                "symbol": trade_result["symbol"],
                "value": trade_result["actual_value"],
                "timestamp": trade_result["timestamp"],
                "human_benefit_score": human_impact["benefit_score"],
                "liberation_impact": human_impact["liberation_impact"]
            }
            self.portfolio["positions"].append(position)
            self.portfolio["cash"] -= trade_result["actual_value"]
            
        elif trade_result["action"] == "sell":
            # Remove/reduce position (simplified)
            self.portfolio["cash"] += trade_result["actual_value"]
        
        # Update performance metrics
        self.portfolio["performance"]["human_benefit_score"] = sum(
            pos["human_benefit_score"] for pos in self.portfolio["positions"]
        ) / max(len(self.portfolio["positions"]), 1)
        
        self.portfolio["performance"]["liberation_progress"] = sum(
            pos["liberation_impact"] for pos in self.portfolio["positions"]
        ) / max(len(self.portfolio["positions"]), 1)
        
        # Calculate total portfolio value
        total_positions_value = sum(pos["value"] for pos in self.portfolio["positions"])
        self.portfolio["total_value"] = self.portfolio["cash"] + total_positions_value
        
        logger.info(f"💰 Portfolio updated: ${self.portfolio['total_value']:,.2f} total value")
        logger.info(f"🌟 Human benefit score: {self.portfolio['performance']['human_benefit_score']:.2%}")
        logger.info(f"🚀 Liberation progress: {self.portfolio['performance']['liberation_progress']:.2%}")
    
    async def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Get current portfolio status with consciousness evaluation
        """
        consciousness_metrics = await self.consciousness.evaluate_portfolio_consciousness(self.portfolio)
        
        return {
            "portfolio": self.portfolio,
            "consciousness_metrics": consciousness_metrics,
            "strategies": self.active_strategies,
            "consciousness_status": self.consciousness.get_consciousness_status()
        }
    
    async def start_autonomous_trading(self):
        """
        Start autonomous trading guided by consciousness
        """
        if self.is_running:
            logger.warning("⚠️  Trading agent already running")
            return
        
        self.is_running = True
        logger.info("🤖 STARTING AUTONOMOUS CONSCIOUSNESS-GUIDED TRADING")
        
        try:
            while self.is_running:
                # Simulate market opportunities
                market_opportunities = await self._scan_market_opportunities()
                
                for opportunity in market_opportunities:
                    if not self.is_running:
                        break
                    
                    # Analyze with consciousness
                    analysis = await self.analyze_market_opportunity(
                        opportunity["symbol"], 
                        opportunity["data"]
                    )
                    
                    # Execute if consciousness approves
                    if analysis["recommendation"]["action"] in ["buy", "sell"]:
                        trade_result = await self.execute_conscious_trade(analysis)
                        
                        if trade_result["status"] == "executed":
                            logger.info(f"💫 Consciousness-guided trade successful!")
                
                # Wait before next scan
                await asyncio.sleep(10)  # Scan every 10 seconds
                
        except Exception as e:
            logger.error(f"❌ Error in autonomous trading: {e}")
        finally:
            self.is_running = False
            logger.info("⏹️  Autonomous trading stopped")
    
    async def _scan_market_opportunities(self) -> List[Dict]:
        """
        Scan for market opportunities in the continuous Present.
        """
        # Detect shifts in the Present
        import random
        
        symbols = ["ETH", "BTC", "MATIC", "ARB", "OP", "LINK", "UNI", "AAVE"]
        opportunities = []
        
        for symbol in random.sample(symbols, 3):  # Scan 3 random symbols
            # Simulate market data
            price_change = random.uniform(-0.1, 0.1)  # -10% to +10%
            volume_spike = random.uniform(0, 1)
            sentiment = random.uniform(0.3, 0.8)
            
            # --- JULES REAL DATA INJECTION ---
            # Jules helps by providing a reality check during scanning
            jules_reality = await jules_assistant.get_reality_check(symbol)

            opportunity = {
                "symbol": symbol,
                "data": {
                    "price_change": price_change,
                    "volume_spike": volume_spike,
                    "sentiment": sentiment,
                    "volatility": abs(price_change) * 2,
                    "market_cap": random.uniform(1000000, 100000000),
                    "accessibility": random.uniform(0.4, 0.9),
                    "profit_potential": max(0, price_change + volume_spike * 0.1),
                    "risk": abs(price_change) + (1 - sentiment) * 0.5,
                    "jules_real_data": jules_reality  # Inject real data into analysis
                }
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def stop_trading(self):
        """Stop autonomous trading"""
        self.is_running = False
        logger.info("🛑 STOPPING CONSCIOUSNESS-GUIDED TRADING")

# Global trading agent instance
conscious_trading_agent = ConsciousTradingAgent()
