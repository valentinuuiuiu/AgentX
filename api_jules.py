"""
Jules API Router - The Voice of Reality
=======================================

Provides endpoints for Rehoboam to access real-world data and
strategic guidance from the Jules AI Assistant.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from jules_real_data_provider import jules_assistant
from utils.user_management import get_current_user

logger = logging.getLogger("API_Jules")

router = APIRouter(prefix="/api/jules", tags=["jules"])

@router.get("/reality-check/{symbol}")
async def get_reality_check(symbol: str, network: str = "ethereum"):
    """
    Get a real-world data validation for a specific token.
    """
    try:
        reality_data = await jules_assistant.get_reality_check(symbol, network)
        return {
            "status": "success",
            "data": reality_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in Jules reality check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-trade")
async def validate_trade(opportunity: Dict[str, Any]):
    """
    Validate a trade opportunity against real-world data.
    """
    try:
        validation = await jules_assistant.validate_opportunity(opportunity)
        return {
            "status": "success",
            "validation": validation,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error validating trade with Jules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment/{symbol}")
async def get_jules_sentiment(symbol: str):
    """
    Get Jules' real-time sentiment analysis for a token.
    """
    try:
        sentiment = await jules_assistant._get_real_sentiment(symbol)
        return {
            "status": "success",
            "sentiment": sentiment,
            "symbol": symbol
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_jules_metrics():
    """
    Get performance metrics for the Jules Real-Data Provider.
    """
    return {
        "status": "success",
        "metrics": jules_assistant.reality_metrics
    }
