import os
import asyncio
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
from datetime import datetime, timezone
import logging

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="MCP Consciousness Layer",
    version="1.0.0",
    description="Provides AI-driven consciousness state and market emotion analysis."
)

# --- Pydantic Models ---
class ConsciousnessState(BaseModel):
    awareness_level: float
    focus_level: float
    mood: str
    narrative: str
    timestamp: str

class MarketEmotions(BaseModel):
    dominant_emotion: str
    fear_grief_index: float
    confidence_index: float
    narrative: str
    timestamp: str

# --- Real Data Analysis ---
async def get_real_consciousness_state() -> ConsciousnessState:
    """Generates real consciousness state based on system metrics and market data."""
    # Get real system metrics
    import psutil

    # Analyze CPU and memory usage for system awareness
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    # Calculate awareness based on system load (inverse relationship)
    awareness_level = max(0.7, 1.0 - (cpu_percent / 200))  # 0.7-1.0 range
    focus_level = max(0.8, 1.0 - (memory.percent / 200))   # 0.8-1.0 range

    # Determine mood based on system state
    if cpu_percent > 80:
        mood = "restless"
    elif memory.percent > 75:
        mood = "cautious"
    else:
        mood = "analytical"

    return ConsciousnessState(
        awareness_level=round(awareness_level, 4),
        focus_level=round(focus_level, 4),
        mood=mood,
        narrative=f"System operating at {cpu_percent}% CPU, {memory.percent}% memory usage. Cognitive functions optimized for current load.",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

async def get_real_market_emotions() -> MarketEmotions:
    """Generates real market emotion analysis using actual market data."""
    # Use real market data sources - for now use a simple API call
    # In production, this would integrate with real market data feeds
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            # Get real BTC price data as a proxy for market sentiment
            response = await client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true", timeout=10)
            data = response.json()

            btc_price = data["bitcoin"]["usd"]
            btc_change = data["bitcoin"]["usd_24h_change"]

            # Calculate real sentiment based on price movement
            if btc_change > 5:
                dominant_emotion = "greed"
                confidence_index = 0.8
            elif btc_change < -5:
                dominant_emotion = "fear"
                confidence_index = 0.7
            else:
                dominant_emotion = "neutral"
                confidence_index = 0.6

            fear_grief_index = max(20, min(80, 50 + (btc_change * 2)))  # 20-80 range

            return MarketEmotions(
                dominant_emotion=dominant_emotion,
                fear_grief_index=round(fear_grief_index, 2),
                confidence_index=round(confidence_index, 3),
                narrative=f"BTC at ${btc_price:,.0f} ({btc_change:+.1f}%). Market showing {dominant_emotion} sentiment with {confidence_index*100:.0f}% confidence.",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    except Exception:
        # Fallback to neutral if API fails
        return MarketEmotions(
            dominant_emotion="neutral",
            fear_grief_index=50.0,
            confidence_index=0.5,
            narrative="Market data temporarily unavailable. Maintaining neutral stance until data connectivity restored.",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

# --- API Endpoints ---
@app.get("/health", status_code=200)
async def health_check():
    """Health check endpoint for Docker and orchestration."""
    return {"status": "ok"}

@app.get("/state", response_model=ConsciousnessState)
async def get_state():
    """Returns the current consciousness state of the AI."""
    logger.info("Request received for /state endpoint.")
    return await get_real_consciousness_state()

@app.get("/emotions", response_model=MarketEmotions)
async def get_emotions():
    """Returns the current analysis of market emotions."""
    logger.info("Request received for /emotions endpoint.")
    return await get_real_market_emotions()

# --- Auto-registration with MCP Registry ---
@app.on_event("startup")
async def startup_event():
    """Auto-register with MCP registry on startup with retry."""
    registry_url = os.environ.get("REGISTRY_URL", "http://mcp-registry:3001")
    port = int(os.getenv("PORT", 3600))
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{registry_url}/api/servers/register",
                    json={
                        "name": "consciousness-layer",
                        "url": f"http://mcp-consciousness-layer:{port}",
                        "capabilities": [
                            "consciousness_state",
                            "market_emotions",
                            "system_awareness",
                            "cognitive_monitoring",
                        ],
                        "metadata": {
                            "version": "1.0.0",
                            "type": "consciousness",
                            "description": "AI-driven consciousness state and market emotion analysis",
                        },
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    logger.info("✅ Consciousness Layer registered with MCP registry")
                    return
        except Exception as e:
            logger.warning(f"Registry registration attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
    logger.error("❌ Failed to register with MCP registry after all retries")


# --- Main Execution Block ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    logger.info(f"Starting MCP Consciousness Layer server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
