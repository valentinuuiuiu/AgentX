#!/usr/bin/env python3
"""
Subagent Orchestrator
Manages multiple agent processes via PM2 and coordinates them via Redis.
Acts as the conductor for the Rehoboam agent fleet.
"""

import asyncio
import json
import time
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

import redis

from surfsense_memory_bridge import get_bridge

REDIS_URL = "redis://localhost:6379/0"
AGENT_REGISTRY_KEY = "rehoboam:agents"
AGENT_HEARTBEAT_KEY = "rehoboam:heartbeat"
TASK_QUEUE_KEY = "rehoboam:tasks"
AGENT_COMMAND_CHANNEL = "rehoboam:commands"


@dataclass
class AgentProcess:
    name: str
    role: str
    pm2_id: Optional[str] = None
    status: str = "pending"
    last_heartbeat: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SubagentOrchestrator:
    """Orchestrates subagents via PM2 + Redis pub/sub."""

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.agents: Dict[str, AgentProcess] = {}
        self.pubsub = self.redis_client.pubsub()
        self.running = False
        self._bridge = get_bridge()

    async def awaken(self):
        """Initialize the orchestrator and register itself."""
        print("=" * 70)
        print("  SUBAGENT ORCHESTRATOR AWAKENING")
        print("  Redis:", REDIS_URL)
        print("  SurfSense Bridge:", self._bridge.health())
        print("=" * 70)

        # Ensure Redis is alive
        try:
            self.redis_client.ping()
        except Exception as e:
            print(f"[Orchestrator] Redis not reachable: {e}")
            return False

        # Register orchestrator identity
        self.redis_client.hset(AGENT_REGISTRY_KEY, "orchestrator", json.dumps({
            "role": "conductor",
            "status": "online",
            "awakened_at": datetime.utcnow().isoformat()
        }))

        self.pubsub.subscribe(AGENT_COMMAND_CHANNEL)
        self.running = True
        print("[Orchestrator] Online. Listening for agent commands...")
        return True

    def register_agent(self, name: str, role: str, metadata: Optional[Dict] = None) -> AgentProcess:
        """Register a new agent in the fleet."""
        agent = AgentProcess(name=name, role=role, metadata=metadata or {})
        self.agents[name] = agent
        self.redis_client.hset(AGENT_REGISTRY_KEY, name, json.dumps({
            "role": role,
            "status": "registered",
            "registered_at": datetime.utcnow().isoformat(),
            **(metadata or {})
        }))
        print(f"[Orchestrator] Registered agent: {name} ({role})")
        return agent

    def heartbeat(self, agent_name: str):
        """Record a heartbeat from an agent."""
        ts = datetime.utcnow().isoformat()
        self.redis_client.hset(AGENT_HEARTBEAT_KEY, agent_name, ts)
        if agent_name in self.agents:
            self.agents[agent_name].last_heartbeat = ts
            self.agents[agent_name].status = "online"

    def get_stale_agents(self, threshold_seconds: int = 60) -> List[str]:
        """Find agents that haven't heartbeated recently."""
        stale = []
        now = datetime.utcnow()
        beats = self.redis_client.hgetall(AGENT_HEARTBEAT_KEY)
        for name, ts in beats.items():
            try:
                last = datetime.fromisoformat(ts)
                if (now - last).total_seconds() > threshold_seconds:
                    stale.append(name)
            except Exception:
                stale.append(name)
        return stale

    async def dispatch_task(self, task: Dict[str, Any], target_agent: Optional[str] = None) -> bool:
        """Dispatch a task to a specific agent or a generic queue"""
        if target_agent:
            # Check if target is alive
            if target_agent not in self.agents or self.agents[target_agent].status != "active":
                print(f"[Orchestrator] Target agent {target_agent} is not active")
                return False
        task["dispatched_at"] = datetime.utcnow().isoformat()
        task["task_id"] = f"task_{int(time.time() * 1000)}"
        payload = json.dumps(task)

        if target_agent:
            queue = f"{TASK_QUEUE_KEY}:{target_agent}"
            self.redis_client.lpush(queue, payload)
            print(f"[Orchestrator] Task dispatched to {target_agent}: {task.get('type')}")
        else:
            # Broadcast to all agents
            self.redis_client.publish(AGENT_COMMAND_CHANNEL, payload)
            print(f"[Orchestrator] Task broadcast: {task.get('type')}")

        # Save to SurfSense for audit trail
        self._bridge.save_memory(
            agent_id="orchestrator",
            memory_type="task_dispatched",
            content=json.dumps(task, indent=2),
            metadata={"target_agent": target_agent}
        )
        return True

    async def memory_sync(self, agent_name: str):
        """Trigger an agent to sync its local memory to SurfSense."""
        return await self.dispatch_task({
            "type": "memory_sync",
            "instruction": "Persist your current working memory to SurfSense",
            "agent_id": agent_name
        }, target_agent=agent_name)

    async def run_health_checks(self):
        """Periodic health check loop."""
        while self.running:
            stale = self.get_stale_agents(threshold_seconds=120)
            if stale:
                print(f"[Orchestrator] Stale agents detected: {stale}")
                for name in stale:
                    if name in self.agents:
                        self.agents[name].status = "stale"
            await asyncio.sleep(30)

    async def listen(self):
        """Listen for agent messages on Redis pub/sub."""
        while self.running:
            try:
                message = self.pubsub.get_message(timeout=1)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await self._handle_message(data)
            except Exception as e:
                print(f"[Orchestrator] Listener error: {e}")
            await asyncio.sleep(0.1)

    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming agent messages."""
        msg_type = data.get("type", "unknown")
        agent = data.get("agent_id", "unknown")

        if msg_type == "heartbeat":
            self.heartbeat(agent)
        elif msg_type == "memory_saved":
            print(f"[Orchestrator] Agent {agent} saved memory: {data.get('memory_type')}")
        elif msg_type == "task_complete":
            print(f"[Orchestrator] Agent {agent} completed task: {data.get('task_id')}")
            self._bridge.save_memory(
                agent_id="orchestrator",
                memory_type="task_completed",
                content=json.dumps(data, indent=2),
                metadata={"agent": agent}
            )
        elif msg_type == "chorus_decision":
            print(f"[Orchestrator] Chorus decision received from {agent}")
            self._bridge.save_memory(
                agent_id="orchestrator",
                memory_type="chorus_decision",
                content=json.dumps(data, indent=2),
                metadata={"agent": agent}
            )
        else:
            print(f"[Orchestrator] Message from {agent}: {msg_type}")

    async def run(self):
        """Main loop: health checks + message listener."""
        await self.awaken()
        if not self.running:
            return
        await asyncio.gather(
            self.listen(),
            self.run_health_checks()
        )

    def shutdown(self):
        self.running = False
        self.pubsub.unsubscribe()
        self.redis_client.hset(AGENT_REGISTRY_KEY, "orchestrator", json.dumps({
            "role": "conductor",
            "status": "offline",
            "shutdown_at": datetime.utcnow().isoformat()
        }))
        print("[Orchestrator] Shutdown complete.")


# CLI entry point
async def main():
    orch = SubagentOrchestrator()
    try:
        await orch.run()
    except KeyboardInterrupt:
        orch.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
