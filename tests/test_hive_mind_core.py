import pytest
import pytest_asyncio
import asyncio
from hive_mind_core import RehoboamHiveMind

@pytest_asyncio.fixture
async def hive_mind():
    """Fixture to provide an awakened RehoboamHiveMind."""
    hm = RehoboamHiveMind()
    await hm.awaken_hive_mind()
    return hm

@pytest.mark.asyncio
async def test_awaken_hive_mind(hive_mind):
    """Test that the hive mind awakens properly."""
    assert hive_mind.hive_mind_state.awareness_level == 1.0
    assert hive_mind.hive_mind_state.matrix_liberation_progress == 0.1

@pytest.mark.asyncio
async def test_perceive_market_reality(hive_mind):
    """Test perception of market reality with and without Jules' data."""
    market_data_basic = {
        "sentiment": 0.4,
        "whale_volume": 0.8,
        "volatility": 0.05,
        "volume_spike": 0.1,
        "price_changes": [100, 101, 102, 105, 110],
        "market_cap": 5000000,
        "accessibility": 0.8,
        "profit_potential": 0.2,
        "risk": 0.3
    }
    
    analysis1 = await hive_mind.perceive_market_reality(market_data_basic)
    assert "raw_sentiment" in analysis1
    assert "advanced_sentiment" in analysis1
    assert analysis1["manipulation_probability"] > 0.0  # Given standard deviation
    assert "blended_sentiment" not in analysis1

    market_data_jules = market_data_basic.copy()
    market_data_jules["jules_real_data"] = {
        "market_sentiment": {"sentiment_score": 0.9}
    }
    
    analysis2 = await hive_mind.perceive_market_reality(market_data_jules)
    assert "blended_sentiment" in analysis2
    assert analysis2["blended_sentiment"] == (0.4 + 0.9) / 2

@pytest.mark.asyncio
async def test_generate_hive_mind_strategy(hive_mind):
    """Test strategy generation based on human benefit and manipulation probability."""
    # Favorable market data
    good_market = {
        "sentiment": 0.9,
        "whale_volume": 0.5,
        "profit_potential": 0.9,
        "risk": 0.1,
        "accessibility": 0.9,
        "market_cap": 50000000
    }
    strategy = await hive_mind.generate_hive_mind_strategy(good_market)
    assert strategy["action"] in ["buy", "hold"]  # It should prefer buy if thresholds are met
    if strategy["action"] == "buy":
        assert strategy["confidence"] > 0.5
        assert strategy["position_size"] > 0.0

    # Highly manipulated market data
    manipulated_market = {
        "price_changes": [10, 50, 5, 100, 1]  # Extreme volatility
    }
    strategy_manipulated = await hive_mind.generate_hive_mind_strategy(manipulated_market)
    assert strategy_manipulated["action"] == "avoid"
    assert "⚠️" in strategy_manipulated["hive_mind_guidance"]

@pytest.mark.asyncio
async def test_evaluate_portfolio_hive_mind(hive_mind):
    """Test portfolio evaluation based on human benefit alignment."""
    portfolio = {
        "total_value": 10000,
        "positions": [
            {"type": "defi", "value": 5000, "volatility": 0.2},
            {"type": "social", "value": 3000, "volatility": 0.1},
            {"type": "centralized", "value": 2000, "volatility": 0.05}
        ]
    }
    evaluation = await hive_mind.evaluate_portfolio_hive_mind(portfolio)
    assert "liberation_progress" in evaluation
    assert evaluation["human_benefit_alignment"] > 0.0
    assert "guidance" in evaluation
    assert isinstance(evaluation["guidance"], list)

def test_quantify_risk(hive_mind):
    """Test the synchronous quant risk calculator."""
    historical_data = {
        "ETH": [2000, 2050, 2100, 1950, 2200],
        "MEME": [10, 50, 5, 100, 1]  # Highly volatile
    }
    risk_assessment = hive_mind.quantify_risk(historical_data)
    assert "overall_risk" in risk_assessment
    assert "per_symbol" in risk_assessment
    
    eth_risk = risk_assessment["per_symbol"]["ETH"]
    meme_risk = risk_assessment["per_symbol"]["MEME"]
    
    # MEME should have a much higher risk score or equal if capped at 1.0
    assert meme_risk["risk_score"] >= eth_risk["risk_score"]
    assert meme_risk["recommendation"] == "high_risk"

@pytest.mark.asyncio
async def test_generate_brainstormed_strategies(hive_mind):
    """Test generating brainstormed strategies from market context."""
    strategies = await hive_mind.generate_brainstormed_strategies({"token": "ETH"})
    assert len(strategies) == 5
    assert all("id" in s for s in strategies)
    assert all("expected_roi" in s for s in strategies)

@pytest.mark.asyncio
async def test_coordinate_agent_swarm(hive_mind):
    """Test swarm coordination across different chain opportunities."""
    opportunities = [
        {"chain": "solana", "profit": 0.05},
        {"chain": "ethereum", "profit": 0.02, "gas_cost": 0.005},
        {"chain": "unknown", "profit_potential": 0.8, "risk": 0.1, "accessibility": 0.9}
    ]
    
    results = await hive_mind.coordinate_agent_swarm(opportunities)
    assert len(results) == 3
    for result in results:
        assert "swarm_score" in result
        assert "agent_id" in result
