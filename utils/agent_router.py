"""
Rehoboam Smart Model Router
=============================
Unified intelligent routing for ALL agents.

FALLBACK CHAIN (NEVER rate limited, ALWAYS $0):
  1. Ollama primary models (task-specific):
     - Orchestrator: minimax-m2.7:cloud
     - Strategist (Akhenaton): gemini-3-flash-preview:latest
     - Guardian (Vetala): kimi-k2.5:cloud
     - Worker: llama3.2:latest
  
  2. OpenRouter FREE models (when Ollama is rate limited):
     - nvidia/nemotron-3-super-120b-a12b:free (MCP generation)
     - qwen/qwen3.6-plus:free (1M context, agentic coding)
     - stepfun/step-3.5-flash:free (fast MoE reasoning)
     - arcee-ai/trinity-large-preview:free (tool navigation)
     - z-ai/glm-4.5-air:free (MoE with thinking mode)
  
  3. Ollama LOCAL (absolute last resort, never fails):
     - ministral-3:3b
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ============================================================
# OPENROUTER CONFIGURATION (from ~/.hermes/config.yaml)
# ============================================================
def _load_openrouter_key() -> str:
    """Read OpenRouter API key from Hermes config.yaml."""
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        key = config.get("model", {}).get("api_key", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("OPENROUTER_API_KEY", "")

OPENROUTER_API_KEY = _load_openrouter_key()
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

FREE_MODELS = [
    {"id": "nvidia/nemotron-3-super-120b-a12b:free", "label": "Nemotron 3 Super", "role": "mcp_gen"},
    {"id": "qwen/qwen3.6-plus:free", "label": "Qwen 3.6 Plus", "role": "strategist"},
    {"id": "stepfun/step-3.5-flash:free", "label": "Step 3.5 Flash", "role": "worker"},
    {"id": "arcee-ai/trinity-large-preview:free", "label": "Trinity Large", "role": "strategist"},
    {"id": "z-ai/glm-4.5-air:free", "label": "GLM 4.5 Air", "role": "guardian"},
]

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

LOCAL_FALLBACK = "ministral-3:3b"

# === PRIMARY: Claude Opus 4.6 via Remix IDE MCP (beta) ===
REMIX_OPUS_URL = os.environ.get("REMIX_OPUS_MCP_URL", "http://localhost:3010")
REMIX_OPUS_MODEL = "claude-opus-4.6-remix"

# === SECONDARY: Chutes.ai (Bittensor-powered, free) ===
CHUTES_API_KEY = os.environ.get("CHUTES_API_KEY", "")
CHUTES_URL = "https://llm.chutes.ai/v1"
CHUTES_MODEL = "deepseek-ai/DeepSeek-V3-0324"

AGENT_MODELS = {
    "orchestrator": "minimax-m2.7:cloud",
    "strategist":   "gemini-3-flash-preview:latest",
    "guardian":     "kimi-k2.5:cloud",
    "knight":       "mimo-v2.5-pro",
    "worker":       "llama3.2:latest",
}

# === AUTOMATION: n8n Workflow Router ===
N8N_ROUTER_URL = os.environ.get("N8N_ROUTER_URL", "http://localhost:5678/webhook/rehoboam/query")

class SmartRouter:
    """
    Unified router for Rehoboam.
    All LLM calls go through this. It handles the fallback chain automatically.
    """
    
    def __init__(self, ollama_base_url: str = None, use_n8n: bool = False):
        self.ollama_url = ollama_base_url or OLLAMA_URL
        self.use_n8n = use_n8n
        self.call_history = []
        self.fallback_stats = {"remix_opus": 0, "chutes": 0, "ollama": 0, "openrouter": 0, "local": 0, "n8n": 0}
    
    def query(
        self,
        prompt: str,
        system_prompt: str = None,
        agent_role: str = "strategist",
        json_mode: bool = False,
        max_tokens: int = 8000,
        temperature: float = 0.3,
        timeout: int = 120,
        use_n8n: Optional[bool] = None,
    ) -> str:
        """
        Universal LLM query with smart routing.
        
        Flow:
        -1. n8n Automation Layer (if enabled)
        0. Claude Opus 4.6 via Remix IDE MCP (PRIMARY)
        ...
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # STEP -1: Delegate to n8n Automation Layer
        effective_use_n8n = use_n8n if use_n8n is not None else self.use_n8n
        if effective_use_n8n:
            try:
                payload = {
                    "messages": messages,
                    "agent_role": agent_role,
                    "chutes_key": CHUTES_API_KEY
                }
                resp = requests.post(N8N_ROUTER_URL, json=payload, timeout=timeout)
                resp.raise_for_status()
                self.fallback_stats["n8n"] += 1
                logger.info(f"[n8n ROUTER] Orchestration successful ✓")
                return resp.json().get("content", str(resp.json()))
            except Exception as e:
                logger.warning(f"n8n Router failed: {e}. Falling back to internal Remix logic...")
        
        # STEP 0: Try Claude Opus 4.6 via Remix IDE MCP (PRIMARY)
        try:
            payload = {"model": REMIX_OPUS_MODEL, "messages": messages,
                       "temperature": temperature, "max_tokens": max_tokens}
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            resp = requests.post(
                f"{REMIX_OPUS_URL}/v1/chat/completions",
                json=payload, timeout=30
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            self.fallback_stats["remix_opus"] += 1
            self.call_history.append({"model": REMIX_OPUS_MODEL, "source": "remix_opus_4.6", "success": True})
            logger.info(f"[REMIX OPUS 4.6] Response received ✓")
            return content
        except Exception as e:
            logger.warning(f"Remix Opus 4.6 unavailable: {e}. Trying Chutes.ai...")
        
        # STEP 0b: Try Chutes.ai (Bittensor-powered free inference)
        if CHUTES_API_KEY:
            try:
                payload = {"model": CHUTES_MODEL, "messages": messages,
                           "temperature": temperature, "max_tokens": max_tokens}
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}
                resp = requests.post(
                    f"{CHUTES_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {CHUTES_API_KEY}",
                             "Content-Type": "application/json"},
                    json=payload, timeout=60
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                self.fallback_stats["chutes"] += 1
                self.call_history.append({"model": CHUTES_MODEL, "source": "chutes_bittensor", "success": True})
                logger.info(f"[CHUTES/BITTENSOR] Response received ✓")
                return content
            except Exception as e:
                logger.warning(f"Chutes.ai unavailable: {e}. Trying Ollama...")

        # STEP 1: Try Ollama primary model
        primary_model = AGENT_MODELS.get(agent_role, AGENT_MODELS["strategist"])
        try:
            resp = requests.post(
                f"{self.ollama_url}/v1/chat/completions",
                json={
                    "model": primary_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            self.fallback_stats["ollama"] += 1
            self.call_history.append({"model": primary_model, "source": "ollama", "success": True})
            return content
        except Exception as e:
            logger.warning(f"Ollama {primary_model} failed: {e}. Trying OpenRouter fallbacks.")
        
        # STEP 2: Try OpenRouter FREE models
        # Pick the best free model for this agent role
        role_models = [m for m in FREE_MODELS if m["role"] == agent_role]
        all_free = role_models + [m for m in FREE_MODELS if m["role"] != agent_role]
        
        for model_info in all_free:
            model_id = model_info["id"]
            try:
                payload = {
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}
                
                resp = requests.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "HTTP-Referer": "https://github.com/rehoboam",
                        "X-Title": "Rehoboam Web3 Agent",
                    },
                    json=payload,
                    timeout=timeout,
                )
                resp.raise_for_status()
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                
                self.fallback_stats["openrouter"] += 1
                self.call_history.append({"model": model_id, "source": "openrouter_free", "success": True})
                logger.info(f"[OPENROUTER FALLBACK OK] {model_info['label']} ({model_id})")
                return content
                
            except Exception as e:
                logger.warning(f"OpenRouter {model_id} failed: {e}")
                continue
        
        logger.warning("All OpenRouter free models failed. Final fallback: Ollama ministral-3:3b")
        
        # STEP 3: Final fallback - Ollama local (ministral-3:3b)
        return self._local_fallback(messages, temperature, max_tokens, json_mode, agent_role)
    
    def _local_fallback(self, messages, temperature, max_tokens, json_mode, agent_role):
        """Absolute last resort. ministral-3:3b on local Ollama."""
        try:
            resp = requests.post(
                f"{self.ollama_url}/v1/chat/completions",
                json={
                    "model": LOCAL_FALLBACK,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=120,
            )
            resp.raise_for_status()
            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            self.fallback_stats["local"] += 1
            self.call_history.append({"model": LOCAL_FALLBACK, "source": "ollama_local_fallback", "success": True})
            logger.info(f"[LOCAL FALLBACK OK] {LOCAL_FALLBACK}")
            return content
        except Exception as e:
            logger.critical(f"ALL PROVIDERS FAILED. Returning safe fallback response: {e}")
            self.call_history.append({"model": LOCAL_FALLBACK, "source": "ollama_local_fallback", "success": False})
            
            # Return safe default JSON based on what might be expected
            if json_mode:
                if agent_role == "strategist":
                    return '{"action": "wait", "confidence": 0, "reasoning": "Offline safe mode", "stop_loss": 0, "take_profit": 0}'
                elif agent_role == "guardian":
                    return '{"risk_level": "high", "max_exposure_pct": 0, "warning_msg": "Offline safe mode - all blocked.", "code": "def offline_mock():\\n    pass"}'
                else:
                    return '{"status": "offline", "error": "All providers failed"}'
            return "System is in safe mode due to LLM provider failure."
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_calls": sum(self.fallback_stats.values()),
            "fallback_distribution": self.fallback_stats.copy(),
            "recent_calls": self.call_history[-10:],
            "config": {
                "ollama_primary": AGENT_MODELS,
                "openrouter_free": [m["id"] for m in FREE_MODELS],
                "local_fallback": LOCAL_FALLBACK,
            }
        }
    
    def health_check(self) -> Dict[str, bool]:
        """Check which providers are available."""
        status = {}
        
        # Check Ollama
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            status["ollama"] = resp.status_code == 200
        except:
            status["ollama"] = False
        
        # Check OpenRouter
        try:
            resp = requests.get(f"{OPENROUTER_BASE}/models", headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"}, timeout=10)
            status["openrouter"] = resp.status_code == 200
        except:
            status["openrouter"] = False
        
        return status

# Global instance
router = SmartRouter()
