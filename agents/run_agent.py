import asyncio
import json
import time
import argparse
import redis
import os
from datetime import datetime
from openai import OpenAI

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
AGENT_COMMAND_CHANNEL = "rehoboam:commands"

class AgentRunner:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.running = False
        
        # Decide which model to use based on the agent's name
        self.model = "deepseek-ai/deepseek-v4-pro"
        if "GLM" in self.name:
            self.model = "z-ai/glm-5.1"
        elif "Kimi" in self.name:
            self.model = "moonshotai/kimi-k2.6"
            
        self.llm_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=NVIDIA_API_KEY
        )

    def heartbeat(self):
        payload = json.dumps({"type": "heartbeat", "agent_id": self.name})
        self.redis_client.publish(AGENT_COMMAND_CHANNEL, payload)

    async def autonomous_loop(self):
        """Simulates the agent performing its continuous specialized tasks."""
        while self.running:
            print(f"[{self.name}] Autonomous loop check...")
            # Here it would execute MCP tools/skills like fetch_market_data, scan_github, etc.
            # For now, it just reports health back to the orchestrator.
            self.heartbeat()
            await asyncio.sleep(10)

    async def listen_for_tasks(self):
        """Listens to Redis for direct instructions from other agents or the UI."""
        self.pubsub.subscribe(f"rehoboam:tasks:{self.name}")
        while self.running:
            try:
                message = self.pubsub.get_message(timeout=1)
                if message and message["type"] == "message":
                    task = json.loads(message["data"])
                    print(f"[{self.name}] Received task: {task}")
                    # Simulate processing task via Nvidia NIM
                    prompt = f"You are {self.name}, {self.role}. Process this task: {task}"
                    try:
                        completion = self.llm_client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.7,
                            max_tokens=500
                        )
                        result = completion.choices[0].message.content
                    except Exception as e:
                        result = f"Error calling model {self.model}: {e}"
                        
                    print(f"[{self.name}] Task completed. Result: {result[:50]}...")
                    # Report back to orchestrator
                    complete_msg = json.dumps({
                        "type": "task_complete",
                        "agent_id": self.name,
                        "task_id": task.get("task_id", "unknown"),
                        "result": result
                    })
                    self.redis_client.publish(AGENT_COMMAND_CHANNEL, complete_msg)
            except Exception as e:
                print(f"[{self.name}] Listener error: {e}")
            await asyncio.sleep(0.5)

    async def run(self):
        print(f"Starting {self.name} ({self.role}) using model {self.model}...")
        self.running = True
        # Register with orchestrator
        reg_payload = json.dumps({
            "type": "register",
            "agent_id": self.name,
            "role": self.role,
            "metadata": {"model": self.model}
        })
        self.redis_client.publish(AGENT_COMMAND_CHANNEL, reg_payload)
        
        await asyncio.gather(
            self.autonomous_loop(),
            self.listen_for_tasks()
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Name of the agent")
    parser.add_argument("--role", required=True, help="Role description")
    args = parser.parse_args()
    
    runner = AgentRunner(args.name, args.role)
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        print(f"Shutting down {args.name}...")
