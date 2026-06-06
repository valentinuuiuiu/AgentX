"""Main application entry point."""
import asyncio
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:5001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-initialized platform state
_platform_state = None


async def init_platform():
    """Initialize the trading platform."""
    global _platform_state
    try:
        from trading_platform.state import State
        from utils.websocket_server import EnhancedWebSocketServer
        ws_server = EnhancedWebSocketServer()
        state = State(ws_server)
        await state.initialize()
        return state
    except Exception as e:
        logger.warning(f"Platform init skipped (missing deps): {e}")
        return None


@app.on_event("startup")
async def startup_event():
    """Initialize application state on startup."""
    global _platform_state
    _platform_state = await init_platform()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    global _platform_state
    if _platform_state and hasattr(_platform_state, 'cleanup'):
        await _platform_state.cleanup()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )