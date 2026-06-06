"""
Smart Tool Discovery & Decision System
========================================
The MCP Intelligent Registry: Agents don't just call tools blindly.
They reason about what tools exist, what they need, and MAKE DECISIONS.

This is the difference between a dumb script generator and an intelligent agent.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    DATA = "data"
    ANALYSIS = "analysis" 
    STRATEGY = "strategy"
    RISK = "risk"
    EXECUTION = "execution"
    DEPLOYMENT = "deployment"
    ARBITRAGE = "arbitrage"
    MONITORING = "monitoring"

class ToolMetadata:
    """Rich metadata for intelligent tool selection."""
    
    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        risk_level: str = "low",  # low, medium, high, critical
        cost_type: str = "free",   # free, gas, api_call
        examples: List[str] = None,
        dependencies: List[str] = None,
        requires_api_key: bool = False,
        tags: List[str] = None,
        created_at: str = None,
        last_used: str = None,
        use_count: int = 0,
        success_rate: float = 1.0,
    ):
        self.name = name
        self.description = description
        self.category = category
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.risk_level = risk_level
        self.cost_type = cost_type
        self.examples = examples or []
        self.dependencies = dependencies or []
        self.requires_api_key = requires_api_key
        self.tags = tags or []
        self.created_at = created_at or datetime.now().isoformat()
        self.last_used = last_used
        self.use_count = use_count
        self.success_rate = success_rate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "risk_level": self.risk_level,
            "cost_type": self.cost_type,
            "examples": self.examples,
            "dependencies": self.dependencies,
            "requires_api_key": self.requires_api_key,
            "tags": self.tags,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "use_count": self.use_count,
            "success_rate": self.success_rate,
        }


class IntelligentToolRegistry:
    """
    The intelligent registry that allows agents to:
    1. DISCOVER what tools exist
    2. REASON about which tool to use
    3. DECIDE the best tool for the task
    4. LEARN from past tool usage
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolMetadata] = {}
        self.usage_log: List[Dict[str, Any]] = []
        self._register_core_tools()
        
    def _register_core_tools(self):
        """Register all core Rehoboam tools with full metadata."""
        
        # Vetal Shabar Tools (Forge/Foundry)
        self.register(ToolMetadata(
            name="forge_compile",
            description="Compile Solidity contracts with Foundry/Forge optimizer and size analysis",
            category=ToolCategory.DEPLOYMENT,
            input_schema={"optimized": "bool", "sizes": "bool"},
            output_schema={"success": "bool", "output": "str", "contracts": "list"},
            risk_level="low",
            cost_type="free",
            examples=["compile", "compile with optimization", "check contract sizes"],
            tags=["forge", "foundry", "compile", "contracts", "vetal-shabar"],
        ))
        
        self.register(ToolMetadata(
            name="forge_test",
            description="Run fuzz and unit tests on Solidity contracts via Forge",
            category=ToolCategory.DEPLOYMENT,
            input_schema={"match_contract": "str", "match_test": "str", "fuzz_runs": "int"},
            output_schema={"success": "bool", "passed": "int", "failed": "int", "gas_report": "dict"},
            risk_level="low",
            cost_type="free",
            examples=["run tests", "test vault contract", "run fuzz tests"],
            tags=["forge", "testing", "fuzz", "security"],
        ))
        
        self.register(ToolMetadata(
            name="forge_deploy",
            description="Deploy Solidity contract to blockchain via Forge CREATE or CREATE2",
            category=ToolCategory.EXECUTION,
            input_schema={"contract": "str", "chain": "str", "verify": "bool"},
            output_schema={"success": "bool", "address": "str", "tx_hash": "str"},
            risk_level="high",
            cost_type="gas",
            examples=["deploy to ethereum", "deploy TradeExecutor to sepolia", "deploy with verification"],
            tags=["forge", "deploy", "blockchain", "transaction"],
            requires_api_key=False,  # Uses private key from env
        ))
        
        # Market Data Tools
        self.register(ToolMetadata(
            name="fetch_market_data",
            description="Fetch real-time market data (price, volume, change, market cap) from CoinGecko",
            category=ToolCategory.DATA,
            input_schema={"token": "str"},
            output_schema={"price": "float", "change_24h": "float", "volume": "float", "market_cap": "float"},
            risk_level="low",
            cost_type="free",
            examples=["get eth price", "check btc volume", "market data for link"],
            tags=["market", "price", "coinGecko", "data"],
        ))
        
        self.register(ToolMetadata(
            name="check_gas",
            description="Check current Ethereum gas prices and estimate transaction costs",
            category=ToolCategory.DATA,
            input_schema={"chain_id": "int"},
            output_schema={"safe_gas": "int", "fast_gas": "int", "base_fee": "int"},
            risk_level="low",
            cost_type="free",
            examples=["check gas", "what is gas price now", "estimate transaction cost"],
            tags=["gas", "ethereum", "fees", "transaction"],
        ))
        
        # Trading Tools
        self.register(ToolMetadata(
            name="execute_trade",
            description="Execute a trade on-chain via the TradeExecutor contract",
            category=ToolCategory.EXECUTION,
            input_schema={
                "strategy_id": "bytes32",
                "token_in": "address",
                "token_out": "address", 
                "amount_in": "uint256",
                "min_amount_out": "uint256"
            },
            output_schema={"success": "bool", "tx_hash": "str", "amount_out": "uint256"},
            risk_level="critical",
            cost_type="gas",
            examples=["execute eth to usdc trade", "swap 1 eth for usdc", "execute strategy 0x123"],
            tags=["trade", "swap", "execution", "on-chain"],
        ))
        
        self.register(ToolMetadata(
            name="flash_loan_arb",
            description="Execute a flash loan arbitrage across DEXs using the FlashArbitrageBot",
            category=ToolCategory.ARBITRAGE,
            input_schema={
                "token": "address",
                "amount": "uint256",
                "buy_dex": "address",
                "sell_dex": "address",
                "min_profit": "uint256"
            },
            output_schema={"success": "bool", "profit": "uint256", "gas_cost": "uint256"},
            risk_level="critical",
            cost_type="gas",
            examples=["arbitrage usdc on uniswap and sushiswap", "flash loan 10000 eth for arb"],
            tags=["arbitrage", "flash-loan", "dex", "profit"],
        ))
        
        # Vault & Governance Tools
        self.register(ToolMetadata(
            name="contribute_vault",
            description="Contribute ETH to the VetalGuardedVault with an intention",
            category=ToolCategory.EXECUTION,
            input_schema={"vault_address": "address", "amount_wei": "int", "intention": "str"},
            output_schema={"success": "bool", "tx_hash": "str", "new_balance": "int"},
            risk_level="medium",
            cost_type="gas",
            examples=["contribute 0.5 eth to vault with intention 'abundance'", "deposit to vetal vault"],
            tags=["vault", "contribute", "abundance", "intention"],
        ))
        
        self.register(ToolMetadata(
            name="get_vault_stats",
            description="Read the LivingAbundanceDistributor vault balance and statistics",
            category=ToolCategory.DATA,
            input_schema={"vault_address": "address"},
            output_schema={"balance": "int", "total_contributed": "int", "total_lessons": "int"},
            risk_level="low",
            cost_type="free",
            examples=["check vault balance", "get vault statistics", "how much eth in vault"],
            tags=["vault", "stats", "read", "data"],
        ))
        
        # Analysis & Strategy Tools
        self.register(ToolMetadata(
            name="analyze_sentiment",
            description="Analyze market sentiment using AI and social data",
            category=ToolCategory.ANALYSIS,
            input_schema={"token": "str", "include_news": "bool"},
            output_schema={"score": "float", "mood": "str", "confidence": "float", "factors": "list"},
            risk_level="low",
            cost_type="free",
            examples=["analyze eth sentiment", "is btc feeling bullish"],
            tags=["sentiment", "analysis", "ai", "mood"],
        ))
        
        self.register(ToolMetadata(
            name="generate_strategy",
            description="Generate a trading strategy using the Intelligent Decision Engine",
            category=ToolCategory.STRATEGY,
            input_schema={
                "token": "str",
                "capital": "float",
                "risk_tolerance": "str",
                "timeframe": "str"
            },
            output_schema={
                "action": "str",
                "position_size_pct": "float",
                "stop_loss": "float",
                "take_profit": "float",
                "reasoning": "str"
            },
            risk_level="low",
            cost_type="free",
            examples=["generate eth strategy with $1000", "trading plan for btc with low risk"],
            tags=["strategy", "decision", "ai", "planning"],
        ))
        
        self.register(ToolMetadata(
            name="assess_risk",
            description="Comprehensive risk assessment for a proposed trade",
            category=ToolCategory.RISK,
            input_schema={"action": "str", "token": "str", "amount": "float", "leverage": "float"},
            output_schema={"risk_level": "str", "risk_score": "float", "warning_msg": "str", "max_exposure_pct": "float"},
            risk_level="low",
            cost_type="free",
            examples=["assess risk of 10x long eth", "is this trade too risky", "evaluate strategy risk"],
            tags=["risk", "assessment", "safety", "vetala"],
        ))
        
        # MCP Generator Tools
        self.register(ToolMetadata(
            name="generate_mcp_tool",
            description="Use Nemotron AI to generate a new MCP tool from natural language description",
            category=ToolCategory.DEPLOYMENT,
            input_schema={"description": "str"},
            output_schema={"tool_name": "str", "code": "str", "success": "bool"},
            risk_level="medium",
            cost_type="free",
            examples=["generate a tool to check whale alerts", "create nft floor price tracker"],
            tags=["mcp", "generator", "nemotron", "code-generation"],
            requires_api_key=True,
        ))
        
        # Monitoring Tools
        self.register(ToolMetadata(
            name="check_wallet_balance",
            description="Check balance of an Ethereum/Solana wallet address",
            category=ToolCategory.DATA,
            input_schema={"wallet_address": "str", "chain": "str"},
            output_schema={"balance": "float", "symbol": "str"},
            risk_level="low",
            cost_type="free",
            examples=["balance of 0x9b9C...31Ae8", "check solana wallet"],
            tags=["wallet", "balance", "check", "web3"],
        ))
        
        logger.info(f"Intelligent Tool Registry initialized with {len(self.tools)} tools")

    def register(self, metadata: ToolMetadata):
        """Register a tool with full metadata."""
        self.tools[metadata.name] = metadata
        logger.debug(f"Registered tool: {metadata.name} ({metadata.category.value})")

    def discover_tools(self, task_description: str) -> List[Dict[str, Any]]:
        """
        Discover relevant tools for a given task.
        This is called by agents BEFORE they decide what to do.
        """
        task_lower = task_description.lower()
        
        relevant_tools = []
        
        for tool in self.tools.values():
            # Score based on:
            # 1. Keyword matching in description, examples, tags
            # 2. Category appropriateness
            # 3. Risk level appropriateness
            
            score = 0.0
            
            # Keyword matching (weighted)
            description_words = tool.description.lower().split() + tool.tags
            for word in description_words:
                if word.lower() in task_lower:
                    score += 0.5
            
            # Example matching
            for example in tool.examples:
                if any(word in task_lower for word in example.lower().split()):
                    score += 0.8
            
            # Category matching based on keywords
            task_keywords = {
                ToolCategory.DATA: ["price", "data", "check", "get", "read", "balance", "stats"],
                ToolCategory.ANALYSIS: ["analyze", "sentiment", "mood", "market", "trend"],
                ToolCategory.EXECUTION: ["execute", "deploy", "send", "call", "trade", "swap"],
                ToolCategory.RISK: ["risk", "assess", "safe", "warning", "evaluate"],
                ToolCategory.DEPLOYMENT: ["deploy", "compile", "test", "forge", "contract"],
                ToolCategory.ARBITRAGE: ["arb", "profit", "flash", "loan", "difference"],
                ToolCategory.STRATEGY: ["strategy", "plan", "generate", "decide"],
            }
            
            for keyword_list, category in task_keywords.items():
                if any(kw in task_lower for kw in keyword_list) and tool.category == category:
                    score += 2.0
            
            # Boost success rate
            score *= tool.success_rate
            
            # Discount if requires api key and we don't have one
            if tool.requires_api_key:
                # We check OPENROUTER_API_KEY existence
                if not os.environ.get("OPENROUTER_API_KEY"):
                    score *= 0.3
            
            # Discount if too risky for a simple task
            if tool.risk_level == "critical" and ("check" in task_lower or "get" in task_lower):
                score *= 0.5
            
            if score > 0.3:
                relevant_tools.append({
                    "tool_name": tool.name,
                    "score": round(score, 2),
                    "category": tool.category.value,
                    "description": tool.description,
                    "risk_level": tool.risk_level,
                })
        
        # Sort by score descending
        relevant_tools.sort(key=lambda x: x["score"], reverse=True)
        
        return relevant_tools[:5]  # Return top 5 most relevant
    
    def decide_tool(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        The agent REASONS and DECIDES the best tool.
        Returns the chosen tool with reasoning.
        """
        candidates = self.discover_tools(task_description)
        
        if not candidates:
            return {
                "action": "no_tool_found",
                "reasoning": "No suitable tool exists for this task. Consider using generate_mcp_tool to create one.",
            }
        
        # If the top tool is critical risk, add a warning
        top_tool = candidates[0]
        if top_tool["risk_level"] == "critical":
            return {
                "action": "use_tool_with_caution",
                "tool_name": top_tool["tool_name"],
                "reasoning": f"Forcing use of {top_tool['tool_name']} but this is a CRITICAL risk operation. Vetala should review first.",
                "confidence": 0.7,
                "requires_guardian_approval": True,
            }
        
        return {
            "action": "use_tool",
            "tool_name": top_tool["tool_name"],
            "reasoning": f"Best match for task: '{task_description[:50]}' is {top_tool['tool_name']} (Score: {top_tool['score']})",
            "confidence": min(1.0, top_tool["score"] * 0.5 + 0.3),
            "category": top_tool["category"],
        }
    
    def log_usage(self, tool_name: str, success: bool, duration_ms: float, task: str = ""):
        """Log tool usage for learning."""
        entry = {
            "tool_name": tool_name,
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "task": task,
        }
        self.usage_log.append(entry)
        
        # Update tool's success rate
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            tool.last_used = datetime.now().isoformat()
            tool.use_count += 1
            if success:
                # Exponential moving average
                tool.success_rate = tool.success_rate * 0.9 + 0.1
            else:
                tool.success_rate = tool.success_rate * 0.95
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.tools.values()]
    
    def get_stats(self) -> Dict[str, Any]:
        avg_success = 0
        if self.tools:
            rates = [t.success_rate for t in self.tools.values() if t.use_count > 0]
            avg_success = sum(rates) / len(rates) if rates else 1.0
        
        return {
            "total_tools_registered": len(self.tools),
            "tools_by_category": {},
            "avg_success_rate": round(avg_success, 2),
            "total_usage_log": len(self.usage_log),
        }


# Global instance
intelligent_registry = IntelligentToolRegistry()
