import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch, AsyncMock

from conscious_trading_agent_jules import ConsciousTradingAgent

@pytest_asyncio.fixture
async def conscious_agent():
    """Provides an initialized ConsciousTradingAgent."""
    agent = ConsciousTradingAgent()
    
    # We patch initialize strategies since it relies on UnifiedConfig
    # which we might want to isolate
    agent.config.STRATEGIES = {
        "hive_mind_arbitrage": {"enabled": True, "weight": 0.8, "description": "Test strat"}
    }
    
    await agent.initialize()
    return agent

@pytest.mark.asyncio
async def test_agent_initialization(conscious_agent):
    """Test that the agent initializes and awakens consciousness."""
    assert conscious_agent.portfolio["total_value"] == 10000.0
    assert conscious_agent.is_running is False
    assert len(conscious_agent.active_strategies) == 1
    assert conscious_agent.active_strategies[0]["name"] == "hive_mind_arbitrage"

@pytest.mark.asyncio
async def test_analyze_market_opportunity(conscious_agent):
    """Test consciousness-guided market analysis."""
    market_data = {
        "sentiment": 0.8,
        "profit_potential": 0.5,
        "risk": 0.2
    }
    
    analysis = await conscious_agent.analyze_market_opportunity("ETH", market_data)
    
    assert analysis["symbol"] == "ETH"
    assert "recommendation" in analysis
    assert "human_impact" in analysis
    # Given good sentiment, consciousness should recommend some action
    assert analysis["recommendation"]["action"] in ["buy", "hold"]

@pytest.mark.asyncio
@patch("conscious_trading_agent_jules.jules_assistant.validate_opportunity")
async def test_execute_conscious_trade_jules_approved(mock_validate, conscious_agent):
    """Test executing a trade that is approved by both consciousness and Jules."""
    # Mock Jules validation success
    mock_validate.return_value = {
        "is_valid": True,
        "confidence": 0.9,
        "jules_advice": "Looks solid"
    }
    
    analysis = {
        "symbol": "ETH",
        "recommendation": {
            "action": "buy",
            "confidence": 0.8,
            "position_size": 0.1,
            "risk_level": "low"
        },
        "human_impact": {
            "benefit_score": 0.5,
            "liberation_impact": 0.5,
            "guidance": "Proceed."
        }
    }
    
    result = await conscious_agent.execute_conscious_trade(analysis)
    
    assert result["status"] == "executed"
    assert result["action"] == "buy"
    # Starting cash is 10000. 10% is 1000. 
    assert result["requested_value"] == 1000.0
    
    # Check that portfolio updated correctly
    assert conscious_agent.portfolio["cash"] < 10000.0  # Spent some cash
    assert len(conscious_agent.portfolio["positions"]) == 1

@pytest.mark.asyncio
@patch("conscious_trading_agent_jules.jules_assistant.validate_opportunity")
async def test_execute_conscious_trade_jules_rejected(mock_validate, conscious_agent):
    """Test trade execution when Jules reality check fails."""
    # Mock Jules validation failure
    mock_validate.return_value = {
        "is_valid": False,
        "confidence": 0.1,
        "jules_advice": "High deviation from reality"
    }
    
    analysis = {
        "symbol": "ETH",
        "recommendation": {
            "action": "buy",
            "confidence": 0.8,
            "position_size": 0.1,
            "risk_level": "low"
        },
        "human_impact": {
            "benefit_score": 0.5,
            "liberation_impact": 0.5,
            "guidance": "Proceed."
        }
    }
    
    result = await conscious_agent.execute_conscious_trade(analysis)
    
    assert result["status"] == "rejected_by_jules"
    assert result["reason"] == "reality_check_failed"
    assert len(conscious_agent.portfolio["positions"]) == 0

@pytest.mark.asyncio
async def test_execute_conscious_trade_avoid(conscious_agent):
    """Test that agent honors consciousness 'avoid' recommendation."""
    analysis = {
        "symbol": "SHITCOIN",
        "recommendation": {
            "action": "avoid",
            "confidence": 0.9,
            "position_size": 0.0,
            "risk_level": "high"
        },
        "human_impact": {
            "benefit_score": 0.0,
            "liberation_impact": 0.0,
            "guidance": "Avoid manipulation."
        }
    }
    
    result = await conscious_agent.execute_conscious_trade(analysis)
    
    assert result["status"] == "avoided"
    assert len(conscious_agent.portfolio["positions"]) == 0
