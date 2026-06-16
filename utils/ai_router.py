"""
Unified AI Router — all free providers in a failover chain.
Providers: Chutes.ai (Bittensor) > NVIDIA NIM > OpenRouter > DeepSeek > Ollama
Each provider uses OpenAI-compatible API, just different base_url and api_key.
"""

import os
import time
import logging
import httpx
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("ai_router")

# ============================================================
# PROVIDER CONFIGS
# ============================================================

@dataclass
class AIProvider:
    name: str
    base_url: str
    api_key: str
    models: Dict[str, str]  # role -> model_id
    priority: int  # lower = tried first
    rpm_limit: int = 40  # requests per minute
    enabled: bool = True
    _last_request_time: float = 0.0
    _request_count: int = 0


def _load_providers() -> List[AIProvider]:
    """Build provider list from env vars. Only includes providers with API keys."""
    providers = []

    # 1. Chutes.ai (Bittensor-powered, FREE)
    chutes_key = os.environ.get("CHUTES_API_KEY", "")
    if chutes_key:
        providers.append(AIProvider(
            name="chutes",
            base_url="https://llm.chutes.ai/v1",
            api_key=chutes_key,
            models={
                "fast": "zai-org/GLM-5.1-TEE",
                "deep": "deepseek-ai/DeepSeek-R1-0528-TEE",
                "orchestrator": "openai/gpt-oss-120b-TEE",
                "code": "Qwen/Qwen3-Coder-Next-TEE",
                "vision": "Qwen/Qwen2.5-VL-32B-Instruct",
            },
            priority=1,
        ))

    # 2. NVIDIA NIM (free credits, 40 RPM)
    nvidia_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
    if nvidia_key:
        providers.append(AIProvider(
            name="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key,
            models={
                "fast": "zai-org/glm-5.1",
                "deep": "nvidia/nemotron-3-super-120b-a12b",
                "orchestrator": "minimaxai/minimax-m2.7",
                "code": "Qwen/Qwen3-Coder-Next-TEE",
                "vision": "nvidia/nemotron-3-super-120b-a12b",
            },
            priority=2,
            rpm_limit=40,
        ))

    # 3. OpenRouter (free models)
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        providers.append(AIProvider(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            models={
                "fast": "google/gemma-3-4b-it:free",
                "deep": "deepseek/deepseek-r1-0528:free",
                "orchestrator": "qwen/qwen3-235b-a22b:free",
                "code": "qwen/qwen3-coder:free",
            },
            priority=3,
        ))

    # 4. DeepSeek (direct API)
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if deepseek_key:
        providers.append(AIProvider(
            name="deepseek",
            base_url="https://api.deepseek.com/v1",
            api_key=deepseek_key,
            models={
                "fast": "deepseek-chat",
                "deep": "deepseek-reasoner",
                "orchestrator": "deepseek-chat",
                "code": "deepseek-chat",
            },
            priority=4,
        ))

    # 5. Ollama (local/cloud)
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
    providers.append(AIProvider(
        name="ollama",
        base_url=ollama_url,
        api_key="ollama",  # no key needed
        models={
            "fast": os.environ.get("OLLAMA_FAST_MODEL", "glm-5.1:cloud"),
            "deep": os.environ.get("OLLAMA_DEEP_MODEL", "gpt-oss:120b-cloud"),
            "orchestrator": os.environ.get("OLLAMA_ORCH_MODEL", "gpt-oss:120b-cloud"),
            "code": os.environ.get("OLLAMA_CODE_MODEL", "glm-5.1:cloud"),
        },
        priority=5,
        rpm_limit=100,
    ))

    providers.sort(key=lambda p: p.priority)
    logger.info(f"AI Router: {len(providers)} providers loaded: {[p.name for p in providers]}")
    return providers


# ============================================================
# AI ROUTER
# ============================================================

class AIRouter:
    """Unified AI router with failover across all free providers."""

    def __init__(self):
        self.providers: List[AIProvider] = _load_providers()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        role: str = "fast",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        preferred_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a chat completion request with automatic failover.

        Args:
            messages: OpenAI-format messages list
            role: "fast", "deep", "orchestrator", "code", "vision"
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            preferred_provider: Skip to this provider first

        Returns:
            {"provider": ..., "model": ..., "content": ..., "usage": ...}
        """
        # Reorder providers if preferred_provider is specified
        providers = list(self.providers)
        if preferred_provider:
            preferred = [p for p in providers if p.name == preferred_provider]
            others = [p for p in providers if p.name != preferred_provider]
            providers = preferred + others

        errors = []
        for provider in providers:
            if not provider.enabled:
                continue
            model = provider.models.get(role, provider.models.get("fast"))
            if not model:
                continue
            try:
                result = await self._call_provider(provider, model, messages, temperature, max_tokens)
                result["provider"] = provider.name
                result["model"] = model
                result["role"] = role
                return result
            except Exception as e:
                logger.warning(f"Provider {provider.name}/{model} failed: {e}")
                errors.append(f"{provider.name}: {e}")
                continue

        return {"error": "All providers failed", "details": errors, "content": ""}

    async def quick_chat(
        self,
        prompt: str,
        role: str = "fast",
        system: str = "You are a helpful AI assistant.",
        preferred_provider: Optional[str] = None,
    ) -> str:
        """Simple prompt -> response. Returns just the text content."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        result = await self.chat(messages, role=role, preferred_provider=preferred_provider)
        return result.get("content", "")

    async def _call_provider(
        self,
        provider: AIProvider,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Make the actual HTTP call to a provider."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        # OpenRouter needs extra headers
        if provider.name == "openrouter":
            headers["HTTP-Referer"] = "https://rehoboam.ai"
            headers["X-Title"] = "Rehoboam"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{provider.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.text[:500]}")

            data = resp.json()
            content = ""
            if "choices" in data and data["choices"]:
                content = data["choices"][0].get("message", {}).get("content", "")

            usage = data.get("usage", {})
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
            }

    def get_status(self) -> Dict[str, Any]:
        """Return status of all providers."""
        return {
            "providers": [
                {
                    "name": p.name,
                    "priority": p.priority,
                    "base_url": p.base_url,
                    "models": p.models,
                    "enabled": p.enabled,
                }
                for p in self.providers
            ],
            "total_providers": len(self.providers),
            "active_providers": sum(1 for p in self.providers if p.enabled),
        }


# Singleton
ai_router = AIRouter()