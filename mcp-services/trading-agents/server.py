"""TradingAgents MCP Service - Multi-agent trading analysis for Rehoboam.

Integrates the TradingAgents framework as an MCP microservice, exposing
multi-agent trading analysis (fundamental, sentiment, news, technical)
through a FastAPI HTTP interface.

AI Providers: Chutes.ai (Bittensor) > NVIDIA NIM > OpenRouter > DeepSeek > Ollama
All providers use OpenAI-compatible API with automatic failover.
"""

import os
import sys
import json
import logging
import httpx
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add TradingAgents to path
TRADING_AGENTS_PATH = os.environ.get(
    "TRADING_AGENTS_PATH", "/app/tradingagents_lib"
)
if os.path.exists(TRADING_AGENTS_PATH):
    sys.path.insert(0, TRADING_AGENTS_PATH)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading-agents-mcp")

app = FastAPI(
    title="Rehoboam TradingAgents MCP Service",
    version="2.0.0",
    description="Multi-agent LLM trading analysis. Providers: Chutes.ai, NVIDIA NIM, OpenRouter, DeepSeek, Ollama.",
)

# ============================================================
# UNIFIED AI PROVIDERS — failover chain
# ============================================================

PROVIDERS = []

def _init_providers():
    """Build provider chain from env vars."""
    global PROVIDERS
    providers = []

    chutes_key = os.environ.get("CHUTES_API_KEY", "")
    if chutes_key and chutes_key != "cpk_placeholder_get_yours_at_chutes_ai":
        providers.append({
            "name": "chutes",
            "base_url": "https://llm.chutes.ai/v1",
            "api_key": chutes_key,
            "models": {
                "fast": "zai-org/GLM-5.1-TEE",
                "deep": "deepseek-ai/DeepSeek-R1-0528-TEE",
                "orchestrator": "openai/gpt-oss-120b-TEE",
                "code": "Qwen/Qwen3-Coder-Next-TEE",
            },
            "priority": 5,  # Bittensor has quota issues, demote to lowest priority
        })

    nvidia_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
    if nvidia_key:
        providers.append({
            "name": "nvidia",
            "base_url": "https://integrate.api.nvidia.com/v1",
            "api_key": nvidia_key,
            "models": {
                "fast": "z-ai/glm-5.1",
                "deep": "moonshotai/kimi-k2.5",
                "orchestrator": "minimaxai/minimax-m2.7",
                "code": "qwen/qwen3-coder-32b-instruct",
            },
            "priority": 2,
        })

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        providers.append({
            "name": "openrouter",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": openrouter_key,
            "models": {
                "fast": "google/gemma-3-4b-it:free",
                "deep": "deepseek/deepseek-r1-0528:free",
                "orchestrator": "qwen/qwen3-235b-a22b:free",
                "code": "qwen/qwen3-coder:free",
            },
            "priority": 3,
        })

    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if deepseek_key:
        providers.append({
            "name": "deepseek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": deepseek_key,
            "models": {
                "fast": "deepseek-chat",
                "deep": "deepseek-reasoner",
                "orchestrator": "deepseek-chat",
                "code": "deepseek-chat",
            },
            "priority": 4,
        })

    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1")
    providers.append({
        "name": "ollama",
        "base_url": ollama_url,
        "api_key": "ollama",
        "models": {
            "fast": os.environ.get("OLLAMA_FAST_MODEL", "glm-5.1:cloud"),
            "deep": os.environ.get("OLLAMA_DEEP_MODEL", "gpt-oss:120b-cloud"),
            "orchestrator": os.environ.get("OLLAMA_ORCH_MODEL", "gpt-oss:120b-cloud"),
            "code": os.environ.get("OLLAMA_CODE_MODEL", "glm-5.1:cloud"),
        },
        "priority": 1,  # Make Ollama primary provider
    })

    providers.sort(key=lambda p: p["priority"])
    PROVIDERS = providers
    logger.info(f"AI providers loaded: {[p['name'] for p in PROVIDERS]}")


async def call_ai(messages: List[Dict], role: str = "fast", temperature: float = 0.7,
                   max_tokens: int = 2048, preferred: str = None) -> Dict[str, Any]:
    """Call AI with automatic failover across all providers."""
    ordered = list(PROVIDERS)
    if preferred:
        preferred_list = [p for p in ordered if p["name"] == preferred]
        others = [p for p in ordered if p["name"] != preferred]
        ordered = preferred_list + others

    errors = []
    for provider in ordered:
        model = provider["models"].get(role, provider["models"].get("fast"))
        if not model:
            continue
        try:
            headers = {
                "Authorization": f"Bearer {provider['api_key']}",
                "Content-Type": "application/json",
            }
            if provider["name"] == "openrouter":
                headers["HTTP-Referer"] = "https://rehoboam.ai"
                headers["X-Title"] = "Rehoboam TradingAgents"

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{provider['base_url']}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code != 200:
                    raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")

                data = resp.json()
                content = ""
                if "choices" in data and data["choices"]:
                    content = data["choices"][0].get("message", {}).get("content", "")

                return {
                    "content": content,
                    "provider": provider["name"],
                    "model": model,
                    "role": role,
                    "usage": data.get("usage", {}),
                }
        except Exception as e:
            logger.warning(f"Provider {provider['name']}/{model} failed: {e}")
            errors.append(f"{provider['name']}: {str(e)[:200]}")

    return {"content": "", "error": "All providers failed", "details": errors}


# ============================================================
# PYDANTIC MODELS
# ============================================================

class AnalysisRequest(BaseModel):
    ticker: str = Field(..., description="Stock/crypto ticker symbol (e.g. BTC-USD, AAPL)")
    date: Optional[str] = Field(None, description="Analysis date YYYY-MM-DD (defaults to today)")
    llm_provider: str = Field("auto", description="LLM provider: auto, chutes, nvidia, openrouter, deepseek, ollama")
    deep_think_llm: str = Field("", description="Override deep-think model (empty = use provider default)")
    quick_think_llm: str = Field("", description="Override quick-think model (empty = use provider default)")
    max_debate_rounds: int = Field(1, description="Number of debate rounds between researchers")
    output_language: str = Field("English", description="Output language for reports")


class AnalysisResponse(BaseModel):
    ticker: str
    date: str
    decision: str
    confidence: float
    analyst_reports: Dict[str, Any] = {}
    researcher_debate: List[Dict[str, Any]] = []
    risk_assessment: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class QuickAnalysisRequest(BaseModel):
    ticker: str
    provider: str = "auto"
    model: str = ""
    role: str = "fast"


class QuickAnalysisResponse(BaseModel):
    ticker: str
    sentiment: str
    recommendation: str
    confidence: float
    reasoning: str
    provider: str = ""
    model: str = ""


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    tradingagents_available: bool
    providers: List[Dict[str, Any]] = []
    ollama_models: List[str] = []


# ============================================================
# OLLAMA DISCOVERY
# ============================================================

def get_ollama_models() -> List[str]:
    import subprocess
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return [line.split()[0] for line in result.stdout.strip().split("\n")[1:] if line.strip()]
    except Exception:
        pass
    return []


# ============================================================
# ENDPOINTS
# ============================================================

@app.on_event("startup")
async def startup():
    _init_providers()


@app.get("/health", response_model=HealthResponse)
async def health():
    ta_available = False
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        ta_available = True
    except ImportError:
        pass
    safe_providers = [
        {"name": p["name"], "models": p["models"], "priority": p["priority"]}
        for p in PROVIDERS
    ]
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        tradingagents_available=ta_available,
        providers=safe_providers,
        ollama_models=get_ollama_models(),
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """Run full multi-agent trading analysis."""
    date_str = request.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Try TradingAgents framework first
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        # Map provider name for TradingAgents config
        provider = request.llm_provider
        if provider == "auto":
            provider = "ollama"  # TradingAgents uses its own config

        # Determine data source - prefer real APIs over yfinance
        alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
        polygon_key = os.environ.get("POLYGON_API_KEY", "")

        if alpha_vantage_key and alpha_vantage_key != "demo":
            core_data_source = "alphavantage"
        elif polygon_key:
            core_data_source = "polygon"
        else:
            core_data_source = "yfinance"  # fallback

        config = {
            "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            "results_dir": "/tmp/tradingagents_results",
            "data_cache_dir": "/tmp/tradingagents_cache",
            "llm_provider": provider if provider != "auto" else "ollama",
            "deep_think_llm": request.deep_think_llm or "gpt-oss:120b-cloud",
            "quick_think_llm": request.quick_think_llm or "glm-5.1:cloud",
            "max_debate_rounds": request.max_debate_rounds,
            "max_risk_discuss_rounds": 1,
            "max_recur_limit": 100,
            "output_language": request.output_language,
            "data_vendors": {
                "core_stock_apis": core_data_source,
                "technical_indicators": "yfinance",
                "fundamental_data": core_data_source,
                "news_data": "newsapi",
            },
            "api_keys": {
                "alpha_vantage": alpha_vantage_key,
                "polygon": polygon_key,
            },
        }
        if provider == "ollama":
            config["backend_url"] = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")

        ta = TradingAgentsGraph(debug=True, config=config)
        _, decision = ta.propagate(request.ticker, date_str)

        return AnalysisResponse(
            ticker=request.ticker, date=date_str,
            decision=decision, confidence=0.8,
            metadata={"llm_provider": provider, "framework": "TradingAgents"},
        )
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"TradingAgents failed, falling back to direct AI: {e}")

    # Fallback: direct AI call for trading analysis
    messages = [
        {"role": "system", "content": "You are an expert crypto trading analyst. Respond in JSON with keys: decision (BUY/SELL/HOLD), confidence (0-1), reasoning, sentiment (bullish/bearish/neutral), risk_level (low/medium/high)."},
        {"role": "user", "content": f"Analyze {request.ticker} for {date_str}. Consider current market conditions, technical indicators, and sentiment."},
    ]
    result = await call_ai(messages, role="deep", preferred=request.llm_provider if request.llm_provider != "auto" else None)

    try:
        parsed = json.loads(result.get("content", "{}"))
    except json.JSONDecodeError:
        parsed = {"decision": "HOLD", "confidence": 0.5, "reasoning": result.get("content", "")[:500]}

    return AnalysisResponse(
        ticker=request.ticker, date=date_str,
        decision=parsed.get("decision", "HOLD"),
        confidence=float(parsed.get("confidence", 0.5)),
        metadata={
            "provider": result.get("provider", "unknown"),
            "model": result.get("model", "unknown"),
            "framework": "direct_ai",
        },
    )


@app.post("/quick-analysis", response_model=QuickAnalysisResponse)
async def quick_analysis(request: QuickAnalysisRequest):
    """Quick single-model analysis using unified AI failover chain."""
    messages = [
        {"role": "system", "content": "You are a crypto trading analyst. Respond in JSON: {sentiment, recommendation, confidence, reasoning}"},
        {"role": "user", "content": f"Quick analysis of {request.ticker}. Sentiment? Recommendation? Confidence 0-1? Brief reasoning."},
    ]
    role = request.role or "fast"
    preferred = request.provider if request.provider != "auto" else None

    result = await call_ai(messages, role=role, temperature=0.3, max_tokens=512, preferred=preferred)

    try:
        parsed = json.loads(result.get("content", "{}"))
    except json.JSONDecodeError:
        content = result.get("content", "")
        parsed = {
            "sentiment": "neutral",
            "recommendation": "hold",
            "confidence": 0.5,
            "reasoning": content[:500] if content else "No output",
        }

    return QuickAnalysisResponse(
        ticker=request.ticker,
        sentiment=parsed.get("sentiment", "neutral"),
        recommendation=parsed.get("recommendation", "hold"),
        confidence=float(parsed.get("confidence", 0.5)),
        reasoning=parsed.get("reasoning", ""),
        provider=result.get("provider", ""),
        model=result.get("model", ""),
    )


# ============================================================
# REAL DATA ENDPOINTS — Alpha Vantage, Polygon
# ============================================================

@app.get("/data/quote/{ticker}")
async def get_quote(ticker: str, source: str = "auto"):
    """Get real-time quote from Alpha Vantage or Polygon."""
    alpha_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    polygon_key = os.environ.get("POLYGON_API_KEY", "")

    # Determine best data source
    if source == "auto":
        if alpha_key and alpha_key != "demo":
            source = "alphavantage"
        elif polygon_key and polygon_key != "demo":
            source = "polygon"
        else:
            return {"error": "No API keys configured. Get free keys at alphavantage.co or polygon.io"}

    try:
        if source == "alphavantage":
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={alpha_key}"
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                data = resp.json()
                quote = data.get("Global Quote", {})
                return {
                    "ticker": ticker,
                    "source": "alphavantage",
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent", "0%"),
                    "volume": int(quote.get("06. volume", 0)),
                    "latest_trading_day": quote.get("07. latest trading day"),
                }

        elif source == "polygon":
            url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}?apiKey={polygon_key}"
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                data = resp.json()
                ticker_data = data.get("ticker", {})
                return {
                    "ticker": ticker,
                    "source": "polygon",
                    "price": ticker_data.get("lastTrade", {}).get("p", 0),
                    "change": ticker_data.get("todaysChange", 0),
                    "change_percent": f"{ticker_data.get('todaysChangePerc', 0):.2f}%",
                    "volume": ticker_data.get("day", {}).get("v", 0),
                    "latest_trading_day": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                }
    except Exception as e:
        logger.error(f"Data fetch failed: {e}")
        return {"error": str(e), "ticker": ticker}


@app.get("/data/crypto/{symbol}")
async def get_crypto_quote(symbol: str = "BTC", market: str = "USD"):
    """Get real-time crypto data from Alpha Vantage."""
    alpha_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    if not alpha_key or alpha_key == "demo":
        return {"error": "Alpha Vantage API key not configured"}

    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={symbol}&to_currency={market}&apikey={alpha_key}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            data = resp.json()
            rate = data.get("Realtime Currency Exchange Rate", {})
            return {
                "symbol": symbol,
                "market": market,
                "source": "alphavantage",
                "exchange_rate": float(rate.get("5. Exchange Rate", 0)),
                "bid": float(rate.get("8. Bid Price", 0)),
                "ask": float(rate.get("9. Ask Price", 0)),
                "last_refreshed": rate.get("6. Last Refreshed"),
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/models")
async def list_models():
    """List all available AI models across all providers."""
    ollama_models = get_ollama_models()
    return {
        "providers": [{"name": p["name"], "models": p["models"], "priority": p["priority"]} for p in PROVIDERS],
        "ollama_local": [m for m in ollama_models if "cloud" not in m],
        "ollama_cloud": [m for m in ollama_models if "cloud" in m],
    }


@app.post("/register")
async def register_with_mcp_registry():
    registry_url = os.environ.get("REGISTRY_URL", "http://10.89.0.110:3001")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{registry_url}/api/servers/register",
                json={
                    "name": "trading-agents",
                    "url": "http://mcp-trading-agents:3000",
                    "capabilities": [
                        "multi_agent_trading_analysis",
                        "fundamental_analysis",
                        "sentiment_analysis",
                        "technical_analysis",
                        "news_analysis",
                        "risk_assessment",
                        "quick_analysis",
                        "ai_failover_chain",
                    ],
                    "metadata": {
                        "version": "2.0.0",
                        "type": "trading",
                        "providers": [p["name"] for p in PROVIDERS],
                        "provider_models": {p["name"]: p["models"] for p in PROVIDERS},
                    },
                },
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Registry unreachable: {e}")


@app.on_event("startup")
async def startup_event():
    """Auto-register with MCP registry on startup with retry."""
    registry_url = os.environ.get("REGISTRY_URL", "http://mcp-registry:3001")
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{registry_url}/api/servers/register",
                    json={
                        "name": "trading-agents",
                        "url": f"http://mcp-trading-agents:{os.environ.get('PORT', '3000')}",
                        "capabilities": [
                            "multi_agent_trading_analysis",
                            "fundamental_analysis",
                            "sentiment_analysis",
                            "technical_analysis",
                            "news_analysis",
                            "risk_assessment",
                            "quick_analysis",
                            "ai_failover_chain",
                        ],
                        "metadata": {
                            "version": "2.0.0",
                            "type": "trading",
                            "providers": [p["name"] for p in PROVIDERS],
                            "provider_models": {p["name"]: p["models"] for p in PROVIDERS},
                        },
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    logger.info("✅ Registered with MCP registry on startup")
                    return
        except Exception as e:
            logger.warning(f"Registry registration attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
    logger.error("❌ Failed to register with MCP registry after all retries")


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", "3000"))
    logger.info(f"Starting TradingAgents MCP v2.0 on port {PORT} — Providers: {[p['name'] for p in PROVIDERS]}")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)