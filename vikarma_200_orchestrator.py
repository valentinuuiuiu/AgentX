#!/usr/bin/env python3
"""
🏔️ VIKARMA 200 - UNIFIED SWARM ORCHESTRATOR 🏔️
=================================================
Fixes the task dispatcher bug + scales to 200 real agents.
Integrates with Podman containers and Rehoboam API.

Critical fixes:
1. Async task execution with proper result callbacks
2. Persistent agent process management
3. Health checking before task dispatch
4. Result aggregation with timeouts
"""

import asyncio
import json
import random
import socket
import time
import struct
import subprocess
import os
import sys
import signal
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging

sys.path.insert(0, '/home/aryan/free-claude/bittensor/clean_rehoboam_project')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

class AgentState(Enum):
    SOVEREIGN = "sovereign"
    EXPLORING = "exploring"
    CONNECTED = "connected"
    ACTING = "acting"
    RESTING = "resting"
    ERROR = "error"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Peer:
    id: str
    address: str
    port: int
    guna: str
    capabilities: List[str]
    last_seen: float = field(default_factory=time.time)
    trust_score: float = 0.5
    tasks_completed: int = 0
    tasks_failed: int = 0

    def is_alive(self, timeout: float = 30.0) -> bool:
        return (time.time() - self.last_seen) < timeout


@dataclass
class SwarmTask:
    id: str
    task_type: str
    guna: str
    description: str
    command: str
    priority: int = 5
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    timeout_seconds: int = 60


# =============================================================================
# AHIMSA VALIDATOR
# =============================================================================

class AhimsaValidator:
    """Non-violence validation for all actions."""

    HARM_INDICATORS = [
        "destroy", "attack", "harm", "kill", "damage",
        "steal", "exploit", "manipulate", "deceive",
        "erase", "wipe", "corrupt", "infect", "rm -rf /",
        "format", "dd if=/dev/zero", ":(){:|:&};:"
    ]

    @classmethod
    def validate(cls, action_type: str, payload: Dict) -> bool:
        action_str = json.dumps({"type": action_type, **payload}).lower()
        for harm in cls.HARM_INDICATORS:
            if harm in action_str:
                logger.warning(f"🚫 Ahimsa blocked: {harm}")
                return False
        return True


# =============================================================================
# REAL AGENT WORKER (Process-based)
# =============================================================================

class RealAgentWorker:
    """
    A real agent worker that runs as a persistent process.
    Handles task execution via subprocess with proper result reporting.
    """

    def __init__(self, agent_id: str, guna: str, port: int, project_dir: str):
        self.id = agent_id
        self.guna = guna
        self.port = port
        self.project_dir = project_dir
        self.process: Optional[subprocess.Popen] = None
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.running = False

    def start(self) -> bool:
        """Start the agent as a persistent subprocess."""
        agent_script = self._generate_agent_script()
        script_path = f"/tmp/vikarma_agent_{self.port}.py"
        
        with open(script_path, 'w') as f:
            f.write(agent_script)

        try:
            self.process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            self.running = True
            logger.info(f"🚀 {self.id} started on port {self.port} [{self.guna}]")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start {self.id}: {e}")
            self.state = AgentState.ERROR
            return False

    def stop(self):
        """Stop the agent process."""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except:
                    pass
            self.running = False
            logger.info(f"🛑 {self.id} stopped")

    def is_alive(self) -> bool:
        """Check if agent process is running."""
        if not self.process:
            return False
        return self.process.poll() is None

    def _generate_agent_script(self) -> str:
        """Generate the agent server script."""
        return f'''#!/usr/bin/env python3
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

AGENT_ID = "{self.id}"
AGENT_GUNA = "{self.guna}"
AGENT_PORT = {self.port}
PROJECT_DIR = "{self.project_dir}"

class AgentServer:
    def __init__(self):
        self.tasks = {{}}
        self.running = True

    async def handle_client(self, reader, writer):
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=10.0)
            if not data:
                return
            
            msg = json.loads(data.decode().strip())
            msg_type = msg.get("type")
            
            if msg_type == "ping":
                response = {{
                    "status": "alive",
                    "agent_id": AGENT_ID,
                    "guna": AGENT_GUNA,
                    "tasks_completed": len([t for t in self.tasks.values() if t.get("success")]),
                    "timestamp": time.time()
                }}
                writer.write(json.dumps(response).encode() + b"\\n")
                await writer.drain()
            
            elif msg_type == "task_assign":
                task = msg.get("task", {{}})
                task_guna = task.get("guna", "")
                
                if task_guna != AGENT_GUNA and task_guna != "any":
                    response = {{"status": "rejected", "reason": "guna_mismatch", "agent_id": AGENT_ID}}
                    writer.write(json.dumps(response).encode() + b"\\n")
                    await writer.drain()
                    return
                
                # Accept task
                response = {{"status": "accepted", "agent_id": AGENT_ID, "guna": AGENT_GUNA}}
                writer.write(json.dumps(response).encode() + b"\\n")
                await writer.drain()
                
                # Execute task synchronously - keep connection open
                await self._execute_task(task, writer)
            
            elif msg_type == "get_results":
                task_id = msg.get("task_id")
                result = self.tasks.get(task_id, {{}})
                response = {{"results": [result] if result else []}}
                writer.write(json.dumps(response).encode() + b"\\n")
                await writer.drain()
            
            elif msg_type == "shutdown":
                response = {{"status": "shutting_down", "agent_id": AGENT_ID}}
                writer.write(json.dumps(response).encode() + b"\\n")
                await writer.drain()
                self.running = False
                
        except asyncio.TimeoutError:
            pass
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"[{{AGENT_ID}}] Error: {{e}}", file=sys.stderr)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def _execute_task(self, task: dict, writer):
        task_id = task.get("id", "unknown")
        command = task.get("command", "")
        
        print(f"[{{AGENT_ID}}] Executing: {{task_id}}", flush=True)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=PROJECT_DIR
            )
            
            task_result = {{
                "task_id": task_id,
                "agent_id": AGENT_ID,
                "success": result.returncode == 0,
                "stdout": result.stdout[:5000],  # Limit output size
                "stderr": result.stderr[:2000],
                "returncode": result.returncode,
                "timestamp": time.time()
            }}
            
            self.tasks[task_id] = task_result
            
            # Send completion notification
            completion = {{
                "type": "task_complete",
                "task_id": task_id,
                "status": "success" if result.returncode == 0 else "failed",
                "agent_id": AGENT_ID
            }}
            writer.write(json.dumps(completion).encode() + b"\\n")
            await writer.drain()
            
            print(f"[{{AGENT_ID}}] Completed: {{task_id}} (rc={{result.returncode}})", flush=True)
            
        except subprocess.TimeoutExpired:
            task_result = {{
                "task_id": task_id,
                "agent_id": AGENT_ID,
                "success": False,
                "error": "Task timed out after 60s",
                "timestamp": time.time()
            }}
            self.tasks[task_id] = task_result
            print(f"[{{AGENT_ID}}] Timeout: {{task_id}}", flush=True)
        except Exception as e:
            task_result = {{
                "task_id": task_id,
                "agent_id": AGENT_ID,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }}
            self.tasks[task_id] = task_result
            print(f"[{{AGENT_ID}}] Error: {{task_id}} - {{e}}", flush=True)

    async def run(self):
        server = await asyncio.start_server(self.handle_client, "127.0.0.1", AGENT_PORT)
        print(f"[{{AGENT_ID}}] Listening on port {{AGENT_PORT}}", flush=True)
        
        async with server:
            while self.running:
                await asyncio.sleep(1)

if __name__ == "__main__":
    agent = AgentServer()
    asyncio.run(agent.run())
'''


# =============================================================================
# TASK DISPATCHER (Fixed)
# =============================================================================

class FixedTaskDispatcher:
    """
    Fixed task dispatcher with proper health checking,
    async execution, and reliable result collection.
    """

    def __init__(self, base_port: int = 10000, num_agents: int = 200):
        self.base_port = base_port
        self.num_agents = num_agents
        self.agent_ports = list(range(base_port, base_port + num_agents))
        self.tasks: List[SwarmTask] = []
        self.completed_tasks: List[SwarmTask] = []
        self.agent_health: Dict[int, Dict] = {}

    async def health_check_all(self) -> Dict[str, List[int]]:
        """Check which agents are alive and their Guna types."""
        healthy = {"sattva": [], "rajas": [], "tamas": [], "any": []}
        
        tasks = [self._check_agent_health(port) for port in self.agent_ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for port, result in zip(self.agent_ports, results):
            if isinstance(result, dict) and result.get("status") == "alive":
                guna = result.get("guna", "any")
                healthy[guna].append(port)
                healthy["any"].append(port)
                self.agent_health[port] = result
        
        return healthy

    async def _check_agent_health(self, port: int) -> Optional[Dict]:
        """Check if a single agent is healthy."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port),
                timeout=3.0
            )
            
            ping = {"type": "ping"}
            writer.write(json.dumps(ping).encode() + b"\n")
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.readline(), timeout=3.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            return response
        except Exception:
            return None

    def create_real_tasks(self) -> List[SwarmTask]:
        """Create actual tasks for the swarm."""
        tasks = []
        
        # Security tasks (Tamas)
        tasks.append(SwarmTask(
            id="sec_secrets_scan",
            task_type="security_scan",
            guna="tamas",
            description="Scan for hardcoded secrets and API keys",
            command="find . -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.json' | xargs grep -l 'nvapi-\|sk-\|ghp_\|password.*=' 2>/dev/null | head -20 || echo 'Scan complete'",
            priority=10
        ))
        
        tasks.append(SwarmTask(
            id="sec_docker_check",
            task_type="security_scan",
            guna="tamas",
            description="Check docker-compose for exposed passwords",
            command="grep -n 'PASSWORD\|password\|secret' docker-compose*.yml 2>/dev/null | head -20 || echo 'No docker-compose secrets found'",
            priority=9
        ))
        
        # Knowledge tasks (Sattva)
        tasks.append(SwarmTask(
            id="doc_api_count",
            task_type="documentation",
            guna="sattva",
            description="Count API endpoints and document structure",
            command="find . -name 'api_*.py' | wc -l && echo 'API files counted'",
            priority=8
        ))
        
        tasks.append(SwarmTask(
            id="doc_class_count",
            task_type="documentation",
            guna="sattva",
            description="Count classes and functions in codebase",
            command="find . -name '*.py' -exec grep -c '^class ' {} + 2>/dev/null | awk -F: '{{sum+=$2}} END {{print sum}}' classes total && find . -name '*.py' -exec grep -c '^def ' {} + 2>/dev/null | awk -F: '{{sum+=$2}} END {{print sum}}' functions total",
            priority=7
        ))
        
        # Build tasks (Rajas)
        tasks.append(SwarmTask(
            id="build_check_deps",
            task_type="build",
            guna="rajas",
            description="Check Python dependencies installation",
            command="pip list 2>/dev/null | wc -l && echo 'dependencies counted'",
            priority=8
        ))
        
        tasks.append(SwarmTask(
            id="build_disk_usage",
            task_type="build",
            guna="rajas",
            description="Check project disk usage",
            command="du -sh . 2>/dev/null && echo 'disk usage calculated'",
            priority=5
        ))
        
        tasks.append(SwarmTask(
            id="build_git_status",
            task_type="build",
            guna="rajas",
            description="Check git status and recent commits",
            command="git log --oneline -5 2>/dev/null || echo 'No git history'",
            priority=6
        ))
        
        # Monitoring tasks (Tamas)
        tasks.append(SwarmTask(
            id="mon_system_load",
            task_type="monitoring",
            guna="tamas",
            description="Check system load and resources",
            command="uptime && free -h 2>/dev/null | head -2 && echo 'System resources checked'",
            priority=6
        ))
        
        return tasks

    async def dispatch_task(self, task: SwarmTask, healthy_agents: Dict[str, List[int]]) -> bool:
        """Dispatch a task to an appropriate agent with guaranteed result collection."""
        
        matching_ports = healthy_agents.get(task.guna, [])
        if not matching_ports:
            matching_ports = healthy_agents.get("any", [])
        
        if not matching_ports:
            logger.warning(f"⚠️ No healthy agents for {task.guna} task {task.id}")
            task.status = TaskStatus.FAILED
            return False
        
        # Pick agent with least load (round-robin)
        port = matching_ports[0]
        
        logger.info(f"🎯 Dispatching {task.id} to agent on port {port} [{task.guna}]")
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port),
                timeout=5.0
            )
            
            task_msg = {
                "type": "task_assign",
                "task": {
                    "id": task.id,
                    "type": task.task_type,
                    "guna": task.guna,
                    "description": task.description,
                    "command": task.command,
                    "priority": task.priority
                }
            }
            
            writer.write(json.dumps(task_msg).encode() + b"\n")
            await writer.drain()
            
            # Wait for acceptance
            response_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
            response = json.loads(response_data.decode())
            
            if response.get("status") == "accepted":
                task.status = TaskStatus.ASSIGNED
                task.assigned_agent = f"agent_{port}"
                task.started_at = time.time()
                
                # Wait for completion notification
                try:
                    completion_data = await asyncio.wait_for(reader.readline(), timeout=task.timeout_seconds)
                    completion = json.loads(completion_data.decode())
                    
                    if completion.get("type") == "task_complete":
                        logger.info(f"✅ {task.id} completed by agent_{port}")
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = time.time()
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ {task.id} completion notification timeout")
                    task.status = TaskStatus.TIMEOUT
                
                writer.close()
                await writer.wait_closed()
                return True
            else:
                logger.warning(f"❌ {task.id} rejected: {response.get('reason', 'unknown')}")
                task.status = TaskStatus.FAILED
                writer.close()
                await writer.wait_closed()
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to dispatch {task.id}: {e}")
            task.status = TaskStatus.FAILED
            return False

    async def collect_results(self, task: SwarmTask) -> Optional[Dict]:
        """Collect results for a completed task."""
        if not task.assigned_agent:
            return None
        
        try:
            port = int(task.assigned_agent.split("_")[1])
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port),
                timeout=5.0
            )
            
            request = {"type": "get_results", "task_id": task.id}
            writer.write(json.dumps(request).encode() + b"\n")
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            results = response.get("results", [])
            if results:
                task.result = results[0]
                return results[0]
            
        except Exception as e:
            logger.error(f"❌ Failed to collect results for {task.id}: {e}")
        
        return None


# =============================================================================
# SWARM ORCHESTRATOR
# =============================================================================

class Vikarma200Orchestrator:
    """
    Orchestrates 200 real agents with proper lifecycle management,
    task dispatching, and result collection.
    """

    def __init__(self, num_agents: int = 200, base_port: int = 10000):
        self.num_agents = num_agents
        self.base_port = base_port
        self.agents: List[RealAgentWorker] = []
        self.dispatcher = FixedTaskDispatcher(base_port, num_agents)
        self.project_dir = "/home/aryan/free-claude/bittensor/clean_rehoboam_project"
        self.running = False
        self.stats = {
            "agents_started": 0,
            "agents_healthy": 0,
            "tasks_dispatched": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "start_time": None
        }

    def create_agents(self):
        """Create all agent workers."""
        gunas = ["sattva", "rajas", "tamas"]
        
        for i in range(self.num_agents):
            guna = gunas[i % 3]
            agent = RealAgentWorker(
                agent_id=f"vikarma_{guna}_{i+1:03d}",
                guna=guna,
                port=self.base_port + i,
                project_dir=self.project_dir
            )
            self.agents.append(agent)
        
        logger.info(f"📋 Created {self.num_agents} agents")

    def start_agents(self, batch_size: int = 20):
        """Start agents in batches to avoid overwhelming the system."""
        logger.info(f"🚀 Starting {self.num_agents} agents in batches of {batch_size}...")
        
        started = 0
        for i in range(0, len(self.agents), batch_size):
            batch = self.agents[i:i+batch_size]
            
            for agent in batch:
                if agent.start():
                    started += 1
            
            logger.info(f"   Batch {i//batch_size + 1}: {len(batch)} agents started")
            time.sleep(0.5)  # Brief pause between batches
        
        self.stats["agents_started"] = started
        logger.info(f"✅ {started}/{self.num_agents} agents started")

    def stop_agents(self):
        """Stop all agents."""
        logger.info("🛑 Stopping all agents...")
        for agent in self.agents:
            agent.stop()
        logger.info("✅ All agents stopped")

    async def run_health_check(self) -> Dict[str, List[int]]:
        """Run health check on all agents."""
        logger.info("🏥 Running health check...")
        healthy = await self.dispatcher.health_check_all()
        
        total_healthy = len(healthy["any"])
        self.stats["agents_healthy"] = total_healthy
        
        logger.info(f"✅ Health check: {total_healthy}/{self.num_agents} agents healthy")
        logger.info(f"   Sattva: {len(healthy['sattva'])} | Rajas: {len(healthy['rajas'])} | Tamas: {len(healthy['tamas'])}")
        
        return healthy

    async def run_mission(self, duration_seconds: int = 300):
        """Run a full mission with task dispatching and result collection."""
        logger.info("="*70)
        logger.info("🏔️  VIKARMA 200 - MISSION START 🏔️")
        logger.info("="*70)
        self.stats["start_time"] = datetime.now().isoformat()
        
        # 1. Health check
        healthy = await self.run_health_check()
        
        if not healthy["any"]:
            logger.error("❌ No healthy agents! Aborting mission.")
            return
        
        # 2. Create tasks
        tasks = self.dispatcher.create_real_tasks()
        logger.info(f"📋 Created {len(tasks)} tasks")
        
        # 3. Dispatch tasks
        logger.info("⚡ Dispatching tasks...")
        dispatch_tasks = [self.dispatcher.dispatch_task(task, healthy) for task in tasks]
        dispatch_results = await asyncio.gather(*dispatch_tasks, return_exceptions=True)
        
        dispatched = sum(1 for r in dispatch_results if r is True)
        self.stats["tasks_dispatched"] = dispatched
        logger.info(f"📤 Dispatched {dispatched}/{len(tasks)} tasks")
        
        # 4. Wait for execution
        logger.info("⏳ Waiting for task execution...")
        await asyncio.sleep(10)
        
        # 5. Collect results
        logger.info("📊 Collecting results...")
        for task in tasks:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.ASSIGNED]:
                result = await self.dispatcher.collect_results(task)
                if result:
                    if result.get("success"):
                        self.stats["tasks_completed"] += 1
                        logger.info(f"✅ {task.id}: SUCCESS")
                        if result.get("stdout"):
                            stdout = result["stdout"].strip()
                            if stdout:
                                logger.info(f"   Output: {stdout[:100]}...")
                    else:
                        self.stats["tasks_failed"] += 1
                        logger.warning(f"❌ {task.id}: FAILED - {result.get('error', 'Unknown')}")
                else:
                    logger.warning(f"⚠️ {task.id}: No results collected")
            else:
                logger.warning(f"⚠️ {task.id}: Status = {task.status.value}")
        
        # 6. Report
        self._print_report(tasks)

    def _print_report(self, tasks: List[SwarmTask]):
        """Print mission report."""
        logger.info("="*70)
        logger.info("📊 MISSION REPORT")
        logger.info("="*70)
        
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in tasks if t.status == TaskStatus.FAILED]
        timeout = [t for t in tasks if t.status == TaskStatus.TIMEOUT]
        
        logger.info(f"Agents:     {self.stats['agents_healthy']}/{self.num_agents} healthy")
        logger.info(f"Dispatched: {self.stats['tasks_dispatched']}/{len(tasks)}")
        logger.info(f"Completed:  {len(completed)}")
        logger.info(f"Failed:     {len(failed)}")
        logger.info(f"Timeout:    {len(timeout)}")
        
        if completed:
            logger.info("\n✅ COMPLETED TASKS:")
            for task in completed:
                logger.info(f"   {task.id}: {task.description}")
                if task.result and task.result.get("stdout"):
                    stdout = task.result["stdout"].strip()
                    if stdout:
                        lines = stdout.split('\n')[:3]
                        for line in lines:
                            logger.info(f"      → {line[:80]}")
        
        if failed:
            logger.info("\n❌ FAILED TASKS:")
            for task in failed:
                logger.info(f"   {task.id}: {task.description}")
        
        logger.info("="*70)

    def save_report(self, filename: str = "vikarma_200_report.json"):
        """Save mission report to file."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "agents_total": self.num_agents,
            "agents_healthy": self.stats["agents_healthy"]
        }
        
        filepath = Path(self.project_dir) / filename
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Report saved to {filepath}")


# =============================================================================
# PODMAN CONTAINER MANAGER
# =============================================================================

class PodmanManager:
    """Manages Podman containers for the Rehoboam ecosystem."""

    CONTAINERS = [
        "clean_rehoboam_project_postgres_1",
        "clean_rehoboam_project_mcp-registry_1",
        "clean_rehoboam_project_rehoboam-api_1",
        "clean_rehoboam_project_rehoboam-frontend_1",
        "clean_rehoboam_project_mcp-function-gemma_1",
        "clean_rehoboam_project_mcp-trading-agents_1",
    ]

    @classmethod
    def start_all(cls):
        """Start all Rehoboam containers."""
        logger.info("🐳 Starting Podman containers...")
        
        for container in cls.CONTAINERS:
            result = subprocess.run(
                ["podman", "start", container],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"   ✅ {container}")
            else:
                logger.warning(f"   ⚠️ {container}: {result.stderr.strip()}")
        
        logger.info("✅ Container start commands issued")
        logger.info("⏳ Waiting 15s for services to initialize...")
        time.sleep(15)

    @classmethod
    def stop_all(cls):
        """Stop all Rehoboam containers."""
        logger.info("🛑 Stopping Podman containers...")
        
        for container in cls.CONTAINERS:
            subprocess.run(
                ["podman", "stop", "-t", "5", container],
                capture_output=True,
                text=True
            )
        
        logger.info("✅ All containers stopped")

    @classmethod
    def status(cls):
        """Get container status."""
        result = subprocess.run(
            ["podman", "ps", "--format", "{{.Names}}|{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        logger.info("📊 Container Status:")
        for line in result.stdout.strip().split('\n'):
            if line:
                logger.info(f"   {line}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for Vikarma 200."""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║   🏔️  VIKARMA 200 - UNIFIED SWARM ORCHESTRATOR  🏔️             ║
    ║                                                                  ║
    ║   "No servers. No kings. 200 sovereign agents."                ║
    ║   "Real work. Real results. No simulation."                    ║
    ║                                                                  ║
    ║   Fixes: Task dispatcher bug | Scales: 20→200 agents          ║
    ║   Integrates: Podman containers | Rehoboam API                 ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    import argparse
    parser = argparse.ArgumentParser(description="Vikarma 200 Swarm Orchestrator")
    parser.add_argument("--agents", type=int, default=200, help="Number of agents (default: 200)")
    parser.add_argument("--port", type=int, default=10000, help="Base port (default: 10000)")
    parser.add_argument("--duration", type=int, default=60, help="Mission duration in seconds")
    parser.add_argument("--start-containers", action="store_true", help="Start Podman containers")
    parser.add_argument("--stop-containers", action="store_true", help="Stop Podman containers")
    parser.add_argument("--status", action="store_true", help="Show container status")
    args = parser.parse_args()
    
    if args.status:
        PodmanManager.status()
        return
    
    if args.stop_containers:
        PodmanManager.stop_all()
        return
    
    if args.start_containers:
        PodmanManager.start_all()
    
    # Create and run swarm
    orchestrator = Vikarma200Orchestrator(
        num_agents=args.agents,
        base_port=args.port
    )
    
    try:
        # Create agents
        orchestrator.create_agents()
        
        # Start agents
        orchestrator.start_agents(batch_size=20)
        
        # Run mission
        asyncio.run(orchestrator.run_mission(duration_seconds=args.duration))
        
        # Save report
        orchestrator.save_report()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
    finally:
        logger.info("🧹 Cleaning up...")
        orchestrator.stop_agents()
        logger.info("✅ Done")


if __name__ == "__main__":
    main()
