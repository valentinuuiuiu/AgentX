from pydantic import BaseModel
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
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body
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
