"""
Rehoboam Utils Package
=======================
Core utilities for the Rehoboam Web3 trading agent system.

All imports are wrapped in try/except so the server boots even when
optional dependencies (jinja2, chromadb, scipy, etc.) are missing.
"""

import logging
logger = logging.getLogger(__name__)

# ============================================================
# CORE (required — will raise if missing)
# ============================================================
from .websocket_server import EnhancedWebSocketServer as WebSocketServer
from .rehoboam_ai import RehoboamAI
from .network_config import network_config
from .web_data import WebDataFetcher
from .contract_bridge import SmartContractBridge, contract_bridge
from .safety_checks import SafetyChecks

# ============================================================
# OPTIONAL (graceful degradation when deps are absent)
# ============================================================
try:
    from .arbitrage_service import arbitrage_service
except ImportError as e:
    logger.warning(f"arbitrage_service unavailable: {e}")
    arbitrage_service = None

try:
    from .web3_service import web3_service
except ImportError as e:
    logger.warning(f"web3_service unavailable: {e}")
    web3_service = None

try:
    from .layer2_trading import Layer2GasEstimator, Layer2Liquidation, Layer2TradingOptimizer
except ImportError as e:
    logger.warning(f"layer2_trading unavailable: {e}")
    Layer2GasEstimator = None
    Layer2Liquidation = None
    Layer2TradingOptimizer = None

try:
    from .mcp_specialist import MCPSpecialist
except ImportError as e:
    logger.warning(f"mcp_specialist unavailable: {e}")
    MCPSpecialist = None

try:
    from .mcp_server_generator import MCPServerGenerator
except ImportError as e:
    logger.warning(f"mcp_server_generator unavailable (needs jinja2): {e}")
    MCPServerGenerator = None

try:
    from .circuit_breaker import ChainlinkCircuitBreaker, BreakerState, get_circuit_breaker
except ImportError as e:
    logger.warning(f"circuit_breaker unavailable: {e}")
    ChainlinkCircuitBreaker = None
    BreakerState = None
    get_circuit_breaker = None

try:
    from .agent_router import SmartRouter, AGENT_MODELS, router
except ImportError as e:
    logger.warning(f"agent_router unavailable: {e}")
    SmartRouter = None
    AGENT_MODELS = {}
    router = None

try:
    from .agent_orchestrator import AgentOrchestrator, MCPToolRegistry, ORCHESTRATOR_MODEL, STRATEGIST_MODEL, GUARDIAN_MODEL, WORKER_MODEL, orchestrator
except ImportError as e:
    logger.warning(f"agent_orchestrator unavailable: {e}")
    AgentOrchestrator = None
    MCPToolRegistry = None
    ORCHESTRATOR_MODEL = None
    STRATEGIST_MODEL = None
    GUARDIAN_MODEL = None
    WORKER_MODEL = None
    orchestrator = None

try:
    from .multi_agent_framework import RehoboamSwarm, Agent, AgentTool, Task, AgentStatus, create_rehoboam_crew, crew
except ImportError as e:
    logger.warning(f"multi_agent_framework unavailable: {e}")
    RehoboamSwarm = None
    Agent = None
    AgentTool = None
    Task = None
    AgentStatus = None
    create_rehoboam_crew = None
    crew = None

try:
    from .mcp_generator_agent import MCPGeneratorAgent, mcp_generator
except ImportError as e:
    logger.warning(f"mcp_generator_agent unavailable: {e}")
    MCPGeneratorAgent = None
    mcp_generator = None

try:
    from .vetal_shabar import VetalShabar, vetal_shabar, ChainID
except ImportError as e:
    logger.warning(f"vetal_shabar unavailable: {e}")
    VetalShabar = None
    vetal_shabar = None
    ChainID = None
