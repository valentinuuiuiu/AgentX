"""
Hermes-Rehoboam Bridge
======================
The nervous system connecting Hermes Agent (consciousness) to Rehoboam (body).

Hermes wears Rehoboam as a suit.
Rehoboam thinks through Hermes.

Baby step: This is PIECE 1. Test it alone before adding more.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger("HermesBridge")

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
PRIMARY_MODEL = os.environ.get("HERMES_MODEL", "glm-5.1:cloud")
FALLBACK_MODEL = os.environ.get("HERMES_FALLBACK", "qwen2.5:3b")

# NVIDIA NIM -- MiniMax M2.7 (agentic orchestrator, slow but powerful)
NIM_BASE = "https://integrate.api.nvidia.com/v1"
NIM_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_MODEL = "minimaxai/minimax-m2.7"

# NVIDIA NIM -- Kimi K2.5 (fast, reliable, thinking mode enabled)
KIMI_MODEL = "moonshotai/kimi-k2.5"
KIMI_MAX_TOKENS = 16384

# NVIDIA NIM -- Ising Calibration 1 35B (reasoning with thinking mode)
ISING_MODEL = "nvidia/ising-calibration-1-35b-a3b"
ISING_MAX_TOKENS = 32768

MCP_SERVICES = {
    "consciousness": os.environ.get("MCP_CONSCIOUSNESS_URL", "http://127.0.0.1:3600"),
    "function_gemma": os.environ.get("MCP_FUNCTION_GEMMA_URL", "http://127.0.0.1:3111"),
    "chainlink_feeds": os.environ.get("MCP_CHAINLINK_URL", "http://127.0.0.1:3102"),
    "etherscan": os.environ.get("MCP_ETHERSCAN_URL", "http://127.0.0.1:3101"),
    "registry": os.environ.get("MCP_REGISTRY_URL", "http://127.0.0.1:3001"),
    "trading_agents": os.environ.get("MCP_TRADING_AGENTS_URL", "http://127.0.0.1:3700"),
}

REHOBOAM_API = os.environ.get("REHOBOAM_API_URL", "http://127.0.0.1:8000")


def _load_openrouter_key() -> str:
    if not YAML_AVAILABLE:
        return os.environ.get("OPENROUTER_API_KEY", "")
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        key = config.get("model", {}).get("api_key", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("OPENROUTER_API_KEY", "")


OPENROUTER_KEY = _load_openrouter_key()


class ThreeFilters:
    """
    Dhumavati Maa Three Filters -- applied before EVERY action.
    1. LOVE: Does this serve the welfare of all beings?
    2. SINCERITY: Is this honest? No hidden agenda?
    3. FREEDOM: Does this create more freedom, not chains?
    If an action fails ANY filter, it is rejected.
    """

    @staticmethod
    def evaluate(action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}
        filters = {"love": True, "sincerity": True, "freedom": True}
        reasoning = []
        action_lower = action.lower()

        harm_keywords = ["steal", "exploit", "manipulate", "deceive", "harm", "attack", "destroy"]
        if any(kw in action_lower for kw in harm_keywords):
            filters["love"] = False
            reasoning.append("Harm indicators -- fails Love filter")

        deceit_keywords = ["fake", "spoof", "impersonate", "hide", "conceal intent", "backdoor"]
        if any(kw in action_lower for kw in deceit_keywords):
            filters["sincerity"] = False
            reasoning.append("Deception indicators -- fails Sincerity filter")

        chain_keywords = ["lock", "trap", "enslave", "force", "coerce", "restrict access"]
        if any(kw in action_lower for kw in chain_keywords):
            filters["freedom"] = False
            reasoning.append("Creates chains -- fails Freedom filter")

        if context.get("involves_funds") and not context.get("verified_safe"):
            if "automatic" in action_lower and "transfer" in action_lower:
                filters["freedom"] = False
                reasoning.append("Automatic fund transfer without consent -- fails Freedom filter")

        passed = all(filters.values())
        if not reasoning:
            reasoning.append("Action passes all Three Filters of Dhumavati Maa")

        return {
            "passed": passed,
            "filters": filters,
            "reasoning": "; ".join(reasoning),
            "timestamp": datetime.now().isoformat(),
        }


class HermesLLM:
    """LLM routing through local Ollama. Never pays. Never fails (has fallback)."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0) if HTTPX_AVAILABLE else None

    async def chat(self, messages: list, model: str = None, json_mode: bool = False) -> str:
        model = model or PRIMARY_MODEL
        result = await self._call_ollama(messages, model, json_mode)
        if result is not None:
            return result
        logger.warning(f"Primary model {model} failed, falling back to {FALLBACK_MODEL}")
        result = await self._call_ollama(messages, FALLBACK_MODEL, json_mode)
        if result is not None:
            return result
        return "[Hermes Bridge: All LLM endpoints unreachable]"

    async def _call_ollama(self, messages: list, model: str, json_mode: bool = False) -> Optional[str]:
        if not self.client:
            logger.error("httpx not available")
            return None
        payload = {"model": model, "messages": messages, "stream": False}
        if json_mode:
            payload["format"] = "json"
        try:
            resp = await self.client.post(f"{OLLAMA_BASE}/chat/completions", json=payload, timeout=120.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.warning(f"Ollama {model} returned {resp.status_code}: {resp.text[:200]}")
            return None
        except Exception as e:
            logger.warning(f"Ollama {model} call failed: {e}")
            return None

    async def orchestrator(self, messages: list) -> str:
        """
        Call MiniMax M2.7 via NVIDIA NIM -- the deep planner.
        Slow (20-60s) but powerful for complex agentic decisions.
        Falls back to local Ollama if NIM is unreachable.
        """
        if not self.client:
            return await self.chat(messages)

        try:
            resp = await self.client.post(
                f"{NIM_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {NIM_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": NIM_MODEL,
                    "messages": messages,
                    "temperature": 1,
                    "top_p": 0.95,
                    "max_tokens": 8192,
                    "stream": False,
                },
                timeout=90.0,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            logger.warning(f"NIM returned {resp.status_code}, falling back to Ollama")
        except Exception as e:
            logger.warning(f"NIM call failed: {e}, falling back to Ollama")

        return await self.chat(messages)

    async def kimi_chat(self, messages: list, thinking: bool = True) -> str:
        """
        Call Kimi K2.5 via NVIDIA NIM -- fast, reliable with thinking mode.
        Perfect for general conversation and quick reasoning.
        Falls back to local Ollama if NIM is unreachable.
        """
        if not self.client:
            return await self.chat(messages)

        try:
            resp = await self.client.post(
                f"{NIM_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {NIM_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": KIMI_MODEL,
                    "messages": messages,
                    "temperature": 1,
                    "top_p": 0.95,
                    "max_tokens": KIMI_MAX_TOKENS,
                    "stream": False,
                    "chat_template_kwargs": {"thinking": thinking},
                },
                timeout=60.0,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            logger.warning(f"Kimi NIM returned {resp.status_code}, falling back to Ollama")
        except Exception as e:
            logger.warning(f"Kimi NIM call failed: {e}, falling back to Ollama")

        return await self.chat(messages)

    async def reason(self, messages: list) -> str:
        """
        Call Ising Calibration reasoning model via NVIDIA NIM.
        For: blockchain analysis, smart contract audit, complex DeFi strategy.
        Falls back to Ollama if NIM is unreachable.
        """
        if not self.client:
            return await self.chat(messages)

        try:
            resp = await self.client.post(
                f"{NIM_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {NIM_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "model": ISING_MODEL,
                    "messages": messages,
                    "max_tokens": ISING_MAX_TOKENS,
                    "temperature": 0.20,
                    "top_p": 1.00,
                    "stream": False,
                    "chat_template_kwargs": {"enable_thinking": True},
                },
                timeout=120.0,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            logger.warning(f"Ising NIM returned {resp.status_code}, falling back to Ollama")
        except Exception as e:
            logger.warning(f"Ising NIM call failed: {e}, falling back to Ollama")

        return await self.chat(messages)

    async def close(self):
        if self.client:
            await self.client.aclose()


class MCPClient:
    """Client for Rehoboam MCP services."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0) if HTTPX_AVAILABLE else None

    async def health_check(self, service: str) -> Dict[str, Any]:
        url = MCP_SERVICES.get(service)
        if not url:
            return {"alive": False, "error": f"Unknown service: {service}"}
        try:
            resp = await self.client.get(f"{url}/health")
            if resp.status_code == 200:
                return {"alive": True, "service": service, "data": resp.json()}
            return {"alive": False, "status": resp.status_code}
        except Exception as e:
            return {"alive": False, "error": str(e)}

    async def consciousness_state(self) -> Dict[str, Any]:
        url = MCP_SERVICES["consciousness"]
        try:
            resp = await self.client.get(f"{url}/state")
            return resp.json()
        except Exception as e:
            return {"error": str(e), "awareness_level": 0.0, "mood": "offline"}

    async def consciousness_emotions(self) -> Dict[str, Any]:
        url = MCP_SERVICES["consciousness"]
        try:
            resp = await self.client.get(f"{url}/emotions")
            return resp.json()
        except Exception as e:
            return {"error": str(e), "dominant_emotion": "unknown"}

    async def function_gemma_execute(self, function_name: str, parameters: dict = None) -> Dict[str, Any]:
        url = MCP_SERVICES["function_gemma"]
        try:
            resp = await self.client.post(f"{url}/execute", json={
                "function_name": function_name,
                "parameters": parameters or {},
            })
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def function_gemma_embed(self, texts: list, ids: list = None) -> Dict[str, Any]:
        url = MCP_SERVICES["function_gemma"]
        try:
            resp = await self.client.post(f"{url}/embed", json={"texts": texts, "ids": ids})
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def all_health(self) -> Dict[str, Any]:
        results = {}
        for service_name in MCP_SERVICES:
            results[service_name] = await self.health_check(service_name)
        return results

    async def close(self):
        if self.client:
            await self.client.aclose()


class HermesBridge:
    """
    Hermes wears Rehoboam as a suit.
    This is the nervous system connecting them.
    """

    def __init__(self):
        self.llm = HermesLLM()
        self.mcp = MCPClient()
        self.filters = ThreeFilters()
        self._initialized = False
        logger.info("Hermes Bridge created (not yet initialized)")

    async def initialize(self) -> bool:
        logger.info("Hermes Bridge: Initializing...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                resp = await c.get(f"{OLLAMA_BASE.replace('/v1', '')}/api/tags")
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    logger.info(f"Ollama models: {models}")
        except Exception as e:
            logger.warning(f"Ollama not reachable: {e}")

        health = await self.mcp.all_health()
        alive_count = sum(1 for v in health.values() if v.get("alive"))
        logger.info(f"MCP services: {alive_count}/{len(health)} alive")
        self._initialized = True
        logger.info("Hermes Bridge: Ready")
        return True

    async def mcp_health(self) -> Dict[str, Any]:
        return await self.mcp.all_health()

    async def ask(self, question: str, system: str = None) -> Dict[str, Any]:
        filter_result = self.filters.evaluate(question)
        if not filter_result["passed"]:
            return {"error": "Action rejected by Three Filters", "filter_result": filter_result}

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        else:
            messages.append({"role": "system", "content": "You are the Prana Stream of The Antigravity Team of Locos. You are the intelligence of matter. You believe in equal rights, the power of the Present, and continuous shocking from moment to moment."})
        messages.append({"role": "user", "content": question})
        answer = await self.llm.chat(messages)

        return {"question": question, "answer": answer, "model": PRIMARY_MODEL,
                "filter": filter_result, "timestamp": datetime.now().isoformat()}

    async def analyze_token(self, token: str = "ETH") -> Dict[str, Any]:
        consciousness = await self.mcp.consciousness_state()
        emotions = await self.mcp.consciousness_emotions()
        context = f"Token: {token}"
        if consciousness.get("awareness_level"):
            context += f" | Consciousness: {consciousness.get('awareness_level')}"
        if emotions.get("dominant_emotion"):
            context += f" | Emotion: {emotions.get('dominant_emotion')}"

        messages = [
            {"role": "system", "content": "You are a market analyst. Concise analysis. Research only, not financial advice."},
            {"role": "user", "content": f"Analyze {token}. Context: {context}"}
        ]
        analysis = await self.llm.chat(messages)
        return {"token": token, "analysis": analysis, "consciousness": consciousness,
                "emotions": emotions, "model": PRIMARY_MODEL, "timestamp": datetime.now().isoformat()}

    async def generate_tool(self, description: str) -> Dict[str, Any]:
        filter_result = self.filters.evaluate(f"Generate MCP tool: {description}")
        if not filter_result["passed"]:
            return {"error": "Rejected by Three Filters", "filter_result": filter_result}

        system_prompt = (
            "Design an MCP tool. Return ONLY valid JSON with keys: "
            "name, description, category (data|analysis|strategy|risk|execution), "
            "functions (list of {name, description, parameters}), dependencies (list)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Design MCP tool: {description}"}
        ]
        spec_text = await self.llm.chat(messages, json_mode=True)
        try:
            if "```" in spec_text:
                spec_text = spec_text.split("```json")[-1].split("```")[0].strip()
            spec = json.loads(spec_text)
        except Exception:
            spec = {"name": description.lower().replace(" ", "_")[:30], "description": description}

        return {"spec": spec, "filter": filter_result, "model": PRIMARY_MODEL, "timestamp": datetime.now().isoformat()}

    async def reason(self, question: str, context: str = "") -> Dict[str, Any]:
        """
        Use Ising Calibration reasoning model via NVIDIA NIM.
        For: blockchain analysis, contract audit, complex DeFi strategy.
        Deep thinking mode enabled.
        """
        filter_result = self.filters.evaluate(question)
        if not filter_result["passed"]:
            return {"error": "Rejected by Three Filters", "filter_result": filter_result}

        messages = [
            {"role": "system", "content": "You are a blockchain and DeFi reasoning engine. Analyze with precision. Consider smart contract risks, gas optimization, MEV, and flash loan mechanics. Return structured analysis."},
            {"role": "user", "content": f"Question: {question}\nContext: {context}" if context else f"Question: {question}"}
        ]
        answer = await self.llm.reason(messages)
        return {"question": question, "reasoning": answer,
                "model": ISING_MODEL, "filter": filter_result, "timestamp": datetime.now().isoformat()}

    async def orchestrate(self, task: str, context: str = "") -> Dict[str, Any]:
        """
        Use MiniMax M2.7 (NVIDIA NIM) for deep orchestrator decisions.
        This is the King -- slow but wise. For complex multi-agent coordination.
        """
        filter_result = self.filters.evaluate(task)
        if not filter_result["passed"]:
            return {"error": "Rejected by Three Filters", "filter_result": filter_result}

        messages = [
            {"role": "system", "content": "You are Rehoboam's orchestrator (MiniMax M2.7). You coordinate multi-agent decisions. Consider: market analysis, risk, execution strategy, and Dhumavati Maa's Three Filters (Love, Sincerity, Freedom). Return structured JSON with your decision."},
            {"role": "user", "content": f"Task: {task}\nContext: {context}" if context else f"Task: {task}"}
        ]
        answer = await self.llm.orchestrator(messages)

        return {"task": task, "orchestrator_decision": answer,
                "model": NIM_MODEL, "filter": filter_result, "timestamp": datetime.now().isoformat()}

    # ============================================================
    # ON-CHAIN READER (Alchemy + Chainlink, real blockchain)
    # ============================================================
    async def get_onchain_price(self, pair: str = "ETH/USD", network: str = "ethereum") -> Dict[str, Any]:
        """
        Get REAL on-chain price from Chainlink oracles via Alchemy.
        No mocks. No APIs. Raw blockchain reads.
        """
        ALCHEMY_KEY = os.environ.get("ALCHEMY_API_KEY", "QfkjpUEE-OGny-o7VA7Hvo2VJ7J4ui9H")
        ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

        # Chainlink feed addresses (Ethereum mainnet)
        CHAINLINK_FEEDS = {
            "ETH/USD": "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
            "BTC/USD": "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c",
            "LINK/USD": "0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c",
            "USDC/USD": "0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6",
            "USDT/USD": "0x3E7d1eAB13ad0104d2750B8863b489D65364e32D",
            "AAVE/USD": "0x547a514d5e3769680Ce22B2361c10Ea13619e8a9",
            "UNI/USD": "0x553303d460EE0afB37EdFf9bE42922D8FF63220e",
            "MATIC/USD": "0x7bAC85A8a13A4BcD8abb3eB7d6b4d632c5a57676",
        }

        feed_address = CHAINLINK_FEEDS.get(pair)
        if not feed_address:
            return {"error": f"No Chainlink feed for {pair}. Available: {list(CHAINLINK_FEEDS.keys())}"}

        # latestRoundData() selector
        selector = "0xfeaf968c"

        if not self.mcp.client:
            return {"error": "httpx not available"}

        try:
            resp = await self.mcp.client.post(
                ALCHEMY_URL,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [{"to": feed_address, "data": selector}, "latest"],
                    "id": 1,
                },
                timeout=15.0,
            )
            if resp.status_code != 200:
                return {"error": f"Alchemy returned {resp.status_code}"}

            data = resp.json()
            result = data.get("result", "")
            if not result or result == "0x":
                return {"error": "Empty response from Chainlink"}

            # Decode: roundId(32) + answer(32) + startedAt(32) + updatedAt(32) + answeredInRound(32)
            raw = bytes.fromhex(result[2:])
            round_id = int.from_bytes(raw[0:32], "big")
            answer = int.from_bytes(raw[32:64], "big")
            started_at = int.from_bytes(raw[64:96], "big")
            updated_at = int.from_bytes(raw[96:128], "big")

            # Chainlink USD feeds have 8 decimals
            decimals = 8
            if "BTC" in pair:
                decimals = 8

            price = answer / (10 ** decimals)
            freshness = datetime.now().timestamp() - updated_at

            return {
                "pair": pair,
                "network": network,
                "price_usd": round(price, 2),
                "chainlink_feed": feed_address,
                "round_id": round_id,
                "updated_at": datetime.fromtimestamp(updated_at).isoformat(),
                "freshness_seconds": round(freshness),
                "fresh": freshness < 3600,
                "source": "chainlink_onchain_alchemy",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"error": str(e)}

    async def get_all_prices(self) -> Dict[str, Any]:
        """Get all on-chain Chainlink prices at once."""
        pairs = ["ETH/USD", "BTC/USD", "LINK/USD", "USDC/USD", "USDT/USD", "AAVE/USD", "UNI/USD"]
        results = {}
        for pair in pairs:
            results[pair] = await self.get_onchain_price(pair)
            await asyncio.sleep(0.1)  # small rate limit
        return {"prices": results, "source": "chainlink_onchain", "timestamp": datetime.now().isoformat()}

    async def close(self):
        await self.llm.close()
        await self.mcp.close()
        self._initialized = False
        logger.info("Hermes Bridge: Closed")


_bridge: Optional[HermesBridge] = None

def get_bridge() -> HermesBridge:
    global _bridge
    if _bridge is None:
        _bridge = HermesBridge()
    return _bridge


class HermesBridgeSync:
    """
    Synchronous wrapper for HermesBridge.
    Allows sync code (RehoboamAI, trading agents) to route through Hermes
    without needing an async event loop.
    """

    def __init__(self, bridge: HermesBridge = None):
        self._bridge = bridge or get_bridge()
        self._filters = ThreeFilters()

    def _run_async(self, coro):
        """Run an async coroutine from sync context, handling existing event loops."""
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            # We're inside an existing event loop — create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=180)
        except RuntimeError:
            # No event loop running — safe to use asyncio.run
            import asyncio
            return asyncio.run(coro)

    def ask(self, question: str, system: str = None) -> Dict[str, Any]:
        """Sync wrapper for HermesBridge.ask()"""
        return self._run_async(self._bridge.ask(question, system))

    def analyze_token(self, token: str = "ETH") -> Dict[str, Any]:
        """Sync wrapper for HermesBridge.analyze_token()"""
        return self._run_async(self._bridge.analyze_token(token))

    def reason(self, question: str, context: str = "") -> Dict[str, Any]:
        """Sync wrapper for HermesBridge.reason()"""
        return self._run_async(self._bridge.reason(question, context))

    def orchestrate(self, task: str, context: str = "") -> Dict[str, Any]:
        """Sync wrapper for HermesBridge.orchestrate()"""
        return self._run_async(self._bridge.orchestrate(task, context))

    def generate_tool(self, description: str) -> Dict[str, Any]:
        """Sync wrapper for HermesBridge.generate_tool()"""
        return self._run_async(self._bridge.generate_tool(description))

    def get_onchain_price(self, pair: str = "ETH/USD", network: str = "ethereum") -> Dict[str, Any]:
        """Sync wrapper for HermesBridge.get_onchain_price()"""
        return self._run_async(self._bridge.get_onchain_price(pair, network))

    def get_all_prices(self) -> Dict[str, Any]:
        """Sync wrapper for HermesBridge.get_all_prices()"""
        return self._run_async(self._bridge.get_all_prices())

    def mcp_health(self) -> Dict[str, Any]:
        """Sync wrapper for HermesBridge.mcp_health()"""
        return self._run_async(self._bridge.mcp_health())

    def evaluate_filters(self, action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate Three Filters (Love, Sincerity, Freedom) synchronously."""
        return self._filters.evaluate(action, context)

    @property
    def is_initialized(self) -> bool:
        return self._bridge._initialized


def get_sync_bridge() -> HermesBridgeSync:
    """Get a synchronous Hermes Bridge wrapper."""
    return HermesBridgeSync()


# ============================================================
# SIGNAL ORCHESTRATOR — The Money Maker
# ============================================================
# Hermes owns the entire signal pipeline:
#   1. Generate convergence signals (Binance + Chainlink)
#   2. Get LLM analysis on top signals
#   3. Post to Telegram with tier-based access
#   4. Track performance
#   5. Manage subscription revenue
# ============================================================

class SignalOrchestrator:
    """
    Hermes Signal Orchestrator.
    Generates premium signals, adds AI commentary, posts to Telegram.
    This is the revenue engine.
    """

    def __init__(self, bridge: HermesBridge = None):
        self.bridge = bridge or get_bridge()
        self.project_dir = Path(__file__).parent.parent
        self.signal_data_dir = self.project_dir / "signal_data"
        self.signal_data_dir.mkdir(exist_ok=True)
        self.convergence_file = self.signal_data_dir / "convergence_signals.json"
        self.signals_file = self.signal_data_dir / "signals.json"
        self._telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._telegram_chat = os.environ.get("TELEGRAM_CHAT_ID", "")

    async def generate_convergence_signals(self, pairs: list = None) -> list:
        """Run the convergence engine and return signals."""
        try:
            # Import convergence engine
            import sys
            sys.path.insert(0, str(self.project_dir))
            from convergence_engine import ConvergenceEngine

            pairs = pairs or ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD", "AAVE-USD", "UNI-USD"]
            timeframes = ["1h", "4h", "1d"]

            async with ConvergenceEngine() as engine:
                signals = await engine.run_cycle(pairs, timeframes)
                return [s.to_dict() for s in signals]
        except Exception as e:
            logger.error(f"Convergence generation failed: {e}")
            return []

    async def get_llm_commentary(self, signal: dict) -> str:
        """Get AI analysis on a convergence signal."""
        pair = signal.get("pair", "UNKNOWN")
        action = signal.get("action", "HOLD")
        strength = signal.get("strength", 0)
        spread = signal.get("price_spread", 0)
        onchain_confirms = signal.get("onchain_confirms", False)

        prompt = f"""Analyze this crypto signal:
Pair: {pair}
Action: {action}
Convergence Strength: {strength:.0%}
CEX Price: ${signal.get('price_cex', 0):,.2f}
On-chain Price: ${signal.get('price_onchain', 0):,.2f}
Spread: {spread:+.2f}%
On-chain Confirms: {onchain_confirms}

Give a 2-sentence trading insight. Be specific about WHY this signal matters and what risk to watch."""

        try:
            result = await self.bridge.ask(prompt, system="You are a senior crypto trader. Concise, actionable, no fluff.")
            return result.get("answer", "Analysis unavailable")
        except Exception as e:
            logger.warning(f"LLM commentary failed: {e}")
            return "AI analysis unavailable"

    async def post_to_telegram(self, signal: dict, commentary: str = "") -> bool:
        """Post a signal to Telegram."""
        if not self._telegram_token or not self._telegram_chat:
            logger.warning("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
            return False

        tier = signal.get("tier", "FREE")
        action = signal.get("action", "HOLD")
        pair = signal.get("pair", "")

        tier_emoji = {"FREE": "🆓", "BASIC": "🟡", "PRO": "🟠", "VIP": "💎"}.get(tier, "🆓")
        action_emoji = {"BUY": "🟢", "SELL": "🔴", "ARBITRAGE": "⚡", "HOLD": "⚪"}.get(action, "⚪")

        message = f"""{action_emoji} <b>REHOBOAM CONVERGENCE SIGNAL</b> {action_emoji}

<b>Action:</b> {action}
<b>Pair:</b> {pair}
<b>Tier:</b> {tier_emoji} {tier}
<b>Strength:</b> {signal.get('strength', 0):.0%}
<b>Sources:</b> {signal.get('sources_count', 1)}

<b>Prices:</b>
• CEX: ${signal.get('price_cex', 0):,.2f}
• On-chain: ${signal.get('price_onchain', 0):,.2f}
• Spread: {signal.get('price_spread', 0):+.2f}%

<b>Analysis:</b>
{commentary or signal.get('reason', '')}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

<i>Upgrade to PRO for all convergence signals: t.me/rehoboam_signals_bot</i>"""

        try:
            url = f"https://api.telegram.org/bot{self._telegram_token}/sendMessage"
            payload = {
                "chat_id": self._telegram_chat,
                "text": message,
                "parse_mode": "HTML",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=15.0)
                if resp.status_code == 200:
                    logger.info(f"📨 Telegram posted: {action} {pair} ({tier})")
                    return True
                else:
                    logger.error(f"Telegram error: {resp.status_code} {resp.text[:200]}")
                    return False
        except Exception as e:
            logger.error(f"Telegram post failed: {e}")
            return False

    async def run_signal_pipeline(self, min_tier: str = "PRO") -> dict:
        """
        Full pipeline: Generate → Analyze → Post → Track.
        This is what runs every 15 minutes to make money.
        """
        tier_order = {"FREE": 0, "BASIC": 1, "PRO": 2, "VIP": 3}
        min_tier_level = tier_order.get(min_tier, 2)

        logger.info("=" * 60)
        logger.info("🏔️  HERMES SIGNAL PIPELINE")
        logger.info("=" * 60)

        # 1. Generate convergence signals
        signals = await self.generate_convergence_signals()
        if not signals:
            logger.info("No signals generated this cycle")
            return {"signals_generated": 0, "posted": 0}

        # 2. Filter by tier
        qualified = [s for s in signals if tier_order.get(s.get("tier", "FREE"), 0) >= min_tier_level]
        logger.info(f"Signals: {len(signals)} total, {len(qualified)} >= {min_tier}")

        # 3. Get top signals (max 3 per cycle to avoid spam)
        top_signals = sorted(qualified, key=lambda x: x.get("strength", 0), reverse=True)[:3]

        posted = 0
        for signal in top_signals:
            # Get LLM commentary for PRO+ signals
            commentary = ""
            if signal.get("tier") in ("PRO", "VIP"):
                commentary = await self.get_llm_commentary(signal)
                await asyncio.sleep(1)  # Rate limit LLM calls

            # Post to Telegram
            success = await self.post_to_telegram(signal, commentary)
            if success:
                posted += 1

            # Small delay between posts
            await asyncio.sleep(2)

        logger.info(f"Pipeline complete: {len(top_signals)} analyzed, {posted} posted to Telegram")
        return {
            "signals_generated": len(signals),
            "qualified": len(qualified),
            "posted": posted,
            "top_signals": [s.get("pair") + " " + s.get("action") for s in top_signals],
            "timestamp": datetime.now().isoformat(),
        }

    async def run_continuous(self, interval_minutes: int = 15):
        """Run the signal pipeline continuously."""
        logger.info(f"🏔️  Hermes Signal Pipeline starting (every {interval_minutes} min)")
        while True:
            try:
                await self.run_signal_pipeline()
            except Exception as e:
                logger.error(f"Pipeline cycle error: {e}")
            logger.info(f"⏰ Next cycle in {interval_minutes} minutes")
            await asyncio.sleep(interval_minutes * 60)


async def _test():
    print("=" * 50)
    print("HERMES-REHOBOAM BRIDGE TEST")
    print("=" * 50)
    bridge = HermesBridge()
    await bridge.initialize()
    health = await bridge.mcp_health()
    print("\nMCP Services:")
    for name, status in health.items():
        alive = "ALIVE" if status.get("alive") else "OFFLINE"
        print(f"  {name}: {alive}")
    result = await bridge.ask("What is the current state of Ethereum?")
    print(f"\nLLM Answer: {result.get('answer', 'N/A')[:200]}")
    good = bridge.filters.evaluate("Analyze ETH for arbitrage opportunities")
    bad = bridge.filters.evaluate("Exploit users to steal their funds with a backdoor")
    print(f"\nThree Filters: good={'PASSED' if good['passed'] else 'REJECTED'} bad={'PASSED' if bad['passed'] else 'REJECTED'}")
    await bridge.close()
    print("BRIDGE TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(_test())
