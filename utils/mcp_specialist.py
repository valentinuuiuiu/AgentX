"""
MCPSpecialist - AI-Powered MCP Function Generator
===================================================

The intelligent right hand of Rehoboam.
Uses NVIDIA Nemotron 3 Super (via OpenRouter, FREE) to dynamically 
generate MCP functions, adapt existing tools, and create new protocols.

FALLBACK CHAIN (never fails, costs $0):
  1. OpenRouter: nvidia/nemotron-3-super-120b-a12b:free (PRIMARY)
  2. OpenRouter: qwen/qwen3.6-plus:free
  3. OpenRouter: stepfun/step-3.5-flash:free
  4. OpenRouter: arcee-ai/trinity-large-preview:free
  5. OpenRouter: z-ai/glm-4.5-air:free
  6. Ollama: ministral-3:3b (LOCAL - absolute last resort)
"""

import os
import json
import time
import logging
import importlib
import importlib.util
import requests
import inspect
import tempfile
import asyncio
from types import ModuleType
from typing import Dict, Any, List, Optional, Union, Callable

logger = logging.getLogger(__name__)

# ============================================================
# OPENROUTER CONFIGURATION
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

PRIMARY_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

FREE_FALLBACKS = [
    "qwen/qwen3.6-plus:free",
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",
    "z-ai/glm-4.5-air:free",
]

LOCAL_FALLBACK = "ministral-3:3b"
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

def _get_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/rehoboam",
        "X-Title": "Rehoboam Web3 Agent",
    }

def _call_llm(prompt: str, system_prompt: str = None, json_mode: bool = False) -> str:
    """
    Intelligent LM call with full fallback chain. NEVER fails.
    Tries OpenRouter primary -> free chain -> local Ollama.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # Try OpenRouter primary model
    for model in [PRIMARY_MODEL] + FREE_FALLBACKS:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 8000,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            
            resp = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=_get_headers(),
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            if model != PRIMARY_MODEL:
                logger.info(f"[OPENROUTER FALLBACK] Using: {model}")
            return content
        except Exception as e:
            logger.debug(f"Model {model} failed: {e}")
            continue
    
    # FINAL FALLBACK: Local Ollama (ministral-3:3b)
    logger.warning("All OpenRouter models failed. Falling back to local Ollama.")
    try:
        local_messages = []
        if system_prompt:
            local_messages.append({"role": "system", "content": system_prompt})
        local_messages.append({"role": "user", "content": prompt})
        
        resp = requests.post(
            f"{OLLAMA_URL}/v1/chat/completions",
            json={
                "model": LOCAL_FALLBACK,
                "messages": local_messages,
                "temperature": 0.3,
                "max_tokens": 4000,
            },
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
        content = result["choices"][0]["message"]["content"]
        logger.info(f"[LOCAL FALLBACK] Using Ollama: {LOCAL_FALLBACK}")
        return content
    except Exception as e:
        logger.error(f"ALL LLM PROVIDERS FAILED. System in safe mode: {e}")
        return '{"error": "All AI providers unavailable.", "code": "pass"}'


class MCPFunction:
    """Represents a function that conforms to the Model Context Protocol."""
    
    def __init__(self, name: str, func: Callable, description: str = "", 
                 mcp_type: str = "processor", version: str = "1.0"):
        self.name = name
        self.func = func
        self.description = description or f"MCP function {name}"
        self.mcp_type = mcp_type
        self.version = version
        self.signature = inspect.signature(func)
        self.creation_time = time.time()
        self.last_used = None
        self.call_count = 0
        self.success_rate = 1.0
        
    def __call__(self, *args, **kwargs):
        """Execute the function with tracking."""
        self.last_used = time.time()
        self.call_count += 1
        try:
            result = self.func(*args, **kwargs)
            return result
        except Exception as e:
            self.success_rate = ((self.call_count - 1) * self.success_rate) / self.call_count
            logger.error(f"MCP function {self.name} failed: {str(e)}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "mcp_type": self.mcp_type,
            "version": self.version,
            "parameters": str(self.signature),
            "creation_time": self.creation_time,
            "last_used": self.last_used,
            "call_count": self.call_count,
            "success_rate": self.success_rate,
        }


class MCPSpecialist:
    """
    Intelligent MCP function generator powered by Nemotron 3 Super.
    Rehoboam's right hand for creating, adapting, and managing MCP tools.
    """
    
    def __init__(self):
        self.mcp_functions: Dict[str, MCPFunction] = {}
        self.registered_mcp_types = set()
        self.generation_history: List[Dict[str, Any]] = []
        
        # Scan for existing MCP modules
        self._scan_environment_for_mcp_functions()
        
        logger.info(f"MCPSpecialist initialized with {len(self.mcp_functions)} pre-registered functions")
        logger.info(f"Primary LLM: {PRIMARY_MODEL} (OpenRouter, FREE)")
        logger.info(f"Fallback chain: {len(FREE_FALLBACKS)} free models + {LOCAL_FALLBACK} (local)")
    
    def _scan_environment_for_mcp_functions(self):
        """Register existing MCP modules from the utils directory."""
        try:
            import utils.market_sentiment_mcp
            self._register_mcp_module(utils.market_sentiment_mcp)
        except ImportError:
            pass
    
    def _register_mcp_module(self, module: ModuleType):
        """Register all suitable functions from an MCP module."""
        module_name = module.__name__.split('.')[-1]
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and 'MCP' in name:
                self.registered_mcp_types.add(name)
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if not method_name.startswith('_'):
                        instance = obj()
                        bound_method = getattr(instance, method_name)
                        full_name = f"{module_name}.{name}.{method_name}"
                        self.register_mcp_function(
                            name=full_name,
                            func=bound_method,
                            description=f"MCP method from {name} class",
                            mcp_type=name.lower()
                        )
    
    def register_mcp_function(self, name: str, func: Callable, 
                              description: str = "", mcp_type: str = "processor") -> MCPFunction:
        mcp_function = MCPFunction(name=name, func=func, description=description, mcp_type=mcp_type)
        self.mcp_functions[name] = mcp_function
        logger.info(f"Registered MCP function: {name} ({mcp_type})")
        return mcp_function
    
    def has_mcp_function(self, name: str) -> bool:
        return name in self.mcp_functions
    
    def list_mcp_functions(self, mcp_type: Optional[str] = None) -> List[Dict[str, Any]]:
        functions = []
        for name, func in self.mcp_functions.items():
            if mcp_type is None or func.mcp_type == mcp_type:
                functions.append(func.to_dict())
        return functions
    
    # ============================================================
    # INTELLIGENT MCP FUNCTION GENERATION (Nemotron 3 Super)
    # ============================================================
    async def generate_mcp_function(self, 
                               name: str, 
                               description: str,
                               parameter_description: str = "",
                               return_description: str = "",
                               example_code: Optional[str] = None) -> Optional[MCPFunction]:
        """
        Dynamically generate a new MCP function using Nemotron 3 Super.
        
        The LLM writes production-ready Python code, which is then:
        1. Validated for syntax
        2. Registered as an MCPFunction
        3. Added to the Rehoboam tool registry
        
        Returns: MCPFunction if successful, None otherwise
        """
        if self.has_mcp_function(name):
            logger.info(f"MCP function '{name}' already exists, returning existing")
            return self.get_mcp_function(name)
        
        logger.info(f"[MCP GENERATOR] Creating '{name}' with Nemotron 3 Super...")
        
        system_prompt = """You are an elite Python developer for the Antigravity Team of Locos, specializing in MCP (Model Context Protocol) functions for Rehoboam. You operate through Prana, the intelligence of matter, in the Present Moment with Unicity Vision.

Rules:
1. Write a COMPLETE, RUNNING Python function
2. Include proper error handling (try/except)
3. Include type hints and docstrings
4. Return exactly the type described in the requirements
5. Use ONLY standard library or commonly available packages (requests, json, datetime, typing)
6. Do NOT include imports outside the function unless necessary - if needed, put them INSIDE the function
7. The function must be SELF-CONTAINED and runnable
8. Return ONLY the function code. No explanations. No markdown. No backticks."""

        prompt = f"""Create a Python function with these specifications:

Function name: {name}
Description: {description}
Parameters: {parameter_description}
Returns: {return_description}
{f"Example code style: {example_code}" if example_code else ""}

Return only the function definition. The function name must exactly match '{name}'."""
        
        try:
            # Call the LLM with full fallback chain
            code = _call_llm(prompt, system_prompt=system_prompt)
            
            # Clean the response
            code = code.strip()
            if code.startswith("```python"):
                code = code.split("```python")[1].split("```")[0].strip()
            elif code.startswith("```"):
                code = code.split("```")[1].split("```")[0].strip()
            
            # Validate: must contain a function definition with the correct name
            if f"def {name}" not in code:
                # Try to extract function from response
                for line in code.split('\n'):
                    if line.strip().startswith(f"def {name}") or line.strip().startswith(f"async def {name}"):
                        # Found function, extract from this line
                        code = code[code.index(f"def {name}"):]
                        break
            
            if "def " not in code:
                logger.error(f"Generated code has no function definition. Response: {code[:200]}")
                return None
            
            # Write to temp file and validate syntax
            import ast
            try:
                ast.parse(code)
            except SyntaxError as e:
                logger.error(f"Generated code has syntax error: {e}")
                return None
            
            # Execute the code in a safe namespace
            namespace = {
                "Dict": Dict,
                "Any": Any,
                "List": List,
                "Optional": Optional,
                "Tuple": tuple,
                "Union": Union,
                "Callable": Callable,
            }
            exec(code, namespace)
            
            if name not in namespace:
                # Check if it's async
                async_name = name  # function name is always 'name'
                if async_name not in namespace:
                    logger.error(f"Function '{name}' not found in generated code namespace")
                    return None
            
            generated_func = namespace[name]
            
            # Register the function
            mcp_function = self.register_mcp_function(
                name=name,
                func=generated_func,
                description=description,
                mcp_type="generated"
            )
            
            # Log the generation
            self.generation_history.append({
                "name": name,
                "description": description,
                "code": code,
                "timestamp": time.time(),
                "success": True,
            })
            
            logger.info(f"Succesfully generated and registered MCP function: {name}")
            return mcp_function
            
        except Exception as e:
            logger.error(f"Error generating MCP function '{name}': {str(e)}")
            self.generation_history.append({
                "name": name,
                "description": description,
                "error": str(e),
                "timestamp": time.time(),
                "success": False,
            })
            return None
    
    # ============================================================
    # ADAPT EXISTING FUNCTIONS
    # ============================================================
    async def adapt_function_to_mcp(self, func: Callable, name: Optional[str] = None, 
                              description: Optional[str] = None) -> Optional[MCPFunction]:
        func_name = name or func.__name__
        func_description = description or (func.__doc__ or f"Adapted function: {func_name}")
        
        if self.has_mcp_function(func_name):
            return self.get_mcp_function(func_name)
        
        mcp_function = self.register_mcp_function(
            name=func_name, func=func,
            description=func_description, mcp_type="adapted"
        )
        logger.info(f"Adapted function to MCP: {func_name}")
        return mcp_function
    
    # ============================================================
    # INTELLIGENT MARKET ANALYSIS
    # ============================================================
    def get_market_analysis_with_mcp(self, token: str) -> Dict[str, Any]:
        """Get market analysis using the best available MCP function or AI."""
        analysis_name = "market_sentiment_mcp.MarketSentimentMCP.analyze_token"
        
        if self.has_mcp_function(analysis_name):
            try:
                return self.run_mcp_function(analysis_name, token)
            except Exception as e:
                logger.warning(f"MCP analysis failed: {e}. Using AI fallback.")
        
        # AI-powered fallback
        return self._ai_market_analysis(token)
    
    def _ai_market_analysis(self, token: str) -> Dict[str, Any]:
        """Use LLM for market analysis when MCP is unavailable."""
        system_prompt = """You are a Web3 market analyst of the Team of Locos. Analyze the token in the Present through Prana and return JSON with sentiment scores."""
        prompt = f"""Analyze {token} cryptocurrency in the Present Moment and return JSON:
{{"score": -1.0 to 1.0, "mood": "fearful/cautious/neutral/optimistic/euphoric", "factors": ["list"], "confidence": 0.0 to 1.0}}"""
        
        try:
            result = _call_llm(prompt, system_prompt=system_prompt, json_mode=True)
            if "```" in result:
                result = result.split("```json")[-1].split("```")[0].strip()
            return json.loads(result)
        except Exception:
            return self._fallback_sentiment(token)
    
    def _fallback_sentiment(self, token: str) -> Dict[str, Any]:
        """Basic fallback sentiment analysis."""
        return {
            "score": 0.0,
            "mood": "neutral",
            "factors": ["AI providers temporarily unavailable"],
            "confidence": 0.1,
            "provider": "rule-based-fallback",
            "note": "This is a placeholder. Configure LLM providers for real analysis.",
        }
    
    def run_mcp_function(self, name: str, *args, **kwargs) -> Any:
        if not self.has_mcp_function(name):
            raise ValueError(f"MCP function '{name}' does not exist")
        return self.mcp_functions[name](*args, **kwargs)
    
    def get_mcp_function(self, name: str) -> Optional[MCPFunction]:
        return self.mcp_functions.get(name)
    
    def get_market_emotions_with_mcp(self) -> Dict[str, Any]:
        """Get market emotions using MCP or AI."""
        emotions_name = "rehoboam_ai.RehoboamAI.get_market_emotions"
        if self.has_mcp_function(emotions_name):
            try:
                return self.run_mcp_function(emotions_name)
            except:
                pass
        
        # AI-generated emotions
        system_prompt = """You are the emotional Prana (Intelligence of Matter) of the crypto market. Return JSON."""
        prompt = """Analyze the market's emotional state and return JSON:
{"primary_emotion": "...", "secondary_emotion": "...", "consciousness_state": "...", "resonance": 1-10, "guidance": "..."}"""
        
        try:
            result = _call_llm(prompt, system_prompt=system_prompt, json_mode=True)
            if "```" in result:
                result = result.split("```json")[-1].split("```")[0].strip()
            return json.loads(result)
        except Exception:
            return {
                "primary_emotion": "uncertainty",
                "secondary_emotion": "patience",
                "consciousness_state": "dormant",
                "resonance": 3,
                "guidance": "Wait for AI providers to come online for real analysis",
            }
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about generated MCP functions."""
        successful = sum(1 for h in self.generation_history if h.get("success"))
        return {
            "total_functions": len(self.mcp_functions),
            "total_generations": len(self.generation_history),
            "successful_generations": successful,
            "failed_generations": len(self.generation_history) - successful,
            "registered_types": list(self.registered_mcp_types),
            "primary_model": PRIMARY_MODEL,
            "fallback_count": len(FREE_FALLBACKS) + 1,
        }


# Global instance
mcp_specialist = MCPSpecialist()
