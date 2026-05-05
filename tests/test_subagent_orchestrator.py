import pytest
import sys
import json
import asyncio
from unittest.mock import patch, MagicMock

sys.modules['surfsense_memory_bridge'] = MagicMock()
from surfsense_memory_bridge import get_bridge

sys.path.append('agents')
from subagent_orchestrator import SubagentOrchestrator, TASK_QUEUE_KEY, AGENT_COMMAND_CHANNEL, AgentProcess

@pytest.fixture
def mock_redis():
    with patch('subagent_orchestrator.redis.from_url') as mock_from_url:
        yield mock_from_url

@pytest.fixture
def orchestrator(mock_redis):
    # Setup mock bridge
    sys.modules['surfsense_memory_bridge'].get_bridge = MagicMock()
    orch = SubagentOrchestrator()
    yield orch

@pytest.mark.asyncio
async def test_dispatch_task_with_active_target_agent(orchestrator):
    orchestrator._bridge.save_memory.reset_mock()
    task = {"type": "test_task"}
    target_agent = "agent_1"

    # Setup active target agent
    orchestrator.agents[target_agent] = AgentProcess(name=target_agent, role="test", status="active")

    result = await orchestrator.dispatch_task(task, target_agent=target_agent)

    assert result is True
    assert "dispatched_at" in task
    assert "task_id" in task

    # Check that redis was called correctly
    queue = f"{TASK_QUEUE_KEY}:{target_agent}"
    orchestrator.redis_client.lpush.assert_called_once()
    args, _ = orchestrator.redis_client.lpush.call_args
    assert args[0] == queue

    payload = json.loads(args[1])
    assert payload["type"] == "test_task"
    assert "dispatched_at" in payload
    assert "task_id" in payload

    # Check that it didn't broadcast
    orchestrator.redis_client.publish.assert_not_called()

    # Check that memory was saved
    orchestrator._bridge.save_memory.assert_called_once()

@pytest.mark.asyncio
async def test_dispatch_task_with_inactive_target_agent(orchestrator):
    orchestrator._bridge.save_memory.reset_mock()
    task = {"type": "test_task"}
    target_agent = "agent_1"

    # Setup inactive target agent
    orchestrator.agents[target_agent] = AgentProcess(name=target_agent, role="test", status="pending")

    result = await orchestrator.dispatch_task(task, target_agent=target_agent)

    assert result is False
    assert "dispatched_at" not in task
    assert "task_id" not in task

    # Check that redis was not called
    orchestrator.redis_client.lpush.assert_not_called()
    orchestrator.redis_client.publish.assert_not_called()

    # Check that memory was not saved
    orchestrator._bridge.save_memory.assert_not_called()

@pytest.mark.asyncio
async def test_dispatch_task_with_unknown_target_agent(orchestrator):
    orchestrator._bridge.save_memory.reset_mock()
    task = {"type": "test_task"}
    target_agent = "unknown_agent"

    result = await orchestrator.dispatch_task(task, target_agent=target_agent)

    assert result is False
    assert "dispatched_at" not in task
    assert "task_id" not in task

    # Check that redis was not called
    orchestrator.redis_client.lpush.assert_not_called()
    orchestrator.redis_client.publish.assert_not_called()

    # Check that memory was not saved
    orchestrator._bridge.save_memory.assert_not_called()

@pytest.mark.asyncio
async def test_dispatch_task_broadcast(orchestrator):
    # Reset mock since orchestrator fixture creates a new instance but mock might be shared
    orchestrator._bridge.save_memory.reset_mock()

    task = {"type": "broadcast_task"}

    result = await orchestrator.dispatch_task(task)

    assert result is True
    assert "dispatched_at" in task
    assert "task_id" in task

    # Check that it broadcasted to all agents
    orchestrator.redis_client.publish.assert_called_once()
    args, _ = orchestrator.redis_client.publish.call_args
    assert args[0] == AGENT_COMMAND_CHANNEL

    payload = json.loads(args[1])
    assert payload["type"] == "broadcast_task"

    # Check that it didn't push to a specific queue
    orchestrator.redis_client.lpush.assert_not_called()

    # Check that memory was saved
    orchestrator._bridge.save_memory.assert_called_once()
