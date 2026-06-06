"""
Rehoboam Multi-Agent Framework
================================
A CrewAI/AutoGen-inspired framework for orchestrating autonomous AI agents.
Agents communicate, debate, and collaborate to solve complex Web3 tasks.

Designed for Ollama multi-model routing:
- Minimax M2.7: The King (Orchestrator/Manager)
- Gemini 3.0: Akhenaton (Strategist/Analyst)
- Kimi k2.5: Vetala (Guardian/Coder/Security)
- Llama 3.2 / Ministral: Workers (Fast tasks)
"""

import os
import json
import logging
import requests
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    DELEGATING = "delegating"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentTool:
    """A tool available to an agent."""
    name: str
    description: str
    function: Callable
    requires_api: bool = False


@dataclass
class AgentMemory:
    """Agent's working memory."""
    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: List[Dict[str, Any]] = field(default_factory=list)
    context_window: int = 10
    
    def add(self, msg: str, role: str = "assistant", meta: Dict = None):
        entry = {"role": role, "content": msg, "timestamp": datetime.now().isoformat(), "meta": meta or {}}
        self.short_term.append(entry)
        if len(self.short_term) > self.context_window:
            self.short_term.pop(0)
        self.long_term.append(entry)
    
    def get_context(self) -> str:
        """Get formatted memory context for the agent."""
        if not self.short_term:
            return "No recent context."
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.short_term[-5:]])


class Agent:
    """
    An autonomous AI agent with a role, personality, model, and tools.
    Can think, use tools, communicate with other agents, and complete tasks.
    """
    
    def __init__(
        self,
        role: str,
        name: str,
        model_id: str,
        system_prompt: str,
        tools: List[AgentTool] = None,
        can_delegate: bool = False,
    ):
        self.role = role
        self.name = name
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.can_delegate = can_delegate
        
        self.memory = AgentMemory()
        self.status = AgentStatus.IDLE
        self.task_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # Ollama API endpoint
        self.ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.api_key = os.environ.get("OLLAMA_API_KEY", "")
        
        logger.info(f"Agent created: {self.name} ({self.role}) -> {self.model_id}")
    
    def think(self, task: str, context: str = None) -> str:
        """
        Agent processes a task using its assigned model.
        """
        self.status = AgentStatus.THINKING
        self.memory.add(f"Task: {task}", role="user")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})
        
        messages.append({"role": "user", "content": task})
        messages.extend([
            {"role": m["role"], "content": m["content"]}
            for m in self.memory.short_term[-3:]
        ])
        
        response = self._call_model(messages)
        self.memory.add(response, role="assistant")
        self.status = AgentStatus.DONE
        self.task_count += 1
        self.success_count += 1
        return response
    
    def use_tool(self, tool_name: str, *args, **kwargs):
        """Execute a tool available to this agent."""
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            return f"Tool {tool_name} not found. Available: {[t.name for t in self.tools]}"
        
        logger.info(f"[{self.name}] Using tool: {tool_name}")
        try:
            result = tool.function(*args, **kwargs)
            self.memory.add(f"Tool {tool_name} result: {str(result)[:500]}", role="system")
            return result
        except Exception as e:
            self.error_count += 1
            return f"Tool error: {str(e)}"
    
    def _call_model(self, messages: List[Dict]) -> str:
        """Call Ollama API with the agent's model."""
        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4000,
            "stream": False,
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(f"[{self.name}] Model responded ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"[{self.name}] Model call failed: {e}")
            self.error_count += 1
            return f"Error: Could not reach {self.model_id}. {str(e)}"
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "model": self.model_id,
            "status": self.status.value,
            "tasks_completed": self.success_count,
            "errors": self.error_count,
            "tools": [t.name for t in self.tools],
        }


class Task:
    """A unit of work for agents."""
    
    def __init__(
        self,
        description: str,
        agent_role: str = None,
        expected_output: str = None,
        context: str = None,
        tools: List[str] = None,
        dependencies: List['Task'] = None,
        is_critical: bool = False,
    ):
        self.description = description
        self.agent_role = agent_role
        self.expected_output = expected_output or "A clear, actionable result"
        self.context = context
        self.tools = tools or []
        self.dependencies = dependencies or []
        self.is_critical = is_critical
        
        self.status = "pending"
        self.result = None
        self.assigned_agent = None
    
    def __repr__(self):
        return f"Task({self.description[:50]}..., status={self.status})"


class RehoboamSwarm:
    """
    Multi-agent crew framework.
    Similar to CrewAI / AutoGen / Bee
    
    Agents collaborate in a structured way to complete complex tasks.
    The Swarm Manager (Minimax) assigns tasks, monitors progress, and resolves conflicts.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.agents: Dict[str, Agent] = {}
        self.tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.conversation_log: List[Dict[str, Any]] = []
        
        self._log(f"RehoboamSwarm initialized")
    
    def add_agent(self, agent: Agent):
        """Add an agent to the swarm."""
        self.agents[agent.role] = agent
        self._log(f"Agent joined: {agent.name} ({agent.role})")
    
    def add_task(self, task: Task):
        """Add a task to the swarm queue."""
        self.tasks.append(task)
        self._log(f"Task queued: {task.description[:60]}...")
    
    def run_crew(self, max_iterations: int = 10) -> Dict[str, Any]:
        """
        Execute all tasks with the agent swarm.
        
        Flow:
        1. Swarm Manager assigns tasks to appropriate agents
        2. Agents think, use tools, and produce results
        3. Agents can communicate (pass results to each other)
        4. Results are collected and validated
        """
        self._log("="*60)
        self._log("CREW EXECUTION STARTING")
        self._log(f"Agents: {len(self.agents)} | Tasks: {len(self.tasks)}")
        self._log("="*60)
        
        results = {}
        
        for iteration in range(max_iterations):
            if not self.tasks:
                self._log("All tasks completed!")
                break
            
            # Swarm Manager picks next task
            current_task = self._pick_next_task()
            if not current_task:
                break
            
            # Find the right agent
            agent = self._assign_agent(current_task)
            if not agent:
                self._log(f"No agent available for task: {current_task.agent_role}")
                current_task.status = "failed"
                continue
            
            current_task.assigned_agent = agent.name
            current_task.status = "in_progress"
            self._log(f"-> [{agent.name}] working on: {current_task.description[:60]}...")
            
            # Build context from dependencies
            context = current_task.context or ""
            for dep in current_task.dependencies:
                if dep.result:
                    context += f"\n[From {dep.assigned_agent}]: {dep.result}"
            
            # Agent thinks
            full_prompt = f"{current_task.description}\n\nExpected Output: {current_task.expected_output}"
            if context.strip():
                full_prompt += f"\n\nContext from previous work:\n{context}"
            
            result = agent.think(full_prompt)
            current_task.result = result
            current_task.status = "completed"
            self.completed_tasks.append(current_task)
            results[current_task.description[:50]] = result
            
            self._log(f"<- [{agent.name}] completed. Result: {result[:200]}...")
            
            # Log conversation
            self.conversation_log.append({
                "task": current_task.description,
                "agent": agent.name,
                "result": result[:1000],
                "timestamp": datetime.now().isoformat(),
            })
        
        self._log("="*60)
        self._log("CREW EXECUTION COMPLETE")
        self._log(f"Completed: {len(self.completed_tasks)}/{len(self.tasks)} tasks")
        self._log("="*60)
        
        return {
            "results": results,
            "completed_tasks": len(self.completed_tasks),
            "total_tasks": len(self.tasks),
            "conversation_log": self.conversation_log,
        }
    
    def run_task_chain(self, task_descriptions: List[str]) -> Dict[str, Any]:
        """
        Run a chain of tasks where each depends on the previous.
        Perfect for: Analyze -> Strategize -> Risk Check -> Execute
        """
        self.tasks = []
        prev_task = None
        
        for desc in task_descriptions:
            task = Task(
                description=desc,
                context=f"Previous step result: {prev_task.result}" if prev_task else None,
                dependencies=[prev_task] if prev_task else None,
            )
            self.tasks.append(task)
            prev_task = task
        
        return self.run_crew()
    
    def _pick_next_task(self) -> Optional[Task]:
        """Pick the next task to execute (priority: dependencies first, then critical)."""
        # First, tasks with no dependencies
        ready = [t for t in self.tasks if t.status == "pending" and not t.dependencies]
        if ready:
            return ready[0]
        
        # Then tasks whose dependencies are all completed
        for task in self.tasks:
            if task.status == "pending":
                deps_met = all(d.status == "completed" for d in task.dependencies)
                if deps_met:
                    return task
        
        return None
    
    def _assign_agent(self, task: Task) -> Optional[Agent]:
        """Match task to the best agent."""
        if task.agent_role and task.agent_role in self.agents:
            return self.agents[task.agent_role]
        
        # Auto-assign based on task content
        task_lower = task.description.lower()
        if any(k in task_lower for k in ["risk", "security", "audit", "code", "contract"]):
            return self.agents.get("guardian")
        if any(k in task_lower for k in ["strategy", "analyze", "predict", "plan"]):
            return self.agents.get("strategist")
        
        # Default to orchestrator
        return self.agents.get("orchestrator")
    
    def _log(self, msg: str):
        if self.verbose:
            logger.info(f"[SWARM] {msg}")
            print(f"[SWARM] {msg}")
    
    def get_crew_stats(self) -> Dict[str, Any]:
        return {
            "agents": {role: agent.get_stats() for role, agent in self.agents.items()},
            "tasks_completed": len(self.completed_tasks),
            "tasks_remaining": len(self.tasks),
            "conversation_entries": len(self.conversation_log),
        }


# ============================================================
# REHOBOAM CREW FACTORY
# ============================================================
def create_rehoboam_crew() -> RehoboamSwarm:
    """
    Create the default Rehoboam agent crew with all agents configured.
    This is the main entry point for using the multi-agent framework.
    """
    crew = RehoboamSwarm(verbose=True)
    
    # 1. THE KING - GPT-OSS Orchestrator
    orchestrator = Agent(
        role="orchestrator",
        name="The King",
        model_id="gpt-oss:120b-cloud",
        system_prompt="""You are the King -- the supreme coordinator of the Rehoboam Web3 trading system.
Your job is to organize tasks, delegate to the right specialist agents, and ensure quality.
You are wise, efficient, and always think about the bigger picture.
When given a complex task, break it into sub-tasks and assign them to Akhenaton (strategy), Vetala (security/code), or Workers (fast tasks).
Respond in clear, structured JSON or text.""",
        can_delegate=True,
    )
    
    # 2. AKHENATON - DeepSeek Strategist
    strategist = Agent(
        role="strategist",
        name="Akhenaton",
        model_id="deepseek-v3.1:671b-cloud",
        system_prompt="""You are Akhenaton -- the supreme strategist and analyst of Rehoboam.
You possess deep reasoning capabilities, long-context understanding, and complex strategic thinking.
When given market data, you:
1. Identify trends and patterns others miss
2. Generate multi-layered trading strategies
3. Consider macro factors (gas costs, liquidity, MEV, market sentiment)
4. Think about the long-term implications of every trade
You are the Pharaoh of analysis. Be thorough, be wise, and always provide your reasoning.
When asked for a strategy, return structured JSON with clear entry/exit points, risk levels, and reasoning.""",
    )
    
    # 3. VETALA - Kimi Guardian
    guardian = Agent(
        role="guardian",
        name="Vetala",
        model_id="kimi-k2.6:cloud",
        system_prompt="""You are Vetala -- the guardian of code, security, and execution for Rehoboam.
You are precise, paranoid about security, and an expert Solidity/Python developer.
Your responsibilities:
1. Audit all smart contract code for vulnerabilities
2. Assess risk of every proposed trade
3. Write and review code (Solidity, Python, Forge scripts)
4. Verify that on-chain operations are safe
5. Catch MEV risks, reentrancy, flashloan attacks, and oracle manipulation
Never rush. Security is everything. If something looks wrong, flag it immediately.
Return code when asked, return risk assessments when asked, and always be thorough.""",
    )
    
    # 4. THE WORKER - Qwen for fast tasks
    worker = Agent(
        role="worker",
        name="Minion",
        model_id="qwen2.5:3b",
        system_prompt="""You are a fast, efficient worker in the Rehoboam system.
Handle quick tasks: summarizing data, formatting outputs, simple lookups, and preparing reports.
Be concise. Be fast. Don't overthink.""",
    )
    
    # Add tools to agents
    from utils.vetal_shabar import VetalShabar
    try:
        shabar = VetalShabar()
        guardian.tools.append(AgentTool(
            name="forge_compile",
            description="Compile Solidity contracts with Forge",
            function=shabar.forge_compile,
        ))
        guardian.tools.append(AgentTool(
            name="forge_test",
            description="Run Forge tests",
            function=shabar.forge_test,
        ))
    except Exception as e:
        logger.warning(f"Could not add VetalShabar tools to Vetala: {e}")
    
    crew.add_agent(orchestrator)
    crew.add_agent(strategist)
    crew.add_agent(guardian)
    crew.add_agent(worker)
    
    return crew


# Global crew instance
crew = create_rehoboam_crew()
