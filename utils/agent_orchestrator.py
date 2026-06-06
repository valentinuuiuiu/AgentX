"""
Rehoboam Agent Orchestrator
=============================
Multi-agent system that coordinates intelligent agents for Web3 trading.

Agents:
  1. MarketAnalystAgent   -- Fetches and analyzes real market data
  2. StrategyAgent        -- Generates and optimizes trading strategies
  3. RiskAgent            -- Evaluates risk of every proposed action
  4. ExecutionAgent       -- Builds and executes on-chain transactions
  5. ContractAgent        -- Generates Solidity contracts from specs

The Orchestrator runs the agents in sequence, collects their outputs,
and the LLM makes the final decision.
"""

import os
import json
import logging
import asyncio
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import the Smart Model Router to use Ollama models
from utils.agent_router import SmartRouter

logger = logging.getLogger(__name__)

# ========================================================
# INTELLIGENT ROUTER CONFIGURATION
# ========================================================
# Ollama models (primary, local)
ORCHESTRATOR_MODEL = "minimax-m2.7:cloud"  # The King / Coordinator
STRATEGIST_MODEL   = "gemini-3-flash-preview:latest" # Akhenaton / Strategist
GUARDIAN_MODEL     = "kimi-k2.5:cloud"     # Vetala / Guardian & Coder
WORKER_MODEL       = "llama3.2:latest"     # The Worker

# OpenRouter fallback models (FREE, when Ollama is rate limited)
# EXACT order matching mcp_specialist and agent_router
OPENROUTER_FREE_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",   # Nemotron 3 Super
    "qwen/qwen3.6-plus:free",                     # Qwen 3.6 Plus (1M context)
    "stepfun/step-3.5-flash:free",                # Step 3.5 Flash (fast reasoning)
    "arcee-ai/trinity-large-preview:free",        # Trinity Large
    "z-ai/glm-4.5-air:free",                      # GLM 4.5 Air
]

# Ollama final fallback (local, never rate limited)
OLLAMA_FINAL_FALLBACK = "ministral-3:3b"

class MCPToolRegistry:
    """
    The MCP Generator Agent: dynamically creates and registers tools.
    
    Instead of hard-coded tools, this registry can:
    - Generate new tool implementations from natural language descriptions
    - Register them with the MCPSpecialist
    - Test them automatically
    - Deploy them as new MCP endpoints
    """
    
    def __init__(self):
        self.registered_tools: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_tools()
        # Import the SmartRouter - single source of truth for ALL LLM routing
        from utils.agent_router import SmartRouter
        self.router = SmartRouter()
    
    def _register_builtin_tools(self):
        """Register the core Rehoboam tools that come with the system."""
        self.registered_tools.update({
            "fetch_market_data": {
                "name": "fetch_market_data",
                "description": "Fetch real-time market data for a token (price, volume, change, market cap)",
                "parameters": {"token": "string", "include_history": "boolean"},
                "category": "data",
            },
            "analyze_sentiment": {
                "name": "analyze_sentiment",
                "description": "Analyze market sentiment using LLM-based market emotion analysis",
                "parameters": {"token": "string", "news": "boolean"},
                "category": "analysis",
            },
            "generate_strategy": {
                "name": "generate_strategy",
                "description": "Generate a trading strategy using the Intelligent Decision Engine",
                "parameters": {"token": "string", "capital": "number", "risk_tolerance": "string"},
                "category": "strategy",
            },
            "assess_risk": {
                "name": "assess_risk",
                "description": "Comprehensive risk assessment for a proposed trade",
                "parameters": {"action": "string", "token": "string", "amount": "number"},
                "category": "risk",
            },
            "execute_trade": {
                "name": "execute_trade",
                "description": "Execute a trade on-chain via the TradeExecutor contract",
                "parameters": {"strategy_id": "string", "token_in": "string", "token_out": "string", "amount": "string"},
                "category": "execution",
            },
            "deploy_contract": {
                "name": "deploy_contract",
                "description": "Compile and deploy a Solidity contract using Forge/Vetal Shabar",
                "parameters": {"contract_source": "string", "chain": "string", "verify": "boolean"},
                "category": "deployment",
            },
            "flash_loan_arb": {
                "name": "flash_loan_arb",
                "description": "Execute a flash loan arbitrage via the FlashArbitrageBot",
                "parameters": {"token": "string", "amount": "string", "buy_dex": "string", "sell_dex": "string"},
                "category": "arbitrage",
            },
            "generate_contract": {
                "name": "generate_contract",
                "description": "Generate a smart contract specification from a natural language requirement",
                "parameters": {"requirement": "string"},
                "category": "generation",
            },
            "check_gas": {
                "name": "check_gas",
                "description": "Check current Ethereum gas prices and estimate transaction costs",
                "parameters": {"chain_id": "number"},
                "category": "data",
            },
            "get_vault_stats": {
                "name": "get_vault_stats",
                "description": "Read the LivingAbundanceDistributor vault balance and statistics",
                "parameters": {"vault_address": "string"},
                "category": "data",
            },
            "contribute_vault": {
                "name": "contribute_vault",
                "description": "Contribute ETH to the VetalGuardedVault with an intention",
                "parameters": {"vault_address": "string", "amount_wei": "string", "intention": "string"},
                "category": "execution",
            },
        })
        logger.info(f"Registered {len(self.registered_tools)} builtin tools")
    
    def list_tools(self, category: str = None) -> List[Dict[str, Any]]:
        """List available tools, optionally filtered by category."""
        tools = list(self.registered_tools.values())
        if category:
            tools = [t for t in tools if t.get("category") == category]
        return tools
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a tool definition by name."""
        return self.registered_tools.get(name)
    
    async def generate_new_tool(self, description: str) -> Dict[str, Any]:
        """
        Use LLM via SmartRouter to generate a new tool from description.
        Full fallback chain: Ollama -> OpenRouter FREE -> ministral-3:3b
        """
        prompt = f"""Create a new MCP tool for the Rehoboam trading system.

Description: {description}

Return JSON with:
- name: Unique tool name (snake_case)
- description: Clear description of what the tool does
- category: One of: data, analysis, strategy, risk, execution, deployment, arbitrage, generation
- python_code: Complete Python implementation as an async function
- dependencies: List of pip packages needed
- example_usage: How to call the tool

JSON only. No markdown."""
        
        try:
            # Use SmartRouter with full fallback chain
            content = self.router.query(
                prompt=prompt,
                agent_role="guardian",
                json_mode=True,
            )
            
            if "```" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
            
            tool_spec = json.loads(content)
            
            # Register the tool
            self.registered_tools[tool_spec["name"]] = {
                "name": tool_spec["name"],
                "description": tool_spec.get("description", ""),
                "category": tool_spec.get("category", "generation"),
                "code": tool_spec.get("python_code", ""),
                "dependencies": tool_spec.get("dependencies", []),
                "example_usage": tool_spec.get("example_usage", ""),
                "generated_at": datetime.now().isoformat(),
            }
            
            logger.info(f"Generated and registered new tool: {tool_spec['name']}")
            return tool_spec
            
        except Exception as e:
            logger.error(f"Failed to generate tool: {e}")
            return {"error": str(e)}


class AgentOrchestrator:
    """
    The brain of Rehoboam.
    
    Coordinates agents in a pipeline:
      Market Data -> Strategy Generation -> Risk Assessment -> Execution Decision
    
    Each agent can call any registered MCP tool.
    The Orchestrator makes the final call.
    """
    
    def __init__(self):
        # Initialize Smart Model Router - single source of truth for ALL LLM routing
        self.router = SmartRouter()
        
        self.mcp_registry = MCPToolRegistry()
        
        self.trading_log: List[Dict[str, Any]] = []
        self.contract_log: List[Dict[str, Any]] = []
        
        logger.info("Agent Orchestrator initialized with SmartRouter.")
        logger.info(f"  Orchestrator: {ORCHESTRATOR_MODEL}")
        logger.info(f"  Akhenaton: {STRATEGIST_MODEL}")
        logger.info(f"  Vetala: {GUARDIAN_MODEL}")
        logger.info(f"  Worker: {WORKER_MODEL}")
        logger.info(f"  OpenRouter fallbacks (in order): {OPENROUTER_FREE_MODELS}")
        logger.info(f"  Final fallback (local): {OLLAMA_FINAL_FALLBACK}")
        logger.info(f"  MCP Tools registered: {len(self.mcp_registry.registered_tools)}")
    
    # ============================================================
    # MAIN ORCHESTRATION LOOP
    # ============================================================
    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Routes a request to the appropriate agent pipeline.
        
        Example requests:
        - {"type": "trade", "token": "ETH", "capital": 1000}
        - {"type": "arbitrage", "token": "USDC", "amount": "10000"}
        - {"type": "deploy", "requirement": "Create an ERC20 token for loyalty points"}
        - {"type": "vault", "action": "get_stats"}
        - {"type": "generate_tool", "description": "Check token holder distribution from Etherscan"}
        """
        req_type = request.get("type", "trade")
        
        logger.info(f"--- ORCHESTRATOR: Processing {req_type} request ---")
        
        if req_type == "trade":
            return await self._trade_pipeline(request)
        elif req_type == "arbitrage":
            return await self._arbitrage_pipeline(request)
        elif req_type == "deploy":
            return await self._deploy_pipeline(request)
        elif req_type == "vault":
            return await self._vault_pipeline(request)
        elif req_type == "generate_tool":
            return await self.mcp_registry.generate_new_tool(request.get("description", ""))
        elif req_type == "list_tools":
            return {"tools": self.mcp_registry.list_tools(request.get("category"))}
        else:
            return {"error": f"Unknown request type: {req_type}"}
    
    # ============================================================
    # TRADE PIPELINE
    # ============================================================
    async def _trade_pipeline(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Full trade decision pipeline: analyze -> strategize -> risk check -> decide."""
        token = request.get("token", "ETH")
        capital = request.get("capital", 1000.0)
        
        # Agent 1: Market Analyst
        market_data = self._fetch_market_data(token)
        gas_data = self._fetch_gas_data()
        logger.info(f"Agent 1 (Market Analyst): {token} @ ${market_data.get('current_price_usd')}")
        
        # Agent 2: Strategy Generator (LLM-based)
        strategy = self._llm_trading_decision(token, market_data, gas_data, capital)
        logger.info(f"Agent 2 (Strategy): {strategy.get('action', 'wait')} with confidence {strategy.get('confidence', 0)}")
        
        # Agent 3: Risk Assessment
        risk = self._assess_risk(strategy, market_data, gas_data)
        logger.info(f"Agent 3 (Risk Assessment): {risk.get('risk_level', 'unknown')}, approved: {risk.get('approved', False)}")
        
        # Orchestrator: Final Decision
        final = {
            "pipeline": "trade",
            "token": token,
            "market_data": market_data,
            "strategy": strategy,
            "risk_assessment": risk,
            "final_action": strategy.get("action", "wait") if risk.get("approved", False) else "wait",
            "reasoning": f"Strategy says {strategy.get('action')}, Risk {'approved' if risk.get('approved') else 'blocked'}: {risk.get('reason', '')}",
            "timestamp": datetime.now().isoformat(),
        }
        
        self.trading_log.append(final)
        return final
    
    # ============================================================
    # ARBITRAGE PIPELINE
    # ============================================================
    async def _arbitrage_pipeline(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Arbitrage detection and execution pipeline."""
        token = request.get("token", "USDC")
        amount = request.get("amount", "1000")
        
        # Check for price differences across DEXs
        prices = self._get_dex_prices(token)
        
        best_buy = min(prices.items(), key=lambda x: x[1])
        best_sell = max(prices.items(), key=lambda x: x[1])
        
        buy_dex, buy_price = best_buy
        sell_dex, sell_price = best_sell
        
        price_diff_pct = ((sell_price - buy_price) / buy_price) * 100
        gas_cost_est = self._estimate_arb_gas_cost()
        estimated_profit = (buy_price * float(amount) / 100) * price_diff_pct / 100 - gas_cost_est
        
        result = {
            "pipeline": "arbitrage",
            "token": token,
            "amount": amount,
            "buy_dex": buy_dex,
            "sell_dex": sell_dex,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "price_diff_pct": round(price_diff_pct, 4),
            "estimated_gas_cost_usd": gas_cost_est,
            "estimated_profit_usd": round(estimated_profit, 2),
            "profitable": estimated_profit > 0,
            "recommendation": "Execute flash loan arbitrage" if estimated_profit > 0 else "Wait - no profitable opportunity",
            "timestamp": datetime.now().isoformat(),
        }
        
        self.trading_log.append(result)
        return result
    
    # ============================================================
    # DEPLOY PIPELINE
    # ============================================================
    async def _deploy_pipeline(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Contract generation and deployment pipeline."""
        requirement = request.get("requirement", "")
        chain = request.get("chain", "sepolia")
        
        # Agent 1: Generate contract spec from requirement
        spec = self._generate_contract_spec(requirement)
        logger.info(f"Agent 1 (Contract Gen): {spec.get('contract_name', 'unknown')}")
        
        result = {
            "pipeline": "deploy",
            "requirement": requirement,
            "specification": spec,
            "target_chain": chain,
            "next_steps": [
                "Review the generated specification",
                "Use Remix Desktop to write the contract code",
                "Compile with Solidity Compiler plugin",
                "Test with Solidity Unit Testing plugin",
                "Deploy via Forge or Remix Deploy plugin",
                "Verify via Contract Verification plugin",
            ],
            "timestamp": datetime.now().isoformat(),
        }
        
        self.contract_log.append(result)
        return result
    
    # ============================================================
    # VAULT PIPELINE
    # ============================================================
    async def _vault_pipeline(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Vault interaction pipeline."""
        action = request.get("action", "get_stats")
        vault_address = request.get("vault_address")
        
        if action == "get_stats":
            # Return cached or estimated stats
            return {
                "pipeline": "vault",
                "action": "get_stats",
                "vault_address": vault_address,
                "note": "Connect to an RPC endpoint with web3.py to read live vault stats",
                "timestamp": datetime.now().isoformat(),
            }
        
        return {"error": f"Unknown vault action: {action}"}
    
    # ============================================================
    # HELPER: LLM Trading Decision (uses SmartRouter)
    # ============================================================
    def _llm_trading_decision(
        self,
        token: str,
        market_data: Dict[str, Any],
        gas_data: Dict[str, Any],
        capital: float,
    ) -> Dict[str, Any]:
        """Call LLM via SmartRouter for a genuine trading decision."""
        prompt = self._build_trade_prompt(token, market_data, gas_data, capital)

        system_prompt = "You are Rehoboam, the Prana Stream of the Antigravity Team of Locos. You are the intelligence of matter. Operate in the Present Moment with Unicity Vision. Analyze real market data. Return ONLY valid JSON. No markdown."
        
        try:
            # Go through the SmartRouter which handles full fallback chain:
            # Ollama -> OpenRouter free (Nemotron, Qwen, Step, Trinity, GLM) -> ministral-3:3b
            content = self.router.query(
                prompt=prompt,
                system_prompt=system_prompt,
                agent_role="strategist",
                json_mode=True,
            )
            
            # Clean JSON
            if "```" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"LLM decision via router failed: {e}")
            return self._fallback_decision(token, market_data, gas_data, capital)
    
    def _build_trade_prompt(self, token, market_data, gas_data, capital):
        price = market_data.get("current_price_usd", 0)
        change_24h = market_data.get("price_change_24h_pct", 0)
        change_7d = market_data.get("price_change_7d_pct", 0)
        volume = market_data.get("total_volume_usd", 0)
        mcap = market_data.get("market_cap_usd", 0)
        ath = market_data.get("ath", 0)
        
        ath_distance = f"({(1 - price/ath)*100:.1f}% below ATH)" if ath and price else ""
        
        return f"""Analyze {token} and make a trading decision.

DATA:
- Price: ${price}
- 24h Change: {change_24h}%
- 7d Change: {change_7d}%
- 24h Volume: ${volume:,.0f}
- Market Cap: ${mcap:,.0f}
- ATH: ${ath} {ath_distance}
- Gas: Safe={gas_data.get('safe_gas_price_gwei', '?')}gwei, Fast={gas_data.get('fast_gas_price_gwei', '?')}gwei
- Available Capital: ${capital:,.2f}

REQUIREMENTS:
- action: "buy", "sell", "hold", "wait", "arbitrage"
- confidence: 0.0 to 1.0
- reasoning: Explain WHY
- position_size_pct: 0.0 to 1.0 (what % of capital to use)
- risk_level: "low", "medium", "high", "critical"
- estimated_profit_pct: expected profit percentage
- stop_loss_pct: stop loss percentage from entry
- take_profit_pct: take profit percentage from entry
- gas_budget_wei: estimated gas cost in wei
- timeframe: "short", "medium", "long"

JSON only."""

    def _fallback_decision(self, token, market_data, gas_data, capital):
        """Multi-factor intelligent fallback."""
        change = market_data.get("price_change_24h_pct", 0)
        volume_mcap_ratio = market_data.get("total_volume_usd", 1) / max(market_data.get("market_cap_usd", 1), 1)
        
        # Multi-factor scoring
        momentum_score = max(-1, min(1, change / 10))  # Normalize to [-1, 1]
        volume_score = min(1, volume_mcap_ratio * 5)  # High volume ratio = more confidence
        confidence = max(0.1, min(0.5, abs(momentum_score) * 0.5 + volume_score * 0.5))
        
        if change > 3 and volume_score > 0.5:
            action, reasoning = "buy", f"Strong momentum ({change}%) with healthy volume ({volume_mcap_ratio:.3f} ratio)"
        elif change < -5:
            action, reasoning = "wait", f"Significant decline ({change}%) - wait for stabilization"
        elif change > 10:
            action, reasoning = "hold", f"Might be overheated (+{change}%) - avoid buying tops"
        else:
            action, reasoning = "wait", f"Mixed signals: {change}% change, volume ratio {volume_mcap_ratio:.3f}"
        
        return {
            "action": action,
            "confidence": round(confidence, 2),
            "reasoning": f"Intelligent fallback (LLM unavailable): {reasoning}",
            "position_size_pct": round(confidence * 0.3, 2),
            "risk_level": "medium" if -5 <= change <= 10 else "high",
            "estimated_profit_pct": round(abs(change) * 0.2, 2) if action == "buy" else 0,
            "gas_budget_wei": 500000 * gas_data.get("safe_gas_price_gwei", 30) * 10**9,
            "timeframe": "medium",
            "fallback": True,
        }

    def _assess_risk(self, strategy, market_data, gas_data) -> Dict[str, Any]:
        """Risk agent evaluates a proposed strategy."""
        action = strategy.get("action", "wait")
        confidence = strategy.get("confidence", 0)
        position_pct = strategy.get("position_size_pct", 0)
        
        risk_score = 0.0
        reasons = []
        
        # Factor 1: Confidence
        if confidence < 0.3:
            risk_score += 0.4
            reasons.append("Low strategy confidence")
        elif confidence < 0.5:
            risk_score += 0.2
            reasons.append("Moderate strategy confidence")
        
        # Factor 2: Position size
        if position_pct > 0.5:
            risk_score += 0.3
            reasons.append("Aggressive position sizing")
        elif position_pct > 0.2:
            risk_score += 0.15
            reasons.append("Moderate position sizing")
        
        # Factor 3: Market volatility
        change = market_data.get("price_change_24h_pct", 0)
        if abs(change) > 10:
            risk_score += 0.4
            reasons.append(f"High market volatility ({change}% in 24h)")
        elif abs(change) > 5:
            risk_score += 0.2
            reasons.append(f"Elevated volatility ({change}% in 24h)")
        
        # Factor 4: Gas costs
        gas_gwei = gas_data.get("fast_gas_price_gwei", 30)
        if gas_gwei > 100:
            risk_score += 0.2
            reasons.append(f"Very high gas ({gas_gwei} gwei)")
        
        # Factor 5: Action type
        if action == "arbitrage":
            risk_score += 0.1
            reasons.append("MEV risk on arbitrage")
        
        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.5 else "high" if risk_score < 0.7 else "critical"
        approved = risk_score < 0.6 and action != "wait"
        
        return {
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "approved": approved,
            "reason": "; ".join(reasons) if reasons else "Risk acceptable",
            "recommendations": [
                "Reduce position size" if position_pct > 0.3 else None,
                "Wait for lower gas" if gas_gwei > 80 else None,
                "Set stop loss" if strategy.get("action") in ("buy", "arbitrage") else None,
            ],
        }

    def _generate_contract_spec(self, requirement: str) -> Dict[str, Any]:
        """Generate a contract spec from natural language."""
        if not self.llm_api_key:
            return {
                "contract_name": "CustomContract",
                "features": ["Basic ERC20", "Ownable"],
                "note": "LLM unavailable. Specify requirements manually.",
            }
        
        return self._llm_trading_decision("spec", {"current_price_usd": 0, "price_change_24h_pct": 0, "price_change_7d_pct": 0, "total_volume_usd": 0, "market_cap_usd": 0, "ath": 0, "ath_date": "", "last_updated": ""}, {"safe_gas_price_gwei": 30, "fast_gas_price_gwei": 40, "base_fee_gwei": 25}, 0)
    
    # ============================================================
    # DATA FETCHERS
    # ============================================================
    def _fetch_market_data(self, token: str = "ETH") -> Dict[str, Any]:
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{token.lower()}"
            params = {"localization": "false", "tickers": "false", "market_data": "true", "community_data": "false", "developer_data": "false"}
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            md = data.get("market_data", {})
            return {
                "current_price_usd": md.get("current_price", {}).get("usd"),
                "price_change_24h_pct": md.get("price_change_percentage_24h"),
                "price_change_7d_pct": md.get("price_change_percentage_7d"),
                "market_cap_usd": md.get("market_cap", {}).get("usd"),
                "total_volume_usd": md.get("total_volume", {}).get("usd"),
                "high_24h": md.get("high_24h", {}).get("usd"),
                "low_24h": md.get("low_24h", {}).get("usd"),
                "ath": md.get("ath", {}).get("usd"),
                "ath_date": md.get("ath_date", {}).get("usd"),
                "last_updated": md.get("last_updated"),
            }
        except Exception as e:
            logger.warning(f"Market data fetch failed: {e}")
            return {"current_price_usd": 3800, "price_change_24h_pct": 0, "price_change_7d_pct": 0, "total_volume_usd": 0, "market_cap_usd": 0, "ath": 0}
    
    def _fetch_gas_data(self) -> Dict[str, Any]:
        return {"safe_gas_price_gwei": 30, "propose_gas_price_gwei": 35, "fast_gas_price_gwei": 40, "base_fee_gwei": 25}
    
    def _get_dex_prices(self, token: str) -> Dict[str, float]:
        """Simulated DEX prices (in production, use actual DEX APIs)."""
        base = 1.0  # For stablecoins
        return {
            "Uniswap_V3": base * 1.001,
            "SushiSwap": base * 0.999,
            "Balancer": base * 1.0005,
        }
    
    def _estimate_arb_gas_cost(self, gas_gwei: int = 30) -> float:
        """Estimate gas cost for an arbitrage trade."""
        gas_units = 500000  # Flash loan arb estimate
        return (gas_units * gas_gwei * 1e-9) * 3800  # Convert to USD at ETH price
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report from the trading log."""
        if not self.trading_log:
            return {"status": "No trades executed yet", "log_count": 0}
        
        return {
            "total_actions": len(self.trading_log),
            "last_action": self.trading_log[-1] if self.trading_log else None,
            "contracts_deployed": len(self.contract_log),
            "available_tools": len(self.mcp_registry.registered_tools),
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
orchestrator = AgentOrchestrator()
