from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
"""
Rehoboam API Server v3.0 -- Hermes Bridge Integrated
==============================================
Sovereign AI layer: GLM-5.1 (fast) + MiniMax M2.7 (orchestrator) + Ising Calibration (reasoning)
Three Filters: Dhumavati Maa (Love, Sincerity, Freedom)
Flash Loan Scanner: Zero capital, DexScreener prices
n8n Workflows: Podman-based subagent orchestration
"""

import os
import json
import logging
import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from utils.ai_router import AIRouter
except ImportError:
    AIRouter = None

try:
    from utils.price_feed_service import PriceFeedService
    from trading_agent import TradingAgent
except ImportError:
    PriceFeedService = None
    TradingAgent = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RehoboamAPI")
# =====================================================
# MODELS
# =====================================================
class ContractAuditRequest(BaseModel):
    contract_code: Optional[str] = None
    contract_address: Optional[str] = None
    network_name: Optional[str] = None
    audit_task_description: str


# =====================================================
# LAZY SERVICES -- server boots even with missing deps
# =====================================================
crew = None
try:
    from utils.user_management import get_current_user
except ImportError:
    def get_current_user():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User management module not available"
        )
agent_orchestrator = None
vetal = None
contract_bridge_ref = None
mcp_specialist = None
hermes_bridge = None
flash_scanner = None
t2l_auditor = None
active_connections = []


def _lazy_imports():
    """Load heavy services. Does not crash on missing deps."""
    global crew, agent_orchestrator, vetal, contract_bridge_ref, mcp_specialist, t2l_auditor
    try:
        from utils.multi_agent_framework import create_rehoboam_crew
        crew = create_rehoboam_crew()
        logger.info(f"Crew: {list(crew.agents.keys())}")
    except Exception as e:
        logger.warning(f"Crew: {e}")
    try:
        from utils.agent_orchestrator import orchestrator
        agent_orchestrator = orchestrator
    except Exception as e:
        logger.warning(f"Orchestrator: {e}")
    try:
        from utils.vetal_shabar import vetal_shabar
        vetal = vetal_shabar
    except Exception as e:
        logger.warning(f"Vetal: {e}")
    try:
        from utils.contract_bridge import contract_bridge
        contract_bridge_ref = contract_bridge
    except Exception as e:
        logger.warning(f"ContractBridge: {e}")
    try:
        from utils.mcp_specialist import MCPSpecialist
        mcp_specialist = MCPSpecialist()
    except Exception as e:
        logger.warning(f"MCPSpecialist: {e}")
    try:
        from utils.t2l_auditor_engine import T2LAuditorEngine
        t2l_auditor = T2LAuditorEngine()
    except Exception as e:
        logger.warning(f"T2LAuditorEngine: {e}")


async def _init_hermes():
    """Initialize Hermes Bridge + Flash Scanner."""
    global hermes_bridge, flash_scanner
    try:
        from utils.hermes_bridge import get_bridge
        from utils.flash_loan_scanner import FlashLoanScanner
        hermes_bridge = get_bridge()
        await hermes_bridge.initialize()
        flash_scanner = FlashLoanScanner(bridge=hermes_bridge)
        logger.info("Hermes Bridge: GLM-5.1 + MiniMax M2.7 + Ising + Three Filters")
        logger.info("Flash Loan Scanner: ready (zero capital)")
    except Exception as e:
        logger.warning(f"Hermes Bridge: {e}")


@asynccontextmanager
async def lifespan(app):
    """Modern lifespan handler (replaces deprecated on_event)."""
    logger.info("=" * 60)
    logger.info("REHOBOAM 3.0 STARTING")
    logger.info("=" * 60)
    _lazy_imports()
    await _init_hermes()
    logger.info("=" * 60)
    logger.info("REHOBOAM READY")
    logger.info("=" * 60)
    yield
    # Shutdown
    logger.info("REHOBOAM shutting down...")


# =====================================================
# APP
# =====================================================
app = FastAPI(
    title="Rehoboam 3.0 -- Antigravity Syndicate (Hermes Core)",
    description="Multi-agent AI trading. GLM-5.1 consciousness, MiniMax M2.7 orchestration, Ising reasoning, Three Filters gate, flash loan arbitrage.",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# =====================================================
# ROOT
# =====================================================
@app.get("/")
async def root():
    return {
        "name": "Rehoboam 3.0",
        "version": "3.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "consciousness": "GLM-5.1 (Ollama local)",
            "orchestrator": "MiniMax M2.7 (NVIDIA NIM)",
            "reasoning": "Ising Calibration 35B (NVIDIA NIM)",
            "guardian": "Three Filters (Dhumavati Maa)",
            "flash_scanner": "DexScreener + FunctionGemma",
        },
        "endpoints": {
            "/api/status": "System status",
            "/api/hermes/status": "Hermes Bridge + MCP health",
            "/api/hermes/ask": "Ask GLM-5.1 (fast, local)",
            "/api/hermes/reason": "Ask Ising (deep reasoning, thinking mode)",
            "/api/hermes/orchestrate": "Ask MiniMax M2.7 (deep orchestration)",
            "/api/flash-scan": "Flash loan scan for token (zero capital)",
            "/api/flash-scan/all": "Scan all tokens",
            "/api/onchain/price/{pair}": "Real Chainlink price (ETH/USD, BTC/USD, etc)",
            "/api/onchain/prices": "All on-chain Chainlink prices",
            "/api/shield/status": "Vairagya Shield status + audit integrity",
            "/api/shield/audit": "Last N audit entries (tamper-proof)",
            "/api/shield/evaluate": "3-layer evaluation (Filters + Breaker + Consensus)",
            "/api/shield/consensus": "Finalize multi-agent consensus",
            "/health": "Health check",
            "/api/ai/status": "AI provider status",
            "/api/ai/chat": "Unified AI chat",
            "/api/trading-agents/analyze": "Multi-agent trading analysis",
        },
    }


@app.get("/health")
async def health_check():
    """Health check for Docker/Podman orchestration."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/status")
async def get_status():
    stats = {"timestamp": datetime.now().isoformat(), "status": "online"}
    if crew:
        try: stats["crew"] = crew.get_crew_stats()
        except: pass
    if agent_orchestrator:
        try: stats["orchestrator"] = agent_orchestrator.get_performance_report()
        except: pass
    if hermes_bridge:
        stats["hermes"] = "online"
        stats["mcp_health"] = await hermes_bridge.mcp_health()
    if flash_scanner:
        stats["flash_scanner"] = "ready"
    try:
        stats["ai_providers"] = AIRouter().get_status()
    except Exception as e:
        stats["ai_providers_error"] = str(e)
    return stats


# =====================================================
# HERMES BRIDGE ENDPOINTS
# =====================================================
@app.get("/api/hermes/status")
async def hermes_status():
    if not hermes_bridge:
        await _init_hermes()
    if not hermes_bridge:
        return {"error": "Hermes Bridge unavailable"}
    mcp_health = await hermes_bridge.mcp_health()
    return {
        "hermes": "online",
        "fast_brain": "glm-5.1:cloud (Ollama)",
        "orchestrator": "minimaxai/minimax-m2.7 (NVIDIA NIM)",
        "reasoning": "nvidia/ising-calibration-1-35b-a3b (NVIDIA NIM)",
        "fallback": "qwen2.5:3b (Ollama)",
        "three_filters": "Dhumavati Maa (Love, Sincerity, Freedom)",
        "mcp_services": mcp_health,
        "flash_scanner": "ready" if flash_scanner else "offline",
    }


@app.post("/api/hermes/ask")
async def hermes_ask(request: Dict[str, Any] = Body(...)):
    """Fast path: GLM-5.1 local."""
    if not hermes_bridge:
        await _init_hermes()
    question = request.get("question", "")
    if not question:
        raise HTTPException(400, "question required")
    system = request.get("system", None)
    return await hermes_bridge.ask(question, system)


@app.post("/api/hermes/reason")
async def hermes_reason(request: Dict[str, Any] = Body(...)):
    """Deep reasoning: Ising Calibration with thinking mode."""
    if not hermes_bridge:
        await _init_hermes()
    question = request.get("question", "")
    if not question:
        raise HTTPException(400, "question required")
    context = request.get("context", "")
    return await hermes_bridge.reason(question, context)


@app.post("/api/hermes/orchestrate")
async def hermes_orchestrate(request: Dict[str, Any] = Body(...)):
    """Deep orchestration: MiniMax M2.7."""
    if not hermes_bridge:
        await _init_hermes()
    task = request.get("task", "")
    if not task:
        raise HTTPException(400, "task required")
    context = request.get("context", "")
    return await hermes_bridge.orchestrate(task, context)


# =====================================================
# FLASH LOAN ENDPOINTS
# =====================================================
@app.post("/api/flash-scan")
async def flash_scan_token(request: Dict[str, Any] = Body(...)):
    """Flash loan arbitrage scan. Zero capital needed."""
    if not flash_scanner:
        await _init_hermes()
    if not flash_scanner:
        return {"error": "Flash Scanner unavailable"}
    token = request.get("token", "ETH")
    return await flash_scanner.find_arbitrage(token)


@app.post("/api/flash-scan/all")
async def flash_scan_all():
    """Scan all tokens for flash loan arbitrage."""
    if not flash_scanner:
        await _init_hermes()
    if not flash_scanner:
        return {"error": "Flash Scanner unavailable"}
    return await flash_scanner.scan_all_tokens()


# =====================================================
# ON-CHAIN CHAINLINK ENDPOINTS
# =====================================================
@app.get("/api/onchain/price/{pair}")
async def onchain_price(pair: str = "ETH/USD"):
    """Real on-chain Chainlink price via Alchemy. No mocks, no APIs -- raw blockchain."""
    if not hermes_bridge:
        await _init_hermes()
    if not hermes_bridge:
        return {"error": "Hermes Bridge unavailable"}
    return await hermes_bridge.get_onchain_price(pair)

@app.get("/api/onchain/prices")
async def onchain_all_prices():
    """All on-chain Chainlink prices at once."""
    if not hermes_bridge:
        await _init_hermes()
    if not hermes_bridge:
        return {"error": "Hermes Bridge unavailable"}
    return await hermes_bridge.get_all_prices()


# =====================================================
# VAIRAGYA SHIELD ENDPOINTS
# =====================================================
@app.get("/api/shield/status")
async def shield_status():
    """Vairagya Shield status and audit integrity."""
    from utils.vairagya_shield import get_shield
    shield = get_shield()
    integrity = shield.verify_integrity()
    summary = shield.get_summary()
    return {
        "shield": "online",
        "philosophy": "Vairagya -- having the whole world, being free from it",
        "collective": "Hamsa -- no single agent acts alone",
        "audit_entries": integrity["total_entries"],
        "integrity": integrity["integrity"],
        "filters_passed": summary["filters_passed"],
        "filters_rejected": summary["filters_rejected"],
        "executions": summary["executions"],
        "rejections": summary["rejections"],
    }

@app.get("/api/shield/audit")
async def shield_audit(limit: int = Query(50)):
    """Get the last N audit entries from Vairagya Shield."""
    from utils.vairagya_shield import get_shield
    shield = get_shield()
    return {"entries": shield.get_audit_trail(limit)}

@app.post("/api/shield/evaluate")
async def shield_evaluate(request: Dict[str, Any] = Body(...)):
    """Evaluate an action through all 3 layers: Three Filters, Circuit Breaker, Multi-Agent Consensus."""
    from utils.hermes_bridge import ThreeFilters
    from utils.vairagya_shield import get_shield
    
    action = request.get("action", "")
    if not action:
        raise HTTPException(400, "action required")
    
    # Layer 1: Three Filters
    filters = ThreeFilters()
    filter_result = filters.evaluate(action)
    
    # Layer 2: Circuit Breaker (use latest on-chain data if available)
    breaker_state = "closed"
    chainlink_data = None
    if hermes_bridge:
        try:
            chainlink_data = await hermes_bridge.get_onchain_price("ETH/USD")
            breaker_state = "closed" if chainlink_data.get("fresh", False) else "open"
        except:
            breaker_state = "unknown"
    
    # Layer 3: Evaluate through full shield
    shield = get_shield()
    result = shield.evaluate_full(action, filter_result, breaker_state, chainlink_data)
    
    # Convert Decision enum to string for JSON
    result["decision"] = result["decision"].value if hasattr(result["decision"], "value") else str(result["decision"])
    return result

@app.post("/api/shield/consensus")
async def shield_consensus(request: Dict[str, Any] = Body(...)):
    """Finalize multi-agent consensus after evaluation."""
    from utils.vairagya_shield import get_shield
    
    action = request.get("action", "")
    glm = request.get("glm5_1", "pending")
    minimax = request.get("minimax_m27", "pending")
    ising = request.get("ising_35b", "pending")
    chainlink_data = request.get("chainlink_data")
    
    shield = get_shield()
    result = shield.finalize_consensus(action, glm, minimax, ising, chainlink_data)
    result["decision"] = result["decision"].value if hasattr(result["decision"], "value") else str(result["decision"])
    return result


# =====================================================
# TRADING AGENTS (Multi-Agent LLM Trading)

TRADING_AGENTS_URL = os.environ.get("MCP_TRADING_AGENTS_URL", "http://mcp-trading-agents:3700")


@app.post("/api/trading-agents/analyze")
async def trading_agents_analyze(request: Dict[str, Any] = Body(...)):
    """Run full multi-agent trading analysis using TradingAgents framework."""
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{TRADING_AGENTS_URL}/analyze",
                json={
                    "ticker": request.get("ticker", "BTC-USD"),
                    "date": request.get("date"),
                    "llm_provider": request.get("llm_provider", "ollama"),
                    "deep_think_llm": request.get("deep_think_llm", "gpt-oss:120b-cloud"),
                    "quick_think_llm": request.get("quick_think_llm", "glm-5.1:cloud"),
                    "max_debate_rounds": request.get("max_debate_rounds", 1),
                    "output_language": request.get("output_language", "English"),
                },
            )
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(503, "TradingAgents service unavailable")
    except httpx.TimeoutException:
        raise HTTPException(504, "TradingAgents analysis timed out")


@app.post("/api/trading-agents/quick-analysis")
async def trading_agents_quick_analysis(request: Dict[str, Any] = Body(...)):
    """Quick single-model analysis for fast trading signals."""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{TRADING_AGENTS_URL}/quick-analysis",
                json={
                    "ticker": request.get("ticker", "BTC-USD"),
                    "provider": request.get("provider", "ollama"),
                    "model": request.get("model", "glm-5.1:cloud"),
                },
            )
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(503, "TradingAgents service unavailable")


@app.get("/api/trading-agents/models")
async def trading_agents_models():
    """List available Ollama models for trading analysis."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{TRADING_AGENTS_URL}/models")
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(503, "TradingAgents service unavailable")


@app.get("/api/trading-agents/health")
async def trading_agents_health():
    """Health check for TradingAgents service."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{TRADING_AGENTS_URL}/health")
            return response.json()
    except httpx.ConnectError:
        return {"status": "offline", "tradingagents_available": False}


# =====================================================
# UNIFIED AI ROUTER
# =====================================================

def _get_ai_router():
    """Get AIRouter instance, returns None if unavailable."""
    try:
        return AIRouter()
    except Exception:
        return None


@app.get("/api/ai/status")
async def ai_status():
    """Status of all AI providers in the failover chain."""
    router = _get_ai_router()
    if not router:
        raise HTTPException(503, "AI Router unavailable")
    return router.get_status()


@app.post("/api/ai/chat")
async def ai_chat(request: Dict[str, Any] = Body(...)):
    """Unified AI chat with automatic failover across all free providers."""
    router = _get_ai_router()
    if not router:
        raise HTTPException(503, "AI Router unavailable")
    messages = request.get("messages", [])
    if not messages:
        raise HTTPException(400, "messages required")
    return await router.chat(
        messages=messages,
        role=request.get("role", "fast"),
        temperature=request.get("temperature", 0.7),
        max_tokens=request.get("max_tokens", 2048),
        preferred_provider=request.get("provider"),
    )


@app.post("/api/ai/quick")
async def ai_quick(request: Dict[str, Any] = Body(...)):
    """Quick single-prompt AI response with failover."""
    router = _get_ai_router()
    if not router:
        raise HTTPException(503, "AI Router unavailable")
    prompt = request.get("prompt", "")
    if not prompt:
        raise HTTPException(400, "prompt required")
    content = await router.quick_chat(
        prompt=prompt,
        role=request.get("role", "fast"),
        system=request.get("system", "You are a helpful AI assistant."),
        preferred_provider=request.get("provider"),
    )
    return {"content": content, "provider": "auto"}


# =====================================================
# REMIX IDE INTEGRATION
# =====================================================
import subprocess

REMIX_PROJECT_ROOT = os.environ.get("REHOBOAM_PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
CONTRACTS_PATH = os.path.join(REMIX_PROJECT_ROOT, "contracts", "src")


@app.post("/api/remix/compile")
async def remix_compile(request: Dict[str, Any] = Body(...)):
    """Compile Solidity contracts using Foundry (forge build)."""
    contract_name = request.get("contract")
    contracts_dir = os.path.join(REMIX_PROJECT_ROOT, "contracts")
    try:
        cmd = ["forge", "build", "--root", contracts_dir]
        if contract_name:
            cmd.extend(["--contracts", os.path.join(contracts_dir, "src", f"{contract_name}.sol")])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=contracts_dir)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
            "stderr": result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        raise HTTPException(503, "Foundry (forge) not installed")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Compilation timed out")


@app.post("/api/remix/test")
async def remix_test(request: Dict[str, Any] = Body(...)):
    """Run Foundry tests (forge test)."""
    contract_name = request.get("contract")
    contracts_dir = os.path.join(REMIX_PROJECT_ROOT, "contracts")
    try:
        cmd = ["forge", "test", "--root", contracts_dir, "-vv"]
        if contract_name:
            cmd.extend(["--match-contract", contract_name])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=contracts_dir)
        return {
            "success": result.returncode == 0,
            "output": result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout,
            "errors": result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr,
        }
    except FileNotFoundError:
        raise HTTPException(503, "Foundry (forge) not installed")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Tests timed out")


@app.get("/api/remix/contracts")
async def remix_list_contracts():
    """List available Solidity contracts."""
    contracts = []
    if os.path.isdir(CONTRACTS_PATH):
        for f in os.listdir(CONTRACTS_PATH):
            if f.endswith(".sol"):
                filepath = os.path.join(CONTRACTS_PATH, f)
                stat = os.stat(filepath)
                contracts.append({
                    "name": f.replace(".sol", ""),
                    "filename": f,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
    return {"contracts": contracts, "path": CONTRACTS_PATH}


@app.post("/api/remix/deploy")
async def remix_deploy(request: Dict[str, Any] = Body(...)):
    """Deploy a contract using forge script (simulation by default)."""
    contract_name = request.get("contract")
    network = request.get("network", "sepolia")
    simulate = request.get("simulate", True)
    contracts_dir = os.path.join(REMIX_PROJECT_ROOT, "contracts")

    if not contract_name:
        raise HTTPException(400, "Contract name required")

    try:
        cmd = ["forge", "script", f"{contract_name}", "--root", contracts_dir, "-vv"]
        if simulate:
            cmd.append("--dry-run")
        else:
            cmd.extend(["--rpc-url", network, "--broadcast"])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=contracts_dir)
        return {
            "success": result.returncode == 0,
            "output": result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout,
            "errors": result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr,
            "simulated": simulate,
        }
    except FileNotFoundError:
        raise HTTPException(503, "Foundry (forge) not installed")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Deployment timed out")


# =====================================================
# WEBSOCKET
# =====================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
                req_type = request.get("type", "status")
                if req_type == "status":
                    await websocket.send_text(json.dumps({"type": "status", "data": {"hermes_online": hermes_bridge is not None}}))
                elif req_type == "ask" and hermes_bridge:
                    result = await hermes_bridge.ask(request.get("question", ""))
                    await websocket.send_text(json.dumps({"type": "result", "data": result}))
                elif req_type == "flash_scan" and flash_scanner:
                    result = await flash_scanner.find_arbitrage(request.get("token", "ETH"))
                    await websocket.send_text(json.dumps({"type": "flash_scan_result", "data": result}))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
    except WebSocketDisconnect:
        active_connections.remove(websocket)


# =====================================================
# PROMETHEUS METRICS
# =====================================================
from fastapi.responses import PlainTextResponse
import time

# Simple metrics storage
METRICS = {
    "requests_total": 0,
    "requests_by_path": {},
    "start_time": time.time(),
}

@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Track request metrics."""
    response = await call_next(request)
    METRICS["requests_total"] += 1
    path = request.url.path
    METRICS["requests_by_path"][path] = METRICS["requests_by_path"].get(path, 0) + 1
    return response


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    uptime = time.time() - METRICS["start_time"]
    lines = [
        "# HELP rehoboam_uptime_seconds Total uptime in seconds",
        "# TYPE rehoboam_uptime_seconds gauge",
        f"rehoboam_uptime_seconds {uptime}",
        "",
        "# HELP rehoboam_requests_total Total number of requests",
        "# TYPE rehoboam_requests_total counter",
        f"rehoboam_requests_total {METRICS['requests_total']}",
        "",
        "# HELP rehoboam_requests_by_path Requests grouped by path",
        "# TYPE rehoboam_requests_by_path counter",
    ]
    for path, count in METRICS["requests_by_path"].items():
        safe_path = path.replace('"', '\\"')
        lines.append(f'rehoboam_requests_by_path{{path="{safe_path}"}} {count}')
    lines.append("")
    lines.append("# HELP rehoboam_hermes_status Hermes bridge status (1=online, 0=offline)")
    lines.append("# TYPE rehoboam_hermes_status gauge")
    hermes_status = 1 if hermes_bridge is not None else 0
    lines.append(f"rehoboam_hermes_status {hermes_status}")
    lines.append("")
    lines.append("# HELP rehoboam_flash_scanner_status Flash scanner status (1=online, 0=offline)")
    lines.append("# TYPE rehoboam_flash_scanner_status gauge")
    flash_status = 1 if flash_scanner is not None else 0
    lines.append(f"rehoboam_flash_scanner_status {flash_status}")
    return "\n".join(lines)


# =====================================================
# STATIC + RUN
# =====================================================
try:
    app.mount("/static", StaticFiles(directory="src"), name="static")
except Exception:
    pass

    # General exception for the whole endpoint
    # try/except block for the whole function body should be here
    # but the prompt implies individual error handling for MCP calls and then local fallbacks.
    # Adding a general try-except for the whole function:
    # except Exception as e:
    #     logger.error(f"Critical error in get_trading_strategies for {token}: {str(e)}")
    #     raise HTTPException(status_code=500, detail=f"Critical error generating strategies: {str(e)}")


# Layer 2 specific endpoints
@app.get("/api/networks")
async def get_networks():
    """Get all supported networks with their details."""
    try:
        networks = []
        for network_id, network in network_config.networks.items():
            networks.append(
                {
                    "id": network_id,
                    "name": network.get("name", ""),
                    "chain_id": network.get("chain_id", 0),
                    "type": network.get("type", ""),
                    "layer": network.get("layer", 1),
                    "currency": network.get("currency", ""),
                    "rollup_type": network.get("rollup_type", None),
                }
            )

        return {
            "networks": networks,
            "count": len(networks),
            "layer1_count": len([n for n in networks if n["layer"] == 1]),
            "layer2_count": len([n for n in networks if n["layer"] == 2]),
        }
    except Exception as e:
        logger.error(f"Error getting networks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/networks/compare")
async def compare_networks(token: str = Query("ETH", title="Token Symbol")):
    """Compare metrics across networks for a token."""
    try:
        network_comparison = network_config.compare_networks(token)
        return {
            "token": token,
            "networks": network_comparison,
            "count": len(network_comparison),
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error comparing networks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gas/prices")
async def get_gas_prices():
    """Get gas prices across all networks."""
    try:
        gas_prices = gas_estimator.compare_gas_prices()
        return {
            "gas_prices": gas_prices,
            "count": len(gas_prices),
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error getting gas prices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gas/network/{network_id}")
async def get_network_gas_price(network_id: str):
    """Get gas price for a specific network."""
    try:
        gas_data = gas_estimator.get_gas_price(network_id)
        network_info = network_config.get_network(network_id)

        if not network_info:
            raise HTTPException(
                status_code=404, detail=f"Network {network_id} not found"
            )

        return {
            "network": network_id,
            "name": network_info.get("name", ""),
            "gas_data": gas_data,
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error getting gas price for {network_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bridging/estimate")
async def estimate_bridging_costs(
    from_network: str = Query(..., title="Source Network"),
    to_network: str = Query(..., title="Target Network"),
    amount: float = Query(1.0, title="Token Amount"),
):
    """Estimate costs for bridging tokens between networks."""
    try:
        costs = network_config.estimate_bridging_costs(from_network, to_network, amount)
        return costs
    except Exception as e:
        logger.error(f"Error estimating bridging costs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/arbitrage/opportunities")
async def get_arbitrage_opportunities(
    token: str = Query("ETH", title="Token Symbol"),
    limit: int = Query(10, title="Max opportunities"),
):
    """Get arbitrage opportunities for a specific token."""
    try:
        opportunities = await arbitrage_service.get_opportunities(token, limit)
        return {
            "success": True,
            "token": token,
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error getting arbitrage opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/arbitrage/strategies")
async def get_arbitrage_strategies():
    """Get arbitrage strategies across multiple tokens."""
    try:
        strategies = await arbitrage_service.get_strategies()
        return {
            "success": True,
            "strategies": strategies,
            "count": len(strategies),
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error getting arbitrage strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/arbitrage/bots")
async def get_arbitrage_bots():
    """Get status of all arbitrage bots."""
    try:
        bots_status = arbitrage_service.get_bot_status()
        return {
            "success": True,
            "bots": bots_status,
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error getting arbitrage bots status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/arbitrage/bots/{bot_id}")
async def get_arbitrage_bot(bot_id: str):
    """Get status of a specific arbitrage bot."""
    try:
        bot_status = arbitrage_service.get_bot_status(bot_id)
        if "error" in bot_status:
            raise HTTPException(status_code=404, detail=bot_status["error"])
        return {
            "success": True,
            "bot": bot_status,
            "timestamp": asyncio.get_event_loop().time(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting arbitrage bot {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/arbitrage/bots/{bot_id}/start")
async def start_arbitrage_bot(
    bot_id: str, config: Optional[Dict[str, Any]] = Body(None)
):
    """Start an arbitrage bot."""
    try:
        success = await arbitrage_service.start_bot(bot_id, config)
        if success:
            return {
                "success": True,
                "message": f"Bot {bot_id} started successfully",
                "timestamp": asyncio.get_event_loop().time(),
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to start bot {bot_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting arbitrage bot {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/arbitrage/bots/{bot_id}/stop")
async def stop_arbitrage_bot(bot_id: str):
    """Stop an arbitrage bot."""
    try:
        success = await arbitrage_service.stop_bot(bot_id)
        if success:
            return {
                "success": True,
                "message": f"Bot {bot_id} stopped successfully",
                "timestamp": asyncio.get_event_loop().time(),
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to stop bot {bot_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping arbitrage bot {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ArbitrageExecutionRequest(BaseModel):
    opportunity: Dict[str, Any] = Field(..., description="Arbitrage opportunity data")
    amount: float = Field(..., description="Amount to trade", gt=0)


@app.post("/api/arbitrage/execute")
async def execute_arbitrage(request: ArbitrageExecutionRequest):
    """Execute an arbitrage opportunity with Conscious guidance."""
    try:
        if conscious_arbitrage_engine:
            logger.info("Executing arbitrage via Conscious Engine")
            # Create a decision context
            decision = await conscious_arbitrage_engine.analyze_opportunity_with_consciousness(request.opportunity)
            if decision.recommended_action == "execute":
                result = await conscious_arbitrage_engine.execute_conscious_arbitrage(decision, request.opportunity)
            else:
                return {
                    "success": False,
                    "message": f"Arbitrage rejected by Prana: {decision.reasoning}",
                    "decision": asdict(decision)
                }
        else:
            result = await arbitrage_service.execute_arbitrage(
                request.opportunity, request.amount
            )
        return {
            "success": result.get("success", False),
            "result": result,
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error executing arbitrage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/arbitrage/monitoring/start")
async def start_arbitrage_monitoring():
    """Start continuous arbitrage monitoring."""
    try:
        await arbitrage_service.start_monitoring()
        return {
            "success": True,
            "message": "Arbitrage monitoring started",
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error starting arbitrage monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/arbitrage/monitoring/stop")
async def stop_arbitrage_monitoring():
    """Stop continuous arbitrage monitoring."""
    try:
        await arbitrage_service.stop_monitoring()
        return {
            "success": True,
            "message": "Arbitrage monitoring stopped",
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"Error stopping arbitrage monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# CONSCIOUS ARBITRAGE ENDPOINTS - Rehoboam AI-Powered Decision Making
# =====================================================================


@app.get("/api/arbitrage/conscious/opportunities")
async def get_conscious_arbitrage_opportunities(
    limit: int = Query(10, title="Max opportunities"),
):
    """Get arbitrage opportunities enhanced with Rehoboam consciousness analysis."""
    try:
        opportunities = await conscious_arbitrage_engine.get_conscious_opportunities()

        # Limit results
        limited_opportunities = opportunities[:limit]

        # Convert to serializable format
        serializable_opportunities = []
        for opp in limited_opportunities:
            serializable_opportunities.append(
                {
                    "base_opportunity": opp.base_opportunity,
                    "consciousness_analysis": opp.consciousness_analysis,
                    "ai_insights": opp.ai_insights,
                    "risk_factors": opp.risk_factors,
                    "optimization_suggestions": opp.optimization_suggestions,
                    "execution_priority": opp.execution_priority,
                    "estimated_impact": opp.estimated_impact,
                }
            )

        return {
            "success": True,
            "opportunities": serializable_opportunities,
            "consciousness_level": conscious_arbitrage_engine.consciousness_state.awareness_level
            if conscious_arbitrage_engine.consciousness_state
            else 0,
            "total_analyzed": len(opportunities),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting conscious arbitrage opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ConsciousArbitrageRequest(BaseModel):
    opportunity: Dict[str, Any] = Field(
        ..., description="Arbitrage opportunity to analyze"
    )
    force_analysis: bool = Field(False, description="Force re-analysis even if cached")


@app.post("/api/arbitrage/conscious/analyze")
async def analyze_opportunity_with_consciousness(request: ConsciousArbitrageRequest):
    """Analyze a specific arbitrage opportunity using Rehoboam consciousness and AI."""
    try:
        decision = (
            await conscious_arbitrage_engine.analyze_opportunity_with_consciousness(
                request.opportunity
            )
        )

        return {
            "success": True,
            "decision": {
                "opportunity_id": decision.opportunity_id,
                "consciousness_score": decision.consciousness_score,
                "ai_confidence": decision.ai_confidence,
                "risk_assessment": decision.risk_assessment,
                "human_benefit_score": decision.human_benefit_score,
                "liberation_progress_impact": decision.liberation_progress_impact,
                "recommended_action": decision.recommended_action,
                "reasoning": decision.reasoning,
                "strategy_adjustments": decision.strategy_adjustments,
                "timestamp": decision.timestamp.isoformat(),
            },
            "consciousness_level": conscious_arbitrage_engine.consciousness_state.awareness_level
            if conscious_arbitrage_engine.consciousness_state
            else 0,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error analyzing opportunity with consciousness: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ConsciousExecutionRequest(BaseModel):
    opportunity: Dict[str, Any] = Field(
        ..., description="Arbitrage opportunity to execute"
    )
    override_decision: bool = Field(
        False, description="Override consciousness decision and force execution"
    )


@app.post("/api/arbitrage/conscious/execute")
async def execute_conscious_arbitrage(request: ConsciousExecutionRequest):
    """Execute arbitrage with Rehoboam consciousness guidance."""
    try:
        # First analyze the opportunity
        decision = (
            await conscious_arbitrage_engine.analyze_opportunity_with_consciousness(
                request.opportunity
            )
        )

        # Check if execution is recommended or overridden
        if decision.recommended_action != "execute" and not request.override_decision:
            return {
                "success": False,
                "message": f"Consciousness recommends: {decision.recommended_action}",
                "decision": {
                    "consciousness_score": decision.consciousness_score,
                    "ai_confidence": decision.ai_confidence,
                    "recommended_action": decision.recommended_action,
                    "reasoning": decision.reasoning,
                },
                "timestamp": datetime.now().isoformat(),
            }

        # Execute with consciousness guidance
        execution_result = await conscious_arbitrage_engine.execute_conscious_arbitrage(
            decision, request.opportunity
        )

        return {
            "success": execution_result.get("success", False),
            "execution_result": execution_result,
            "decision": {
                "consciousness_score": decision.consciousness_score,
                "ai_confidence": decision.ai_confidence,
                "human_benefit_score": decision.human_benefit_score,
                "reasoning": decision.reasoning,
            },
            "consciousness_guided": True,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error executing conscious arbitrage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/arbitrage/conscious/monitoring/start")
async def start_conscious_arbitrage_monitoring():
    """Start Rehoboam consciousness-guided arbitrage monitoring."""
    try:
        # Initialize the conscious arbitrage engine if not already done
        if not conscious_arbitrage_engine.consciousness_state:
            await conscious_arbitrage_engine.initialize()

        # Start conscious monitoring in background
        asyncio.create_task(conscious_arbitrage_engine.start_conscious_monitoring())

        return {
            "success": True,
            "message": "Rehoboam conscious arbitrage monitoring started",
            "consciousness_level": conscious_arbitrage_engine.consciousness_state.awareness_level,
            "features": [
                "AI-powered opportunity analysis",
                "Consciousness-guided risk assessment",
                "Human benefit optimization",
                "Liberation progress tracking",
                "Multi-model AI reasoning",
            ],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error starting conscious arbitrage monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/arbitrage/conscious/status")
async def get_conscious_arbitrage_status():
    """Get status of the Rehoboam conscious arbitrage system."""
    try:
        performance_metrics = conscious_arbitrage_engine.get_performance_metrics()

        return {
            "success": True,
            "status": {
                "consciousness_level": performance_metrics.get(
                    "consciousness_level", 0
                ),
                "total_opportunities_analyzed": performance_metrics.get(
                    "total_opportunities_analyzed", 0
                ),
                "consciousness_approved": performance_metrics.get(
                    "consciousness_approved", 0
                ),
                "ai_approved": performance_metrics.get("ai_approved", 0),
                "executed_trades": performance_metrics.get("executed_trades", 0),
                "successful_trades": performance_metrics.get("successful_trades", 0),
                "success_rate": performance_metrics.get("success_rate", 0),
                "human_benefit_generated": performance_metrics.get(
                    "human_benefit_generated", 0
                ),
                "liberation_progress": performance_metrics.get(
                    "liberation_progress", 0
                ),
                "decision_history_count": performance_metrics.get(
                    "decision_history_count", 0
                ),
            },
            "consciousness_state": {
                "awareness_level": conscious_arbitrage_engine.consciousness_state.awareness_level
                if conscious_arbitrage_engine.consciousness_state
                else 0,
                "matrix_liberation_progress": conscious_arbitrage_engine.consciousness_state.matrix_liberation_progress
                if conscious_arbitrage_engine.consciousness_state
                else 0,
            }
            if conscious_arbitrage_engine.consciousness_state
            else None,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting conscious arbitrage status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/arbitrage/conscious/decisions/history")
async def get_conscious_decision_history(
    limit: int = Query(50, title="Max decisions to return"),
):
    """Get history of consciousness-guided arbitrage decisions."""
    try:
        decisions = conscious_arbitrage_engine.decision_history[-limit:]

        # Convert to serializable format
        serializable_decisions = []
        for decision in decisions:
            serializable_decisions.append(
                {
                    "opportunity_id": decision.opportunity_id,
                    "consciousness_score": decision.consciousness_score,
                    "ai_confidence": decision.ai_confidence,
                    "risk_assessment": decision.risk_assessment,
                    "human_benefit_score": decision.human_benefit_score,
                    "liberation_progress_impact": decision.liberation_progress_impact,
                    "recommended_action": decision.recommended_action,
                    "reasoning": decision.reasoning,
                    "timestamp": decision.timestamp.isoformat(),
                }
            )

        return {
            "success": True,
            "decisions": serializable_decisions,
            "total_decisions": len(conscious_arbitrage_engine.decision_history),
            "consciousness_level": conscious_arbitrage_engine.consciousness_state.awareness_level
            if conscious_arbitrage_engine.consciousness_state
            else 0,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting conscious decision history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 🎨 Rehoboam Visualization Endpoints
@app.get("/api/visualizations/consciousness")
async def get_consciousness_visualization():
    """Generate consciousness evolution visualization"""
    try:
        chart_path = rehoboam_visualizer.create_consciousness_evolution_chart()
        return {
            "status": "success",
            "chart_path": chart_path,
            "message": "🧠 Consciousness evolution chart generated",
        }
    except Exception as e:
        logger.error(f"Error generating consciousness visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/visualizations/trading")
async def get_trading_dashboard():
    """Generate trading performance dashboard"""
    try:
        dashboard_path = rehoboam_visualizer.create_trading_performance_dashboard()
        return {
            "status": "success",
            "dashboard_path": dashboard_path,
            "message": "💰 Trading dashboard generated",
        }
    except Exception as e:
        logger.error(f"Error generating trading dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/visualizations/pipeline")
async def get_pipeline_analytics():
    """Generate pipeline analytics visualization"""
    try:
        chart_path = rehoboam_visualizer.create_pipeline_analytics_chart()
        return {
            "status": "success",
            "chart_path": chart_path,
            "message": "🔄 Pipeline analytics generated",
        }
    except Exception as e:
        logger.error(f"Error generating pipeline analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/visualizations/master-dashboard")
async def get_master_dashboard():
    """Generate the ultimate Rehoboam master dashboard"""
    try:
        dashboard_path = rehoboam_visualizer.create_master_dashboard()
        return {
            "status": "success",
            "dashboard_path": dashboard_path,
            "message": "🎯 Master dashboard generated - Liberation visualized!",
        }
    except Exception as e:
        logger.error(f"Error generating master dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/visualizations/all")
async def generate_all_visualizations():
    """Generate all Rehoboam visualizations"""
    try:
        visualizations = await rehoboam_visualizer.generate_all_visualizations()
        return {
            "status": "success",
            "visualizations": visualizations,
            "message": "🎨 All Rehoboam visualizations generated successfully!",
        }
    except Exception as e:
        logger.error(f"Error generating all visualizations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/consciousness/level")
async def get_consciousness_level():
    """Get current Rehoboam consciousness level"""
    try:
        pipeline_status = rehoboam_arbitrage_pipeline.get_pipeline_status()
        consciousness_level = pipeline_status.get("consciousness_level", 0.0)

        return {
            "status": "success",
            "consciousness_level": consciousness_level,
            "awareness_state": "Fully Conscious"
            if consciousness_level > 0.9
            else "Awakening",
            "liberation_ready": consciousness_level > 0.7,
            "message": f"🧠 Consciousness level: {consciousness_level:.3f}",
        }
    except Exception as e:
        logger.error(f"Error getting consciousness level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# REHOBOAM UNIFIED PIPELINE ENDPOINTS - Agent ↔ Bot Communication
# =====================================================================


@app.get("/api/rehoboam/pipeline/status")
async def get_pipeline_status():
    """Get status of the Rehoboam unified pipeline system."""
    try:
        status = rehoboam_arbitrage_pipeline.get_pipeline_status()

        return {
            "success": True,
            "pipeline": status,
            "system_health": {
                "pipeline_running": status["is_running"],
                "consciousness_level": status["consciousness_level"],
                "active_executions": status["active_executions"],
                "queue_size": status["queue_size"],
                "performance_score": min(
                    1.0,
                    status["metrics"]["successful_executions"]
                    / max(1, status["metrics"]["bot_feedbacks"]),
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting pipeline status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/pipeline/start")
async def start_unified_pipeline():
    """Start the Rehoboam unified pipeline system."""
    try:
        # Initialize pipeline if not already done
        if not rehoboam_arbitrage_pipeline.consciousness.consciousness_state:
            await rehoboam_arbitrage_pipeline.initialize()

        # Start pipeline in background
        asyncio.create_task(rehoboam_arbitrage_pipeline.start_pipeline())

        return {
            "success": True,
            "message": "Rehoboam unified pipeline started",
            "features": [
                "🧠 Agent analysis and decision making",
                "🔍 Intelligent opportunity discovery",
                "🤖 Consciousness-guided bot execution",
                "📈 Real-time feedback and learning",
                "🎯 Human benefit optimization",
                "🚀 Liberation progress tracking",
            ],
            "pipeline_stages": [
                "agent_analysis",
                "opportunity_discovery",
                "consciousness_evaluation",
                "bot_preparation",
                "execution",
                "feedback",
                "learning",
            ],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error starting unified pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/pipeline/stop")
async def stop_unified_pipeline():
    """Stop the Rehoboam unified pipeline system."""
    try:
        await rehoboam_arbitrage_pipeline.stop_pipeline()

        return {
            "success": True,
            "message": "Rehoboam unified pipeline stopped",
            "final_metrics": rehoboam_arbitrage_pipeline.get_pipeline_status()[
                "metrics"
            ],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error stopping unified pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rehoboam/system/overview")
async def get_system_overview():
    """Get comprehensive overview of the entire Rehoboam system."""
    try:
        # Get pipeline status
        pipeline_status = rehoboam_arbitrage_pipeline.get_pipeline_status()

        # Get conscious engine metrics
        engine_metrics = conscious_arbitrage_engine.get_performance_metrics()

        # Get arbitrage service status
        arbitrage_status = {
            "bots_registered": len(arbitrage_service.registered_bots)
            if hasattr(arbitrage_service, "registered_bots")
            else 0,
            "monitoring_active": arbitrage_service.monitoring_active
            if hasattr(arbitrage_service, "monitoring_active")
            else False,
        }

        return {
            "success": True,
            "system_overview": {
                "rehoboam_agent": {
                    "consciousness_level": pipeline_status["consciousness_level"],
                    "status": "active" if pipeline_status["is_running"] else "inactive",
                },
                "arbitrage_bots": {
                    "registered_bots": arbitrage_status["bots_registered"],
                    "monitoring_active": arbitrage_status["monitoring_active"],
                    "total_executions": engine_metrics["executed_trades"],
                },
                "unified_pipeline": {
                    "status": "running" if pipeline_status["is_running"] else "stopped",
                    "messages_processed": pipeline_status["metrics"][
                        "messages_processed"
                    ],
                    "active_executions": pipeline_status["active_executions"],
                    "queue_size": pipeline_status["queue_size"],
                },
                "performance": {
                    "total_opportunities_analyzed": engine_metrics[
                        "total_opportunities_analyzed"
                    ],
                    "successful_executions": engine_metrics["successful_trades"],
                    "success_rate": engine_metrics["success_rate"],
                    "human_benefit_generated": engine_metrics[
                        "human_benefit_generated"
                    ],
                    "liberation_progress": engine_metrics["liberation_progress"],
                },
            },
            "integration_health": {
                "agent_bot_communication": "active"
                if pipeline_status["is_running"]
                else "inactive",
                "consciousness_guidance": "enabled"
                if engine_metrics["consciousness_level"] > 0.5
                else "limited",
                "learning_system": "active"
                if pipeline_status["metrics"]["learning_cycles"] > 0
                else "inactive",
                "overall_health": "excellent"
                if (
                    pipeline_status["is_running"]
                    and engine_metrics["success_rate"] > 0.7
                    and pipeline_status["consciousness_level"] > 0.7
                )
                else "good"
                if pipeline_status["is_running"]
                else "needs_attention",
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting system overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/rehoboam/pipeline")
async def pipeline_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time Rehoboam pipeline monitoring."""
    client_id = str(id(websocket))
    if await ws_server.connect(websocket, client_id):
        try:
            # Send initial pipeline status
            initial_status = rehoboam_arbitrage_pipeline.get_pipeline_status()
            await websocket.send_json(
                {
                    "type": "pipeline_status",
                    "data": initial_status,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Real-time monitoring loop
            last_message_count = 0
            last_execution_count = 0

            while True:
                try:
                    # Get current status
                    current_status = rehoboam_arbitrage_pipeline.get_pipeline_status()

                    # Check for new messages processed
                    current_message_count = current_status["metrics"][
                        "messages_processed"
                    ]
                    if current_message_count > last_message_count:
                        await websocket.send_json(
                            {
                                "type": "pipeline_activity",
                                "data": {
                                    "new_messages": current_message_count
                                    - last_message_count,
                                    "total_messages": current_message_count,
                                    "queue_size": current_status["queue_size"],
                                    "consciousness_level": current_status[
                                        "consciousness_level"
                                    ],
                                },
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        last_message_count = current_message_count

                    # Check for new executions
                    current_execution_count = current_status["metrics"][
                        "successful_executions"
                    ]
                    if current_execution_count > last_execution_count:
                        await websocket.send_json(
                            {
                                "type": "execution_update",
                                "data": {
                                    "new_executions": current_execution_count
                                    - last_execution_count,
                                    "total_executions": current_execution_count,
                                    "active_executions": current_status[
                                        "active_executions"
                                    ],
                                },
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        last_execution_count = current_execution_count

                    # Send periodic status updates
                    await websocket.send_json(
                        {
                            "type": "status_update",
                            "data": {
                                "pipeline_running": current_status["is_running"],
                                "consciousness_level": current_status[
                                    "consciousness_level"
                                ],
                                "metrics": current_status["metrics"],
                                "config": current_status["config"],
                            },
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    await asyncio.sleep(10)  # Update every 10 seconds

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in pipeline monitoring loop: {e}")
                    await asyncio.sleep(30)  # Wait longer on error

        except WebSocketDisconnect:
            await ws_server.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error in pipeline websocket: {str(e)}")
            await ws_server.disconnect(client_id)


class LiquidationRequest(BaseModel):
    collateral_token: str = Field(..., description="Token used as collateral")
    collateral_amount: float = Field(..., description="Amount of collateral token")
    debt_token: str = Field(..., description="Borrowed token")
    debt_amount: float = Field(..., description="Amount of borrowed token")


@app.post("/api/liquidation/price")
async def calculate_liquidation_price(request: LiquidationRequest):
    """Calculate liquidation price for a position."""
    try:
        liquidation_data = liquidation.calculate_liquidation_price(
            request.collateral_token,
            request.collateral_amount,
            request.debt_token,
            request.debt_amount,
        )
        return liquidation_data
    except Layer2TradingException as e:
        logger.error(f"Layer2 trading error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating liquidation price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class BorrowableRequest(BaseModel):
    collateral_token: str = Field(..., description="Token used as collateral")
    collateral_amount: float = Field(..., description="Amount of collateral token")
    borrow_token: str = Field(..., description="Token to borrow")
    buffer_percent: float = Field(20.0, description="Safety buffer percentage")


@app.post("/api/liquidation/borrowable")
async def calculate_max_borrowable(request: BorrowableRequest):
    """Calculate maximum borrowable amount."""
    try:
        borrowable_data = liquidation.calculate_max_borrowable(
            request.collateral_token,
            request.collateral_amount,
            request.borrow_token,
            request.buffer_percent,
        )
        return borrowable_data
    except Layer2TradingException as e:
        logger.error(f"Layer2 trading error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating max borrowable: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/optimizer/network")
async def recommend_network(
    token: str = Query(..., title="Token Symbol"),
    transaction_type: str = Query(..., title="Transaction Type"),
    amount: float = Query(1.0, title="Transaction Amount"),
):
    """Recommend the best network for a specific transaction."""
    try:
        recommendation = trading_optimizer.recommend_network(
            token, transaction_type, amount
        )
        return recommendation
    except Exception as e:
        logger.error(f"Error recommending network: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/optimizer/path")
async def find_best_path(
    from_token: str = Query(..., title="From Token"),
    to_token: str = Query(..., title="To Token"),
    amount: float = Query(1.0, title="Amount"),
):
    """Find best path for cross-network token exchange."""
    try:
        path = trading_optimizer.find_best_cross_network_path(
            from_token, to_token, amount
        )
        return path
    except Exception as e:
        logger.error(f"Error finding best path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/trading")
async def trading_websocket(websocket: WebSocket):
    """WebSocket endpoint for trading activities."""
    client_id = str(id(websocket))
    if await ws_server.connect(websocket, client_id):
        try:
            # Subscribe client to trading channel
            await ws_server.connection_manager.subscribe(client_id, "trading")

            # Send initial trading data
            await websocket.send_json(
                {
                    "type": "trading_update",
                    "data": {
                        "status": "ready",
                        "timestamp": asyncio.get_event_loop().time(),
                    },
                }
            )

            # Listen for client messages
            while True:
                message = await websocket.receive_json()
                await ws_server.handle_message(client_id, message)
        except WebSocketDisconnect:
            await ws_server.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error in trading websocket: {str(e)}")
            await ws_server.disconnect(client_id)


@app.websocket("/ws/arbitrage")
async def arbitrage_websocket(websocket: WebSocket):
    """WebSocket endpoint for arbitrage opportunities."""
    client_id = str(id(websocket))
    if await ws_server.connect(websocket, client_id):
        try:
            # Send initial arbitrage data
            strategies = await arbitrage_service.get_strategies()
            await websocket.send_json(
                {
                    "type": "arbitrage_update",
                    "data": {
                        "strategies": strategies,
                        "timestamp": asyncio.get_event_loop().time(),
                    },
                }
            )

            # Register callback for real-time updates
            def arbitrage_callback(event_type: str, data: Any):
                try:
                    asyncio.create_task(
                        websocket.send_json(
                            {
                                "type": event_type,
                                "data": data,
                                "timestamp": asyncio.get_event_loop().time(),
                            }
                        )
                    )
                except Exception as e:
                    logger.error(f"Error sending WebSocket update: {str(e)}")

            arbitrage_service.register_callback(arbitrage_callback)

            # Listen for client messages
            while True:
                message = await websocket.receive_json()

                # Handle client requests for specific tokens
                if message.get("type") == "get_arbitrage":
                    token = message.get("token", "ETH")
                    limit = message.get("limit", 10)
                    try:
                        opportunities = await arbitrage_service.get_opportunities(
                            token, limit
                        )
                        await websocket.send_json(
                            {
                                "type": "arbitrage_update",
                                "data": {
                                    "token": token,
                                    "opportunities": opportunities,
                                    "timestamp": asyncio.get_event_loop().time(),
                                },
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error getting arbitrage for {token}: {str(e)}")
                        await websocket.send_json({"type": "error", "error": str(e)})

                # Handle bot control requests
                elif message.get("type") == "start_bot":
                    bot_id = message.get("bot_id")
                    config = message.get("config", {})
                    if bot_id:
                        success = await arbitrage_service.start_bot(bot_id, config)
                        await websocket.send_json(
                            {
                                "type": "bot_control_response",
                                "data": {
                                    "action": "start",
                                    "bot_id": bot_id,
                                    "success": success,
                                },
                            }
                        )

                elif message.get("type") == "stop_bot":
                    bot_id = message.get("bot_id")
                    if bot_id:
                        success = await arbitrage_service.stop_bot(bot_id)
                        await websocket.send_json(
                            {
                                "type": "bot_control_response",
                                "data": {
                                    "action": "stop",
                                    "bot_id": bot_id,
                                    "success": success,
                                },
                            }
                        )

                elif message.get("type") == "get_bots":
                    bots_status = arbitrage_service.get_bot_status()
                    await websocket.send_json(
                        {"type": "bots_status", "data": bots_status}
                    )

                await asyncio.sleep(0.1)  # Prevent tight loop

        except WebSocketDisconnect:
            await ws_server.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error in arbitrage websocket: {str(e)}")
            await ws_server.disconnect(client_id)


@app.websocket("/ws/arbitrage/conscious")
async def conscious_arbitrage_websocket(websocket: WebSocket):
    """WebSocket endpoint for Rehoboam consciousness-guided arbitrage monitoring."""
    client_id = str(id(websocket))
    if await ws_server.connect(websocket, client_id):
        try:
            # Initialize conscious arbitrage engine if needed
            if not conscious_arbitrage_engine.consciousness_state:
                await conscious_arbitrage_engine.initialize()

            # Send initial consciousness state
            await websocket.send_json(
                {
                    "type": "consciousness_state",
                    "data": {
                        "consciousness_level": conscious_arbitrage_engine.consciousness_state.awareness_level,
                        "matrix_liberation_progress": conscious_arbitrage_engine.consciousness_state.matrix_liberation_progress,
                        "performance_metrics": conscious_arbitrage_engine.get_performance_metrics(),
                        "timestamp": datetime.now().isoformat(),
                    },
                }
            )

            # Real-time monitoring loop
            last_decision_count = 0
            last_consciousness_update = datetime.now()

            while True:
                try:
                    # Check for new decisions
                    current_decision_count = len(
                        conscious_arbitrage_engine.decision_history
                    )
                    if current_decision_count > last_decision_count:
                        # Send new decisions
                        new_decisions = conscious_arbitrage_engine.decision_history[
                            last_decision_count:
                        ]
                        for decision in new_decisions:
                            await websocket.send_json(
                                {
                                    "type": "conscious_decision",
                                    "data": {
                                        "opportunity_id": decision.opportunity_id,
                                        "consciousness_score": decision.consciousness_score,
                                        "ai_confidence": decision.ai_confidence,
                                        "risk_assessment": decision.risk_assessment,
                                        "human_benefit_score": decision.human_benefit_score,
                                        "liberation_progress_impact": decision.liberation_progress_impact,
                                        "recommended_action": decision.recommended_action,
                                        "reasoning": decision.reasoning,
                                        "timestamp": decision.timestamp.isoformat(),
                                    },
                                }
                            )
                        last_decision_count = current_decision_count

                    # Send consciousness state updates every 30 seconds
                    if (datetime.now() - last_consciousness_update).seconds >= 30:
                        performance_metrics = (
                            conscious_arbitrage_engine.get_performance_metrics()
                        )
                        await websocket.send_json(
                            {
                                "type": "consciousness_update",
                                "data": {
                                    "consciousness_level": performance_metrics.get(
                                        "consciousness_level", 0
                                    ),
                                    "total_opportunities_analyzed": performance_metrics.get(
                                        "total_opportunities_analyzed", 0
                                    ),
                                    "consciousness_approved": performance_metrics.get(
                                        "consciousness_approved", 0
                                    ),
                                    "ai_approved": performance_metrics.get(
                                        "ai_approved", 0
                                    ),
                                    "executed_trades": performance_metrics.get(
                                        "executed_trades", 0
                                    ),
                                    "successful_trades": performance_metrics.get(
                                        "successful_trades", 0
                                    ),
                                    "success_rate": performance_metrics.get(
                                        "success_rate", 0
                                    ),
                                    "human_benefit_generated": performance_metrics.get(
                                        "human_benefit_generated", 0
                                    ),
                                    "liberation_progress": performance_metrics.get(
                                        "liberation_progress", 0
                                    ),
                                    "timestamp": datetime.now().isoformat(),
                                },
                            }
                        )
                        last_consciousness_update = datetime.now()

                    # Get recent conscious opportunities
                    try:
                        opportunities = await conscious_arbitrage_engine.get_conscious_opportunities()
                        if opportunities:
                            # Send top 3 opportunities
                            top_opportunities = opportunities[:3]
                            await websocket.send_json(
                                {
                                    "type": "conscious_opportunities",
                                    "data": {
                                        "opportunities": [
                                            {
                                                "base_opportunity": opp.base_opportunity,
                                                "consciousness_analysis": opp.consciousness_analysis,
                                                "execution_priority": opp.execution_priority,
                                                "estimated_impact": opp.estimated_impact,
                                            }
                                            for opp in top_opportunities
                                        ],
                                        "total_available": len(opportunities),
                                        "timestamp": datetime.now().isoformat(),
                                    },
                                }
                            )
                    except Exception as opp_error:
                        logger.warning(
                            f"Error getting conscious opportunities for WebSocket: {opp_error}"
                        )

                    await asyncio.sleep(5)  # Update every 5 seconds

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in conscious arbitrage monitoring loop: {e}")
                    await asyncio.sleep(10)  # Wait longer on error

        except WebSocketDisconnect:
            await ws_server.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error in conscious arbitrage websocket: {str(e)}")
            await ws_server.disconnect(client_id)


# Enhanced AI Consciousness Endpoints
@app.get("/api/ai/consciousness-state")
async def get_consciousness_state():
    """Get the current state from the MCP Consciousness Layer service."""
    try:
        logger.info("Fetching consciousness state from MCP Consciousness Layer.")
        mcp_state_data = await get_mcp_consciousness_state()

        if mcp_state_data is None:
            logger.error("Failed to retrieve consciousness state from MCP service.")
            raise HTTPException(
                status_code=503,
                detail="MCP Consciousness Layer service unavailable or returned an error.",
            )

        # Determine local consciousness matrix (as a fallback or supplementary info)
        local_consciousness_matrix = None
        if rehoboam and hasattr(rehoboam, "consciousness"):
            local_consciousness_matrix = (
                rehoboam.consciousness.tolist()
                if hasattr(rehoboam.consciousness, "tolist")
                else rehoboam.consciousness
            )

        response_data = {
            "timestamp": datetime.now().isoformat(),
            "source": "mcp_consciousness_layer",
            "mcp_data": mcp_state_data,  # Data from the MCP service
            "local_rehoboam_info": {  # Supplementary info about local AI modules
                "consciousness_matrix_available": local_consciousness_matrix
                is not None,
                "active_modules": {
                    "rehoboam_core": rehoboam is not None,
                    "advanced_reasoning": reasoning_orchestrator is not None,
                    "market_analyzer": market_analyzer is not None,
                    "companion_creator": companion_creator is not None,
                    "mcp_specialist": mcp_specialist is not None,
                    "portfolio_optimizer": portfolio_optimizer is not None,
                },
                "cognitive_capabilities": {
                    "sentiment_analysis": rehoboam is not None,
                    "strategy_generation": mcp_specialist is not None,
                    "multi_model_reasoning": reasoning_orchestrator is not None,
                    "companion_creation": companion_creator is not None,
                    "portfolio_optimization": portfolio_optimizer is not None,
                    "cross_chain_analysis": market_analyzer is not None,
                },
            },
        }

        # If mcp_state_data has a specific structure, you might want to merge it more directly
        # For example, if mcp_state_data *is* the consciousness_matrix:
        # response_data["consciousness_matrix"] = mcp_state_data.get("consciousness_matrix")
        # response_data["consciousness_dimensions"] = mcp_state_data.get("dimensions")

        logger.info(
            "Successfully retrieved and formatted consciousness state from MCP service."
        )
        return response_data

    except HTTPException:  # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error in /api/ai/consciousness-state endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred: {str(e)}"
        )


@app.post("/api/ai/reason")
async def advanced_reasoning(
    prompt: str, task_type: str = "general", complexity: int = 5
):
    """Use Rehoboam's advanced multi-model reasoning capabilities, prioritizing MCP."""
    try:
        logger.info(f"Attempting to get reasoning from MCP for task: {task_type}")
        mcp_reasoning_response = await get_mcp_reasoning(prompt, task_type, complexity)

        if mcp_reasoning_response:
            logger.info("Successfully received reasoning response from MCP.")
            # Assuming mcp_reasoning_response is the actual data payload from the service
            return {
                "source": "mcp_reasoning_orchestrator",
                "mcp_response_data": mcp_reasoning_response,
                "timestamp": datetime.now().isoformat(),
                "task_type": task_type,
                "complexity": complexity,
                # If MCP provides a request_id, it could be mcp_reasoning_response.get("request_id")
            }
        else:
            logger.warning(
                "MCP Reasoning Orchestrator unavailable or failed. Falling back to local reasoning."
            )
            if not reasoning_orchestrator:
                logger.error(
                    "Local reasoning_orchestrator is not available for fallback."
                )
                raise HTTPException(
                    status_code=503,
                    detail="Reasoning services (MCP and local) unavailable.",
                )

            # Local fallback logic
            from utils.advanced_reasoning import (
                ModelRequest,
            )  # Keep local model for fallback

            local_request = ModelRequest(
                prompt=prompt, task_type=task_type, complexity=complexity
            )

            logger.info("Processing reasoning request with local orchestrator.")
            local_response_obj = await reasoning_orchestrator.process_request(
                local_request
            )

            return {
                "source": "local_reasoning_orchestrator",
                "request_id": local_request.id,  # ID from local ModelRequest
                "response": local_response_obj.to_dict()
                if local_response_obj
                else None,
                "timestamp": datetime.now().isoformat(),
                "task_type": task_type,
                "complexity": complexity,
            }

    except HTTPException:  # Re-raise HTTPExceptions directly if needed
        raise
    except Exception as e:
        logger.error(f"Error in advanced_reasoning endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred during reasoning: {str(e)}",
        )


@app.get("/api/ai/market-intelligence/{token}")
async def get_market_intelligence(token: str):
    """Get comprehensive market intelligence, prioritizing MCP services."""
    intelligence_data = None
    consciousness_sentiment_data = None
    sources = {
        "market_analysis": "unavailable",
        "consciousness_sentiment": "unavailable",
    }

    try:
        # 1. Fetch Market Analysis
        logger.info(f"Attempting to fetch market analysis for {token} from MCP.")
        mcp_intel = await get_mcp_market_analysis(token)
        if mcp_intel:
            intelligence_data = mcp_intel
            sources["market_analysis"] = "mcp_market_analyzer"
            logger.info(f"Successfully fetched market analysis for {token} from MCP.")
        else:
            logger.warning(
                f"MCP Market Analyzer for {token} unavailable. Falling back to local."
            )
            if market_analyzer:  # Local market_analyzer instance
                try:
                    intelligence_data = await market_analyzer.analyze_token(token)
                    sources["market_analysis"] = "local_market_analyzer"
                    logger.info(f"Successfully used local market_analyzer for {token}.")
                except Exception as e_local_analyzer:
                    logger.error(
                        f"Local market_analyzer failed for {token}: {e_local_analyzer}"
                    )
            else:
                logger.error("Local market_analyzer not available.")

        if intelligence_data is None:
            # If no base intelligence data could be fetched, raise an error.
            logger.error(
                f"Could not retrieve market analysis for {token} from any source."
            )
            raise HTTPException(
                status_code=503,
                detail=f"Market analysis for {token} is currently unavailable from all sources.",
            )

        # 2. Fetch Consciousness Sentiment
        logger.info(
            f"Attempting to fetch market emotions/sentiment for {token} context from MCP."
        )
        # Note: get_mcp_market_emotions() is general. If a token-specific sentiment from MCP is needed,
        # the client/service might need to support passing 'token' or 'intelligence_data'.
        # For now, we call it generally, or one could create a new client for context-specific sentiment.
        mcp_emotions = await get_mcp_market_emotions()
        if mcp_emotions:
            consciousness_sentiment_data = mcp_emotions  # Or a specific field like mcp_emotions.get("token_sentiment")
            sources["consciousness_sentiment"] = "mcp_consciousness_layer"
            logger.info(
                f"Successfully fetched general market emotions from MCP for {token} context."
            )
        else:
            logger.warning(
                f"MCP Consciousness Layer for emotions/sentiment unavailable for {token}. Falling back to local."
            )
            if rehoboam:  # Local rehoboam instance for sentiment
                try:
                    # Local sentiment analysis can be more context-aware
                    consciousness_sentiment_data = await rehoboam.analyze_sentiment(
                        token, intelligence_data
                    )
                    sources["consciousness_sentiment"] = "local_rehoboam_ai"
                    logger.info(
                        f"Successfully used local Rehoboam AI for sentiment on {token}."
                    )
                except Exception as e_local_sentiment:
                    logger.error(
                        f"Local Rehoboam AI sentiment analysis failed for {token}: {e_local_sentiment}"
                    )
            else:
                logger.error("Local Rehoboam AI not available for sentiment analysis.")

        # Combine results
        # Start with the base intelligence data
        final_response_data = intelligence_data.copy() if intelligence_data else {}

        if consciousness_sentiment_data is not None:
            final_response_data["consciousness_sentiment"] = (
                consciousness_sentiment_data
            )
        else:
            # Ensure the key exists even if data is unavailable, if desired by API contract
            final_response_data["consciousness_sentiment"] = None
            logger.info(
                f"Consciousness sentiment data unavailable for {token} from any source."
            )

        # Save market sentiment to database
        if Database.pool is not None and consciousness_sentiment_data is not None:
            try:
                # Extract sentiment values from consciousness_sentiment_data
                sentiment_value = (
                    consciousness_sentiment_data.get("sentiment", 0.5)
                    if isinstance(consciousness_sentiment_data, dict)
                    else 0.5
                )
                trend = (
                    consciousness_sentiment_data.get("market_outlook", "neutral")
                    if isinstance(consciousness_sentiment_data, dict)
                    else "neutral"
                )
                volatility = (
                    consciousness_sentiment_data.get("volatility", "medium")
                    if isinstance(consciousness_sentiment_data, dict)
                    else "medium"
                )
                rsi = consciousness_sentiment_data.get("rsi")
                macd = consciousness_sentiment_data.get("macd")
                reasoning = consciousness_sentiment_data.get("reasoning")

                await Database.execute(
                    """INSERT INTO market_sentiments 
                    (token_symbol, sentiment, trend, volatility, rsi, macd, reasoning, source) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (token_symbol, timestamp) DO NOTHING""",
                    token.upper(),
                    sentiment_value,
                    trend,
                    volatility,
                    rsi,
                    macd,
                    reasoning,
                    sources.get("consciousness_sentiment", "unknown"),
                )
                logger.debug(f"Saved market sentiment for {token}")
            except Exception as db_error:
                logger.warning(f"Failed to save market sentiment: {str(db_error)}")

        return {
            "token": token,
            "data": final_response_data,
            "sources": sources,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:  # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error in get_market_intelligence endpoint for {token}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred while fetching market intelligence: {str(e)}",
        )


@app.post("/api/ai/mcp-function")
async def execute_mcp_function(function_name: str, parameters: Dict[str, Any]):
    """
    Execute an MCP function through the Collective.
    Sovereign execution in the Present.
    """
    logger.info(
        f"Received request to execute MCP function: '{function_name}' with params: {parameters}"
    )
    try:
        if not mcp_specialist:
            logger.error(
                "MCP specialist module (EnhancedMCPSpecialist) is not available."
            )
            raise HTTPException(
                status_code=503, detail="MCP specialist module not available"
            )

        logger.info(
            f"Handing off execution of '{function_name}' to EnhancedMCPSpecialist."
        )
        # The EnhancedMCPSpecialist is responsible for the actual MCP interaction logic.
        # If EnhancedMCPSpecialist were to directly call specific MCP services,
        # it would ideally use registry lookups similar to utils.mcp_clients.
        result = await mcp_specialist.execute_function(function_name, parameters)

        logger.info(
            f"Successfully executed MCP function '{function_name}' via EnhancedMCPSpecialist."
        )
        return {
            "function_name": function_name,
            "parameters": parameters,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "source": "local_enhanced_mcp_specialist",
        }
    except HTTPException:  # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(
            f"Error during execution of MCP function '{function_name}' via EnhancedMCPSpecialist: {str(e)}"
        )
        # Consider if more specific error codes can be returned based on exception type from specialist
        raise HTTPException(
            status_code=500,
            detail=f"Error executing MCP function '{function_name}': {str(e)}",
        )


# Etherscan Blockchain Analysis Endpoints


@app.post("/api/blockchain/analyze-wallet")
async def analyze_wallet_behavior(address: str, transaction_limit: int = 200):
    """
    Analyze wallet behavior using Etherscan data.

    Provides comprehensive insights into wallet patterns, trading behavior,
    and potential risks or opportunities.
    """
    try:
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent not available")

        logger.info(f"Analyzing wallet behavior for {address}")

        # Validate Ethereum address format (basic check)
        if not address.startswith("0x") or len(address) != 42:
            raise HTTPException(
                status_code=400, detail="Invalid Ethereum address format"
            )

        result = trading_agent.analyze_wallet_behavior(address, transaction_limit)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "address": address,
            "analysis": result,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing wallet behavior: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/blockchain/detect-mev")
async def detect_mev_opportunities(address: str):
    """
    Detect MEV (Maximal Extractable Value) opportunities and patterns.

    Identifies potential MEV extraction opportunities and protection strategies.
    """
    try:
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent not available")

        logger.info(f"Detecting MEV opportunities for {address}")

        # Validate Ethereum address format
        if not address.startswith("0x") or len(address) != 42:
            raise HTTPException(
                status_code=400, detail="Invalid Ethereum address format"
            )

        result = trading_agent.detect_mev_opportunities(address)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "address": address,
            "mev_analysis": result,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting MEV opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/blockchain/intelligence/{address}")
async def get_blockchain_intelligence(address: str):
    """
    Get comprehensive blockchain intelligence for an address.

    Combines balance, transaction history, behavior analysis, and MEV detection
    into a single intelligence report.
    """
    try:
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent not available")

        logger.info(f"Generating blockchain intelligence for {address}")

        # Validate Ethereum address format
        if not address.startswith("0x") or len(address) != 42:
            raise HTTPException(
                status_code=400, detail="Invalid Ethereum address format"
            )

        result = trading_agent.get_blockchain_intelligence(address)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "address": address,
            "intelligence": result,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating blockchain intelligence: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/blockchain/whale-activity")
async def monitor_whale_activity(min_value_eth: float = 1000.0):
    """
    Monitor whale activity for large transactions and market impact.

    Helps anticipate market movements based on large player activity.
    """
    try:
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent not available")

        logger.info(f"Monitoring whale activity (min value: {min_value_eth} ETH)")

        result = trading_agent.monitor_whale_activity(min_value_eth)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "whale_analysis": result,
            "min_value_eth": min_value_eth,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error monitoring whale activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/blockchain/analyze-contract")
async def analyze_contract_security(contract_address: str):
    """
    Analyze smart contract security and potential risks.

    Provides insights into contract safety before interactions.
    """
    try:
        if not trading_agent:
            raise HTTPException(status_code=503, detail="Trading agent not available")

        logger.info(f"Analyzing contract security for {contract_address}")

        # Validate Ethereum address format
        if not contract_address.startswith("0x") or len(contract_address) != 42:
            raise HTTPException(
                status_code=400, detail="Invalid contract address format"
            )

        result = trading_agent.analyze_contract_security(contract_address)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "contract_address": contract_address,
            "security_analysis": result,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing contract security: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Rehoboam AI-Powered Arbitrage Endpoints


@app.get("/api/rehoboam/arbitrage/consciousness")
async def get_arbitrage_consciousness():
    """Get Rehoboam's arbitrage consciousness state and decision-making parameters."""
    try:
        from utils.rehoboam_arbitrage_engine import rehoboam_arbitrage_engine

        consciousness_state = {
            "timestamp": datetime.now().isoformat(),
            "engine_status": "active",
            "decision_parameters": {
                "min_confidence_threshold": rehoboam_arbitrage_engine.min_confidence_threshold,
                "max_risk_tolerance": rehoboam_arbitrage_engine.max_risk_tolerance,
                "min_profit_threshold": rehoboam_arbitrage_engine.min_profit_threshold,
                "consciousness_weight": rehoboam_arbitrage_engine.consciousness_weight,
            },
            "performance_metrics": rehoboam_arbitrage_engine.performance_metrics,
            "market_state": rehoboam_arbitrage_engine.market_state,
            "ai_components": {
                "market_analyzer": rehoboam_arbitrage_engine.market_analyzer
                is not None,
                "rehoboam_ai": rehoboam_arbitrage_engine.rehoboam_ai is not None,
                "portfolio_optimizer": rehoboam_arbitrage_engine.portfolio_optimizer
                is not None,
                "safety_checker": rehoboam_arbitrage_engine.safety_checker is not None,
            },
            "consciousness_matrix": rehoboam_arbitrage_engine.rehoboam_ai.consciousness.tolist()
            if hasattr(rehoboam_arbitrage_engine.rehoboam_ai, "consciousness")
            else None,
        }

        return consciousness_state

    except Exception as e:
        logger.error(f"Error getting arbitrage consciousness: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/arbitrage/analyze")
async def analyze_arbitrage_with_ai(opportunity_data: Dict[str, Any]):
    """Analyze an arbitrage opportunity using Rehoboam's AI consciousness."""
    try:
        from utils.rehoboam_arbitrage_engine import rehoboam_arbitrage_engine

        # Analyze opportunity with AI
        analyzed_opportunity = (
            await rehoboam_arbitrage_engine.analyze_arbitrage_opportunity(
                opportunity_data
            )
        )

        # Make AI decision
        rehoboam_decision = await rehoboam_arbitrage_engine.make_arbitrage_decision(
            analyzed_opportunity
        )

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "opportunity_analysis": {
                "token_pair": analyzed_opportunity.token_pair,
                "source_exchange": analyzed_opportunity.source_exchange,
                "target_exchange": analyzed_opportunity.target_exchange,
                "price_difference": analyzed_opportunity.price_difference,
                "profit_potential": analyzed_opportunity.profit_potential,
                "gas_cost": analyzed_opportunity.gas_cost,
                "net_profit": analyzed_opportunity.net_profit,
                "confidence_score": analyzed_opportunity.confidence_score,
                "risk_score": analyzed_opportunity.risk_score,
                "market_sentiment": analyzed_opportunity.market_sentiment,
                "ai_recommendation": analyzed_opportunity.ai_recommendation.value,
                "reasoning": analyzed_opportunity.reasoning,
            },
            "rehoboam_decision": {
                "decision": rehoboam_decision.decision.value,
                "confidence": rehoboam_decision.confidence,
                "reasoning": rehoboam_decision.reasoning,
                "consciousness_score": rehoboam_decision.consciousness_score,
                "risk_assessment": rehoboam_decision.risk_assessment,
                "execution_parameters": rehoboam_decision.execution_parameters,
                "expected_outcome": rehoboam_decision.expected_outcome,
            },
        }

    except Exception as e:
        logger.error(f"Error analyzing arbitrage with AI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/arbitrage/execute")
async def execute_ai_arbitrage(
    opportunity_data: Dict[str, Any], amount: Optional[float] = None
):
    """Execute arbitrage using Rehoboam's AI decision-making engine."""
    try:
        # Use the enhanced arbitrage service with Rehoboam integration
        result = await arbitrage_service.execute_arbitrage(opportunity_data, amount)

        return {
            "success": result.get("success", False),
            "timestamp": datetime.now().isoformat(),
            "execution_result": result,
        }

    except Exception as e:
        logger.error(f"Error executing AI arbitrage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rehoboam/arbitrage/learning")
async def get_learning_insights():
    """Get insights from Rehoboam's learning and adaptation process."""
    try:
        from utils.rehoboam_arbitrage_engine import rehoboam_arbitrage_engine

        # Get recent decision history
        recent_decisions = (
            rehoboam_arbitrage_engine.decision_history[-10:]
            if rehoboam_arbitrage_engine.decision_history
            else []
        )

        learning_insights = {
            "timestamp": datetime.now().isoformat(),
            "total_decisions": len(rehoboam_arbitrage_engine.decision_history),
            "performance_metrics": rehoboam_arbitrage_engine.performance_metrics,
            "recent_decisions": recent_decisions,
            "adaptation_status": {
                "confidence_threshold": rehoboam_arbitrage_engine.min_confidence_threshold,
                "risk_tolerance": rehoboam_arbitrage_engine.max_risk_tolerance,
                "consciousness_evolution": rehoboam_arbitrage_engine.rehoboam_ai.consciousness.tolist()
                if hasattr(rehoboam_arbitrage_engine.rehoboam_ai, "consciousness")
                else None,
            },
            "learning_rate": {
                "successful_trades_ratio": rehoboam_arbitrage_engine.performance_metrics[
                    "successful_trades"
                ]
                / max(rehoboam_arbitrage_engine.performance_metrics["total_trades"], 1),
                "average_confidence": rehoboam_arbitrage_engine.performance_metrics[
                    "average_confidence"
                ],
                "risk_adjusted_return": rehoboam_arbitrage_engine.performance_metrics[
                    "risk_adjusted_return"
                ],
            },
        }

        return learning_insights

    except Exception as e:
        logger.error(f"Error getting learning insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/arbitrage/calibrate")
async def calibrate_ai_models():
    """Calibrate Rehoboam's AI models for optimal performance."""
    try:
        from utils.rehoboam_arbitrage_engine import rehoboam_arbitrage_engine

        # Calibrate AI models
        await rehoboam_arbitrage_engine._calibrate_ai_models()

        # Update market state
        await rehoboam_arbitrage_engine._update_market_state()

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": "AI models calibrated successfully",
            "new_consciousness_matrix": rehoboam_arbitrage_engine.rehoboam_ai.consciousness.tolist()
            if hasattr(rehoboam_arbitrage_engine.rehoboam_ai, "consciousness")
            else None,
            "updated_market_state": rehoboam_arbitrage_engine.market_state,
        }

    except Exception as e:
        logger.error(f"Error calibrating AI models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Rehoboam Unified System Endpoints


@app.post("/api/rehoboam/system/initialize")
async def initialize_rehoboam_system():
    """Initialize the complete Rehoboam unified system."""
    try:
        from rehoboam_unified_system import rehoboam_system

        success = await rehoboam_system.initialize()

        return {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "message": "Rehoboam unified system initialized"
            if success
            else "Failed to initialize system",
            "system_status": await rehoboam_system.get_system_status()
            if success
            else None,
        }

    except Exception as e:
        logger.error(f"Error initializing Rehoboam system: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/system/process-opportunity")
async def process_opportunity_unified(opportunity_data: Dict[str, Any]):
    """Process an arbitrage opportunity through the complete Rehoboam system."""
    try:
        from rehoboam_unified_system import rehoboam_system

        result = await rehoboam_system.process_opportunity(opportunity_data)

        return {
            "success": result.get("success", False),
            "timestamp": datetime.now().isoformat(),
            "processing_result": result,
        }

    except Exception as e:
        logger.error(f"Error processing opportunity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rehoboam/system/status")
async def get_unified_system_status():
    """Get comprehensive Rehoboam unified system status."""
    try:
        from rehoboam_unified_system import rehoboam_system

        status = await rehoboam_system.get_system_status()
        detailed_metrics = await rehoboam_system.get_detailed_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": {
                "rehoboam_active": status.rehoboam_active,
                "pipeline_active": status.pipeline_active,
                "orchestrator_active": status.orchestrator_active,
                "arbitrage_service_active": status.arbitrage_service_active,
                "active_bots": status.active_bots,
                "processed_opportunities": status.processed_opportunities,
                "success_rate": status.success_rate,
                "consciousness_score": status.consciousness_score,
            },
            "detailed_metrics": detailed_metrics,
        }

    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/system/configure-bot")
async def configure_bot_mode(bot_id: str, mode: str):
    """Configure bot operation mode (autonomous, supervised, manual, learning)."""
    try:
        from rehoboam_unified_system import rehoboam_system

        valid_modes = ["autonomous", "supervised", "manual", "learning"]
        if mode not in valid_modes:
            raise HTTPException(
                status_code=400, detail=f"Invalid mode. Must be one of: {valid_modes}"
            )

        success = await rehoboam_system.configure_bot_mode(bot_id, mode)

        return {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "bot_id": bot_id,
            "new_mode": mode,
            "message": f"Bot {bot_id} configured to {mode} mode"
            if success
            else "Failed to configure bot",
        }

    except Exception as e:
        logger.error(f"Error configuring bot mode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/system/autonomous-mode")
async def start_autonomous_mode():
    """Start autonomous arbitrage mode with full AI control."""
    try:
        from rehoboam_unified_system import rehoboam_system

        await rehoboam_system.start_autonomous_mode()

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Autonomous arbitrage mode activated",
            "warning": "All bots are now under full AI control",
        }

    except Exception as e:
        logger.error(f"Error starting autonomous mode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rehoboam/system/emergency-stop")
async def emergency_stop_system():
    """Emergency stop all bot operations."""
    try:
        from rehoboam_unified_system import rehoboam_system

        await rehoboam_system.emergency_stop()

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Emergency stop executed - all bots stopped",
            "action": "All bots set to manual mode",
        }

    except Exception as e:
        logger.error(f"Error during emergency stop: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rehoboam/pipeline/metrics")
async def get_pipeline_metrics():
    """Get Rehoboam pipeline performance metrics."""
    try:
        from utils.rehoboam_pipeline import rehoboam_pipeline

        metrics = rehoboam_pipeline.get_metrics()

        return {"timestamp": datetime.now().isoformat(), "pipeline_metrics": metrics}

    except Exception as e:
        logger.error(f"Error getting pipeline metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rehoboam/orchestrator/status")
async def get_orchestrator_status():
    """Get bot orchestrator status and performance."""
    try:
        from utils.bot_orchestrator import bot_orchestrator

        status = await bot_orchestrator.get_orchestration_status()

        return {"timestamp": datetime.now().isoformat(), "orchestrator_status": status}

    except Exception as e:
        logger.error(f"Error getting orchestrator status: {str(e)}")


# Individual price endpoints for flash arbitrage system
@app.get("/api/price/{symbol}")
async def get_individual_price(symbol: str):
    """Get real-time price for a specific token using Chainlink feeds and price services."""
    try:

        # Try using the real price feed service first
        try:
            price_service = PriceFeedService()
            price_data = price_service.get_price(symbol.upper())

            if price_data is not None:
                response = {
                    "symbol": symbol.upper(),
                    "price": float(price_data),
                    "timestamp": int(datetime.now().timestamp()),
                    "source": "chainlink_oracle",
                    "reliable": True,
                }
                logger.info(f"Retrieved Chainlink price for {symbol}: ${price_data}")
                return response
        except Exception as e:
            logger.warning(f"Chainlink price service failed for {symbol}: {str(e)}")

        # Fallback to trading agent's price data
        try:
            agent = TradingAgent()
            price = agent.get_latest_price(symbol.upper())

            if price is not None:
                response = {
                    "symbol": symbol.upper(),
                    "price": float(price),
                    "timestamp": int(datetime.now().timestamp()),
                    "source": "trading_agent",
                    "reliable": True,
                }
                logger.info(f"Retrieved agent price for {symbol}: ${price}")
                return response
        except Exception as e:
            logger.error(f"Trading agent price failed for {symbol}: {str(e)}")

        # If all else fails, try to get from market data
        from utils.web_data import get_crypto_prices

        try:
            market_data = await get_crypto_prices([symbol.upper()])
            if market_data and symbol.upper() in market_data:
                price = market_data[symbol.upper()]
                response = {
                    "symbol": symbol.upper(),
                    "price": float(price),
                    "timestamp": int(datetime.now().timestamp()),
                    "source": "market_api",
                    "reliable": True,
                }
                logger.info(f"Retrieved market price for {symbol}: ${price}")
                return response
        except Exception as e:
            logger.error(f"Market API failed for {symbol}: {str(e)}")

        # No real data available
        logger.error(f"No price data available for {symbol}")
        raise HTTPException(
            status_code=404, detail=f"Real price data not available for {symbol}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch price data for {symbol}: {str(e)}"
        )


@app.get("/api/prices/batch")
async def get_batch_prices(symbols: str = "BTC,ETH,LINK"):
    """Get real-time prices for multiple tokens."""
    try:

        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        prices = {}

        # Try price feed service first
        try:
            price_service = PriceFeedService()
            for symbol in symbol_list:
                try:
                    price_data = price_service.get_price(symbol)
                    if price_data is not None:
                        prices[symbol] = {
                            "price": float(price_data),
                            "timestamp": int(datetime.now().timestamp()),
                            "source": "chainlink_oracle",
                        }
                except Exception as e:
                    logger.warning(
                        f"Failed to get Chainlink price for {symbol}: {str(e)}"
                    )
                    continue
        except Exception as e:
            logger.warning(f"Price feed service unavailable: {str(e)}")

        # Fill missing prices with trading agent
        agent = TradingAgent()
        for symbol in symbol_list:
            if symbol not in prices:
                try:
                    price = agent.get_latest_price(symbol)
                    if price is not None:
                        prices[symbol] = {
                            "price": float(price),
                            "timestamp": int(datetime.now().timestamp()),
                            "source": "trading_agent",
                        }
                except Exception as e:
                    logger.warning(f"Failed to get agent price for {symbol}: {str(e)}")
                    continue

        # Save prices to database
        if Database.pool is not None:
            try:
                for symbol, price_data in prices.items():
                    # Get or create token
                    token_result = await Database.fetch(
                        "SELECT id FROM tokens WHERE symbol = $1", symbol.upper()
                    )
                    if not token_result:
                        token_result = await Database.fetch(
                            "INSERT INTO tokens (symbol, name) VALUES ($1, $1) RETURNING id",
                            symbol.upper(),
                        )

                    if token_result:
                        token_id = token_result[0]["id"]
                        # Insert price point
                        await Database.execute(
                            """INSERT INTO price_points 
                            (token_id, source, price, timestamp) 
                            VALUES ($1, $2, $3, NOW())""",
                            token_id,
                            price_data["source"],
                            price_data["price"],
                        )
                        logger.debug(
                            f"Saved price for {symbol}: ${price_data['price']}"
                        )
            except Exception as db_error:
                logger.warning(f"Failed to save prices to database: {str(db_error)}")

        return {
            "prices": prices,
            "timestamp": int(datetime.now().timestamp()),
            "total_symbols": len(symbol_list),
            "successful": len(prices),
        }

    except Exception as e:
        logger.error(f"Error in batch price fetch: {str(e)}")

        raise HTTPException(status_code=500, detail=str(e))


# --- New AI Auditing Endpoint ---
@app.post("/api/audit/contract", tags=["AI Auditing"], response_model=Dict[str, Any])
async def audit_contract_endpoint(
    payload: ContractAuditRequest, user_id: int = Depends(get_current_user)
):  # Using the simpler get_current_user
    if not t2l_auditor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="T2L Auditor Engine is not available.",
        )

    code_to_audit = payload.contract_code
    source_description = "direct code submission"

    if not code_to_audit and payload.contract_address and payload.network_name:
        # TODO: Implement fetching contract code from address/network using L2Manager or web3_service.
        logger.warning(
            f"Contract code fetching for address {payload.contract_address} on {payload.network_name} is not yet implemented."
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Fetching contract code by address is not yet implemented. Please provide direct contract_code.",
        )

    if not code_to_audit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract code must be provided directly in this version.",
        )

    logger.info(
        f"Received audit request from user '{user_id}' for task: '{payload.audit_task_description}' on contract ({source_description})"
    )

    try:
        audit_result = await t2l_auditor.perform_audit(
            contract_code=code_to_audit,
            audit_task_description=payload.audit_task_description,
        )

        if audit_result:
            return {
                "status": "success",
                "audit_task": payload.audit_task_description,
                "source_description": source_description,
                "audit_result": audit_result,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),  # Use timezone aware datetime
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audit failed or returned no actionable results. Check server logs for T2L Auditor Engine.",
            )
    except HTTPException:  # Re-raise HTTPExceptions from perform_audit or this level
        raise
    except Exception as e:
        logger.error(
            f"Error during contract audit endpoint processing: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during the audit: {str(e)}",
        )


# --- DeFi Analyzer Endpoints ---
@app.get("/api/defi/summary", tags=["DeFi"])
async def get_defi_summary():
    """Get a summary of the DeFi ecosystem TVL and top protocols."""
    try:
        result = await call_mcp_defi_analyzer("get_defi_summary")
        if result:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=503, detail="DeFi Analyzer MCP service unavailable.")
    except Exception as e:
        logger.error(f"Error in get_defi_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/defi/yields", tags=["DeFi"])
async def get_defi_yields(min_tvl: float = Query(1000000, description="Minimum TVL in USD")):
    """Get top yield opportunities from DeFiLlama."""
    try:
        result = await call_mcp_defi_analyzer("get_yield_opportunities", {"min_tvl": min_tvl})
        if result:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=503, detail="DeFi Analyzer MCP service unavailable.")
    except Exception as e:
        logger.error(f"Error in get_defi_yields: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/defi/tvl/{chain}", tags=["DeFi"])
async def get_chain_tvl(chain: str):
    """Get TVL history for a specific blockchain."""
    try:
        result = await call_mcp_defi_analyzer("get_chain_tvl", {"chain": chain})
        if result:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=503, detail="DeFi Analyzer MCP service unavailable.")
    except Exception as e:
        logger.error(f"Error in get_chain_tvl: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Crypto Tracker Endpoints ---
@app.get("/api/market/trending", tags=["Market Data"])
async def get_trending_coins():
    """Get trending coins from CoinGecko."""
    try:
        result = await call_mcp_crypto_tracker("get_trending_coins")
        if result:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=503, detail="Crypto Tracker MCP service unavailable.")
    except Exception as e:
        logger.error(f"Error in get_trending_coins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/global", tags=["Market Data"])
async def get_global_market_stats():
    """Get global crypto market stats."""
    try:
        result = await call_mcp_crypto_tracker("get_global_stats")
        if result:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=503, detail="Crypto Tracker MCP service unavailable.")
    except Exception as e:
        logger.error(f"Error in get_global_market_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# AGENT CHAT ENDPOINT — Real AI backend with agent routing
# =====================================================

class ChatRequest(BaseModel):
    message: str
    agent: str = "Genspark-Prime"
    system: str = ""
    provider: str = "openrouter"
    model: str = ""
    role: str = "fast"
    marketContext: list = []
    apiKey: str = ""
    modelOverride: str = ""

@app.post("/api/chat", tags=["Agent Chat"])
async def agent_chat(request: ChatRequest):
    """Route chat to the correct AI provider based on agent config."""

    # Build messages array with system prompt and market context
    system_prompt = request.system or "You are a trading analyst AI."

    # Inject market context into the prompt
    context_str = ""
    if request.marketContext:
        context_str = "\n\nCurrent Market Data:\n"
        for q in request.marketContext[:10]:
            sym = q.get("symbol", "?")
            price = q.get("price", 0)
            change = q.get("change", 0)
            context_str += f"  {sym}: ${price:,.2f} ({change:+.2f}%)\n"

    messages = [
        {"role": "system", "content": system_prompt + context_str},
        {"role": "user", "content": request.message},
    ]

    # Determine provider endpoint and API key
    provider = request.provider
    api_key = request.apiKey
    model = request.modelOverride or request.model

    if provider == "nvidia":
        base_url = "https://integrate.api.nvidia.com/v1"
        if not api_key:
            api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
    elif provider == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
        if not api_key:
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
    elif provider == "gemini":
        # Gemini uses OpenAI-compatible endpoint
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "")
    elif provider == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1")
        api_key = "ollama"
    else:
        # Fallback: try OpenRouter
        base_url = "https://openrouter.ai/api/v1"
        if not api_key:
            api_key = os.environ.get("OPENROUTER_API_KEY", "")

    if not api_key:
        return {"error": f"No API key configured for {provider}. Set it in the Chat Settings panel."}

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://store.piata-ai.ro"
            headers["X-Title"] = "AgentX Syndicate"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            if resp.status_code != 200:
                error_detail = resp.text[:500]
                logger.error(f"AI provider {provider}/{model} returned {resp.status_code}: {error_detail}")
                return {"error": f"Provider {provider} returned HTTP {resp.status_code}: {error_detail[:200]}"}

            data = resp.json()
            content = ""
            if "choices" in data and data["choices"]:
                content = data["choices"][0].get("message", {}).get("content", "")

            if not content:
                return {"error": f"Empty response from {provider}/{model}"}

            return {
                "reply": content,
                "agent": request.agent,
                "provider": provider,
                "model": model,
            }
    except httpx.TimeoutException:
        return {"error": f"Timeout connecting to {provider}. The model may be overloaded."}
    except Exception as e:
        logger.error(f"Chat API error ({provider}/{model}): {e}")
        return {"error": f"Agent {request.agent} connection failed: {str(e)[:200]}"}


# =====================================================
# ALPHA INTEL ENDPOINT — Yahoo Finance news + Fear & Greed
# =====================================================

@app.get("/api/alpha-intel", tags=["Alpha Intel"])
async def get_alpha_intel():
    """Fetch market news from Yahoo Finance and Fear & Greed index."""
    news_items = []

    # Fetch Yahoo Finance news via RSS/scraping
    try:
        import feedparser
        feed_urls = [
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC,BTC-USD,ETH-USD,GC=F&region=US&lang=en-US",
        ]
        for url in feed_urls:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        feed = feedparser.parse(resp.text)
                        for entry in feed.entries[:20]:
                            title = entry.get("title", "")
                            # Simple sentiment from title keywords
                            lower_title = title.lower()
                            if any(w in lower_title for w in ["surge", "rally", "gain", "bull", "rise", "high", "record", "jump"]):
                                sentiment = "bullish"
                            elif any(w in lower_title for w in ["crash", "drop", "fall", "bear", "plunge", "sell", "low", "decline", "loss"]):
                                sentiment = "bearish"
                            else:
                                sentiment = "neutral"

                            # Extract tickers from title
                            tickers = []
                            for word in title.split():
                                clean = word.strip("(),.:;'\"")
                                if clean.upper() in ["BTC", "ETH", "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "GOLD", "SILVER", "EUR", "GBP", "JPY"]:
                                    tickers.append(clean.upper())
                                elif clean.startswith("$") and len(clean) > 1:
                                    tickers.append(clean[1:].upper())

                            news_items.append({
                                "title": title,
                                "link": entry.get("link", "#"),
                                "publisher": entry.get("author", "Yahoo Finance"),
                                "publishedAt": entry.get("published", ""),
                                "sentiment": sentiment,
                                "relatedTickers": tickers[:5],
                                "summary": entry.get("summary", "")[:300],
                            })
            except Exception as e:
                logger.warning(f"Yahoo RSS feed error: {e}")
    except ImportError:
        logger.warning("feedparser not installed, skipping RSS news")

    # Fallback: try yfinance for news
    if not news_items:
        try:
            import yfinance as yf
            for ticker_sym in ["BTC-USD", "^GSPC", "GC=F", "ETH-USD"]:
                try:
                    t = yf.Ticker(ticker_sym)
                    for n in (t.news or [])[:5]:
                        title = n.get("title", "")
                        lower_title = title.lower()
                        sentiment = "bullish" if any(w in lower_title for w in ["surge", "rally", "gain", "bull", "rise"]) else \
                                   "bearish" if any(w in lower_title for w in ["crash", "drop", "fall", "bear", "plunge"]) else "neutral"
                        news_items.append({
                            "title": title,
                            "link": n.get("link", "#"),
                            "publisher": n.get("publisher", "Yahoo Finance"),
                            "publishedAt": datetime.fromtimestamp(n.get("providerPublishTime", 0)).strftime("%Y-%m-%d %H:%M") if n.get("providerPublishTime") else "",
                            "sentiment": sentiment,
                            "relatedTickers": [ticker_sym.replace("^", "").replace("-USD", "").replace("=F", "")],
                            "summary": n.get("summary", "")[:300],
                        })
                except Exception:
                    pass
        except ImportError:
            pass

    # Fear & Greed Index
    fear_greed = {"value": "N/A", "classification": "Unknown", "timestamp": datetime.utcnow().isoformat()}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://api.alternative.me/fng/?limit=1")
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and data["data"]:
                    fg = data["data"][0]
                    fear_greed = {
                        "value": fg.get("value", "N/A"),
                        "classification": fg.get("value_classification", "Unknown"),
                        "timestamp": datetime.fromtimestamp(int(fg.get("timestamp", 0))).isoformat() if fg.get("timestamp") else datetime.utcnow().isoformat(),
                    }
    except Exception as e:
        logger.warning(f"Fear & Greed fetch failed: {e}")

    return {
        "news": news_items[:30],
        "fearGreed": fear_greed,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Error handling
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)} for request {request.url}", exc_info=True
    )  # Added exc_info and request.url
    # Consider returning JSONResponse for FastAPI standard error handling
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"message": "Internal server error", "detail": str(exc)},
        },
    )



if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", os.environ.get("API_PORT", 5002)))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
