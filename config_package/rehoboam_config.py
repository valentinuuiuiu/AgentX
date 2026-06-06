"""
Rehoboam Global Configuration
===============================
Single source of truth for API keys, model routing, and fallback chains.
Reads the OpenRouter API key from ~/.hermes/config.yaml
"""

import os
import yaml
from typing import List, Dict, Any

# ============================================================
# OPENROUTER CONFIGURATION (from ~/.hermes/config.yaml)
# ============================================================
def _load_openrouter_key() -> str:
    """Read OpenRouter API key from Hermes config.yaml."""
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        key = config.get("model", {}).get("api_key", "")
        if key:
            return key
    except Exception:
        pass
    # Fallback to env var
    return os.environ.get("OPENROUTER_API_KEY", "")

OPENROUTER_API_KEY = _load_openrouter_key()
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Primary MCP generator model (MCPSpecialist uses this)
OPENROUTER_MCP_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

# ============================================================
# OLLAMA CONFIGURATION (local agent models)
# ============================================================
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

AGENT_MODELS = {
    "orchestrator": "z-ai/glm-4.5-air:free",
    "strategist":   "google/gemma-2-9b-it:free",
    "guardian":     "google/gemma-2-27b-it:free",
    "worker":       "ollama/qwen2.5:3b",
}

# ============================================================
# EXACT FALLBACK ORDER (NEVER change this order)
# ============================================================
# When ANY model fails or is rate limited, try in THIS ORDER:
OPENROUTER_FREE_FALLBACKS: List[str] = [
    "qwen/qwen3.6-plus:free",
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",
    "z-ai/glm-4.5-air:free",
]

# Absolute last resort (local, never rate limited)
LOCAL_FALLBACK_MODEL = "ministral-3:3b"
