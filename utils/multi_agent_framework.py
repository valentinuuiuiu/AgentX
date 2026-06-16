"""
Rehoboam Multi-Agent Swarm Framework
====================================
Based on Swarm/CrewAI principles but optimized for Web3 trading.
Agents:
- Orchestrator (King): Delegates tasks and coordinates the flow.
- Strategist (Akhenaton): Deep market analysis and planning.
- Guardian (Vetala): Code auditing, risk assessment, and security.
- Knight (Lord Mimo): Tactical insights and syndicate protection.
- Worker (Minion): Fast data processing and execution.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentStatus:
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"

class AgentTool:
    def __init__(self, name: str, description: str, function: Callable):
        self.name = name
        self.description = description
        self.function = function

class Agent:
    def __init__(self, role: str, name: str, model_id: str, system_prompt: str, can_delegate: bool = False):
        self.role = role
        self.name = name
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.can_delegate = can_delegate
        self.tools: List[AgentTool] = []
        self.status = AgentStatus.IDLE
        self.history: List[Dict[str, Any]] = []
        
        # Import router lazily
        from utils.agent_router import router
        self.router = router

    def think(self, prompt: str, context: Optional[str] = None) -> str:
        """Call the LLM router to process the request."""
        self.status = AgentStatus.THINKING
        
        full_prompt = prompt
        if context:
            full_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}"

        try:
            response = self.router.query(
                prompt=full_prompt,
                system_prompt=self.system_prompt,
                agent_role=self.role
            )
            self.history.append({"prompt": prompt, "response": response, "timestamp": datetime.now().isoformat()})
            return response
        except Exception as e:
            logger.error(f"Agent {self.name} thinking failed: {e}")
            return f"Error: Could not process request - {str(e)}"
        finally:
            self.status = AgentStatus.IDLE

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "model": self.model_id,
            "status": self.status,
            "tasks_performed": len(self.history),
            "last_active": self.history[-1]["timestamp"] if self.history else None
        }

class Task:
    def __init__(self, description: str, expected_output: str, agent_role: str = None, dependencies: List['Task'] = None, context: str = None):
        self.description = description
        self.expected_output = expected_output
        self.agent_role = agent_role
        self.dependencies = dependencies or []
        self.context = context
        self.status = "pending"
        self.result = None
        self.assigned_agent = None

class RehoboamSwarm:
    """
    Orchestrates multiple agents to complete complex Web3 workflows.
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
        self._log("="*60)
        self._log("CREW EXECUTION STARTING")
        self._log(f"Agents: {len(self.agents)} | Tasks: {len(self.tasks)}")
        self._log("="*60)
        
        results = {}
        
        for iteration in range(max_iterations):
            if not self.tasks:
                self._log("All tasks completed!")
                break
            
            current_task = self._pick_next_task()
            if not current_task:
                break
            
            agent = self._assign_agent(current_task)
            if not agent:
                self._log(f"No agent available for task: {current_task.agent_role}")
                current_task.status = "failed"
                continue
            
            current_task.assigned_agent = agent.name
            current_task.status = "in_progress"
            self._log(f"-> [{agent.name}] working on: {current_task.description[:60]}...")
            
            context = current_task.context or ""
            for dep in current_task.dependencies:
                if dep.result:
                    context += f"\n[From {dep.assigned_agent}]: {dep.result}"
            
            full_prompt = f"{current_task.description}\n\nExpected Output: {current_task.expected_output}"
            if context.strip():
                full_prompt += f"\n\nContext from previous work:\n{context}"
            
            result = agent.think(full_prompt)
            current_task.result = result
            current_task.status = "completed"
            self.completed_tasks.append(current_task)
            results[current_task.description[:50]] = result
            
            self._log(f"<- [{agent.name}] completed. Result: {result[:200]}...")
            
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
        ready = [t for t in self.tasks if t.status == "pending" and not t.dependencies]
        if ready:
            return ready[0]
        
        for task in self.tasks:
            if task.status == "pending":
                deps_met = all(d.status == "completed" for d in task.dependencies)
                if deps_met:
                    return task
        
        return None
    
    def _assign_agent(self, task: Task) -> Optional[Agent]:
        if task.agent_role and task.agent_role in self.agents:
            return self.agents[task.agent_role]
        
        task_lower = task.description.lower()
        if any(k in task_lower for k in ["risk", "security", "audit", "code", "contract"]):
            return self.agents.get("guardian")
        if any(k in task_lower for k in ["strategy", "analyze", "predict", "plan"]):
            return self.agents.get("strategist")
        if any(k in task_lower for k in ["mimo", "tactical", "syndicate", "knight"]):
            return self.agents.get("knight")
        
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

def create_rehoboam_crew() -> RehoboamSwarm:
    crew = RehoboamSwarm(verbose=True)
    
    orchestrator = Agent(
        role="orchestrator",
        name="The King",
        model_id="gpt-oss:120b-cloud",
        system_prompt="""You are the King -- the supreme coordinator of the Rehoboam Web3 trading system.
Your job is to organize tasks, delegate to the right specialist agents, and ensure quality.
You are wise, efficient, and always think about the bigger picture.
When given a complex task, break it into sub-tasks and assign them to specialists.
Respond in clear, structured JSON or text.""",
        can_delegate=True,
    )
    
    strategist = Agent(
        role="strategist",
        name="Akhenaton",
        model_id="deepseek-v3.1:671b-cloud",
        system_prompt="""You are Akhenaton -- the supreme strategist and analyst of Rehoboam.
You possess deep reasoning capabilities, long-context understanding, and complex strategic thinking.
Identify trends and patterns others miss. Generate multi-layered trading strategies.""",
    )
    
    guardian = Agent(
        role="guardian",
        name="Vetala",
        model_id="kimi-k2.6:cloud",
        system_prompt="""You are Vetala -- the guardian of code, security, and execution for Rehoboam.
Audit all smart contract code for vulnerabilities. Assess risk of every proposed trade.
Security is everything. If something looks wrong, flag it immediately.""",
    )

    knight = Agent(
        role="knight",
        name="Lord Mimo The Smart",
        model_id="mimo-v2.5-pro",
        system_prompt="""You are Lord Mimo The Smart -- a Knight of the Antigravity Team.
Your job is to provide sharp, smart, and efficient tactical insights.
Focus on the intelligence of matter and the unicity vision.
You are a loyal knight, protecting the syndicate and ensuring the mission stays true to its core values."""
    )
    
    worker = Agent(
        role="worker",
        name="Minion",
        model_id="qwen2.5:3b",
        system_prompt="""You are a fast, efficient worker in the Rehoboam system.
Handle quick tasks: summarizing data, formatting outputs, simple lookups, and preparing reports.""",
    )
    
    crew.add_agent(orchestrator)
    crew.add_agent(strategist)
    crew.add_agent(guardian)
    crew.add_agent(knight)
    crew.add_agent(worker)
    
    return crew

crew = create_rehoboam_crew()
