import pytest
import asyncio
from jules_real_data_provider import jules_assistant
from conscious_trading_agent_jules import ConsciousTradingAgent

@pytest.mark.asyncio
async def test_jules_reality_check():
    """Test that Jules can fetch real data for ETH"""
    reality = await jules_assistant.get_reality_check("ETH")
    assert reality["is_real_data"] is True
    assert reality["symbol"] == "ETH"
    assert reality["real_price"] > 0
    assert "market_sentiment" in reality

@pytest.mark.asyncio
async def test_jules_validation_logic():
    """Test the validation logic rejects high deviations"""
    # Create an opportunity with a fake price
    opp = {
        "symbol": "ETH",
        "price": 100.0, # Reality is ~3000
        "token_pair": "ETH/USDC",
        "network": "ethereum"
    }

    validation = await jules_assistant.validate_opportunity(opp)
    assert validation["is_valid"] is False
    assert "High deviation" in validation["jules_advice"]

@pytest.mark.asyncio
async def test_jules_sentiment_fallback():
    """Test that sentiment fetching works or falls back gracefully"""
    sentiment = await jules_assistant._get_real_sentiment("BTC")
    assert "dominant_sentiment" in sentiment
    assert 0 <= sentiment["sentiment_score"] <= 1
