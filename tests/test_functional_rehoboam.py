import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from rehoboam_unified_system import RehoboamUnifiedSystem
from utils.bot_orchestrator import bot_orchestrator, BotMode
from utils.arbitrage_service import arbitrage_service

@pytest_asyncio.fixture
async def rehoboam_system():
    system = RehoboamUnifiedSystem()
    # Mock initialize to avoid needing a real network connection or long delays
    success = await system.initialize()
    yield system
    # Cleanup if needed

@pytest.mark.asyncio
async def test_rehoboam_initialization(rehoboam_system):
    """Test that the system initializes correctly and sets up bots."""
    assert rehoboam_system.initialized is True
    assert rehoboam_system.system_metrics["start_time"] is not None
    
    # Check if bots are running via status
    status = await rehoboam_system.get_system_status()
    assert status.rehoboam_active is True
    # If the mocked arbitrage service returns active bots, this might be > 0
    assert isinstance(status.active_bots, int)

@pytest.mark.asyncio
async def test_process_opportunity(rehoboam_system):
    """Test processing a structured arbitrage opportunity."""
    test_opportunity = {
        "token_pair": "ETH/USDC",
        "source_exchange": "Uniswap",
        "target_exchange": "SushiSwap",
        "price_difference": 0.02,
        "net_profit_usd": 50.0,
        "gas_cost_usd": 5.0,
        "risk_score": 0.3
    }
    
    result = await rehoboam_system.process_opportunity(test_opportunity)
    
    assert result is not None
    assert "success" in result
    assert "system_context" in result
    assert result["system_context"]["processed_by"] == "rehoboam_unified_system"
    assert rehoboam_system.system_metrics["opportunities_processed"] > 0

@pytest.mark.asyncio
async def test_bot_mode_configuration(rehoboam_system):
    """Test changing a bot's mode."""
    # Assuming bot_orchestrator returns some bots
    orchestrator_status = await bot_orchestrator.get_orchestration_status()
    active_bots = orchestrator_status.get("active_bots", [])
    
    if active_bots:
        bot_id = active_bots[0]
        # Change mode to AUTONOMOUS
        success = await rehoboam_system.configure_bot_mode(bot_id, "autonomous")
        assert success is True
        
        # Change mode back to MANUAL
        success = await rehoboam_system.configure_bot_mode(bot_id, "manual")
        assert success is True

@pytest.mark.asyncio
async def test_detailed_metrics(rehoboam_system):
    """Test the detailed metrics generation."""
    metrics = await rehoboam_system.get_detailed_metrics()
    
    assert "timestamp" in metrics
    assert "system_metrics" in metrics
    assert "uptime" in metrics
    assert "success_rate" in metrics
    assert "hive_mind_score" in metrics
