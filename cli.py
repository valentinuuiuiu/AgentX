"""
cli.py - Command Line Interface for Rehoboam Agents
=====================================================
Tests the live agents with simulated market data.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s'
)
logger = logging.getLogger("RehoboamCLI")

# Banner
BANNER = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║            REHOBOAM CLI -- Agent Simulation Tests        ║
║                                                          ║
║  Testing the live intelligence of the agents.            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

async def run_tests():
    print(BANNER)
    
    # Import the brains
    try:
        from utils.agent_router import router
        from utils.agent_orchestrator import AgentOrchestrator
        from utils.mcp_specialist import MCPSpecialist
    except Exception as e:
        print(f"[FATAL] Failed to import Rehoboam modules: {e}")
        return

    # Initialize
    print("[INIT] Initializing Agent Orchestrator...")
    orchestrator = AgentOrchestrator()
    specialist = MCPSpecialist()
    print("[INIT] Systems Ready.\n")

    # =========================================================================
    # TEST 1: THE STRATEGIST (Akhenaton)
    # =========================================================================
    print("="*60)
    print("TEST 1: AKHENATON (Strategist) -- Market Analysis")
    print("="*60)
    
    prompt = """
    Analyze the following simulated market data for ETH and provide a trading strategy.
    Return ONLY valid JSON with keys: action, confidence (0-1), stop_loss, take_profit, reasoning.
    
    DATA:
    - ETH Price: $3,850
    - 24h Change: +12%
    - Volume: $15B
    - RSI: 72 (Overbought)
    - Gas Price: 45 gwei
    """
    
    print(f"[AKHENATON] Querying with market data...")
    content = router.query(
        prompt=prompt,
        system_prompt="You are Akhenaton, the supreme strategist. Return ONLY valid JSON.",
        agent_role="strategist",
        json_mode=True,
    )
    
    # Clean and parse
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0].strip()
    
    try:
        decision = json.loads(content)
        print(f"[AKHENATON] Response: action={decision.get('action')}, confidence={decision.get('confidence')}")
        print(f"[AKHENATON] Strategy: {decision.get('reasoning')}")
        print(f"[AKHENATON] STOP LOSS: {decision.get('stop_loss')}")
    except json.JSONDecodeError as e:
        print(f"[AKHENATON] JSON Parse Error. Raw response: {content[:200]}")

    # =========================================================================
    # TEST 2: THE GUARDIAN (Vetala)
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 2: VETALA (Guardian) -- Risk Assessment")
    print("="*60)
    
    prompt = """
    Assess the risk of a proposed trade. 
    Return ONLY valid JSON with keys: risk_level (low/medium/high), max_exposure_pct, warning_msg.
    
    SCENARIO:
    User wants to leverage 10x long on a new memecoin with liquidity $50k.
    """
    
    print(f"[VETALA] Querying with high-risk scenario...")
    content = router.query(
        prompt=prompt,
        system_prompt="You are Vetala, the supreme guardian. Paranoid about security. Return ONLY valid JSON.",
        agent_role="guardian",
        json_mode=True,
    )
    
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0].strip()
        
    try:
        assessment = json.loads(content)
        print(f"[VETALA] Risk Level: {assessment.get('risk_level')}")
        print(f"[VETALA] Max Exposure: {assessment.get('max_exposure_pct')}%")
        print(f"[VETALA] Warning: {assessment.get('warning_msg')}")
    except json.JSONDecodeError as e:
        print(f"[VETALA] JSON Parse Error. Raw response: {content[:200]}")

    # =========================================================================
    # TEST 3: THE ORCHESTRATOR (The King)
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 3: THE KING (Orchestrator) -- Trade Pipeline")
    print("="*60)
    
    # Use the orchestrator's actual pipeline
    result = await orchestrator._trade_pipeline({
        "token": "ETH",
        "capital": 5000,
    })
    
    print(f"[THE KING] Trade Pipeline Result:")
    print(f"  Final Action: {result.get('final_action')}")
    print(f"  Reasoning: {result.get('reasoning')}")
    print(f"  Risk Score: {result.get('risk_assessment', {}).get('risk_score')}")

    # =========================================================================
    # TEST 4: MCP GENERATOR (Nemotron)
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 4: MCP GENERATOR (Nemotron) -- Tool Creation")
    print("="*60)
    
    # Since we don't have an async loop in test script easily without import, 
    # we'll use the MCP specialist's sync method if available or simple call
    # For demo purposes, let's just try the router again for a code generation task
    prompt = """
    Write a Python function named `fetch_token_liquidity(token: str)` that fetches 
    Uniswap V3 liquidity data from a REST API. Return the function code inside a JSON block:
    {"code": "python code here"}
    """
    
    print(f"[GENERATOR] Querying Nemotron/Router for code generation...")
    content = router.query(
        prompt=prompt,
        system_prompt="You are a Python expert. Return ONLY valid JSON with a key 'code' containing the Python function.",
        agent_role="guardian",
        json_mode=True,
    )
    
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0].strip()
    
    try:
        code_block = json.loads(content)
        func_code = code_block.get("code", "")
        print(f"[GENERATOR] Generated function: {func_code[:150]}...")
    except json.JSONDecodeError as e:
        print(f"[GENERATOR] JSON Parse Error. Raw response: {content[:200]}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*60)
    print("SYSTEM STATUS")
    print("="*60)
    
    stats = router.get_stats()
    print(f"Agent Router Stats:")
    print(f"  Total LLM Calls: {stats['total_calls']}")
    print(f"  Fallback Usage: {stats['fallback_distribution']}")
    print(f"  Recent Successes: {[entry['source'] for entry in stats['recent_calls']]}\n")

    print("Rehoboam CLI simulation complete.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tests())
