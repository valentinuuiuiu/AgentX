"""
run.py - Single Entry Point for Rehoboam
==========================================
Starts the entire multi-agent system with:
  - 4 specialized agents (Ollama)
  - Smart fallback routing (OpenRouter FREE -> ministral-3:3b)
  - MCP Specialist (Nemotron 3 Super)
  - Vetal Shabar (Forge tools)
  - FastAPI server + WebSocket
"""

import os
import sys
import json
import logging
from datetime import datetime

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("RehoboamRun")


def check_ollama():
    """Check if Ollama is running and list available models."""
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            logger.info(f"Ollama running. Models: {models}")
            return True, models
    except Exception as e:
        logger.warning(f"Ollama not reachable: {e}")
        logger.info("System will use OpenRouter fallbacks.")
    return False, []


def check_openrouter():
    """Check OpenRouter API key and connectivity."""
    import requests
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        logger.info("OPENROUTER_API_KEY not in env vars.")
    return True


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║              REHOBOAM v2.0 - Web3 Agent System           ║
║                                                          ║
║  Agents:                                                 ║
║    The King       → minimax-m2.7:cloud                  ║
║    Akhenaton      → gemini-3-flash-preview:latest       ║
║    Vetala         → kimi-k2.5:cloud                     ║
║    Minion         → llama3.2:latest                     ║
║                                                          ║
║  MCP Generator    → nemotron-3-super-120b-a12b:free    ║
║  Fallback Chain → Qwen 3.6 → Step 3.5 → Trinity → GLM  ║
║  Final Fallback   → ministral-3:3b (local)              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


def main():
    print_banner()
    
    logger.info("Rehoboam starting up...")
    
    # Check providers
    check_ollama()
    check_openrouter()
    
    # Import the multi-agent framework
    from utils.multi_agent_framework import create_rehoboam_crew
    from utils.agent_router import router
    from utils.mcp_specialist import MCPSpecialist
    from utils.vetal_shabar import VetalShabar
    
    # Initialize the crew
    logger.info("Initializing multi-agent crew...")
    crew = create_rehoboam_crew()
    logger.info(f"Crew ready: {list(crew.agents.keys())}")
    
    # Initialize MCP Specialist
    logger.info("Initializing MCP Specialist (Nemotron 3 Super)...")
    specialist = MCPSpecialist()
    
    # Initialize Vetal Shabar
    logger.info("Initializing Vetal Shabar (Forge tools)...")
    shabar = VetalShabar()
    
    # Print status
    logger.info(f"Fallback stats: {router.get_stats()}")
    logger.info(f"MCP tools: {len(specialist.list_mcp_functions())}")
    
    # Start FastAPI server
    logger.info("Starting API server on port 8000...")
    print("\nRehoboam ready! API: http://localhost:8000")
    print("WebSocket: ws://localhost:8000/ws")
    print("Press Ctrl+C to stop.\n")
    
    import uvicorn
    from api_server import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
    )

if __name__ == "__main__":
    main()
