
"""
NVIDIA-BabyAGI Integration Module

This module configures BabyAGI to use NVIDIA's API endpoint instead of OpenAI.
"""

import os
import litellm
from litellm import completion

def configure_nvidia():
    """Configure LiteLLM for NVIDIA endpoint."""
    # Set NVIDIA configuration
    nvidia_config = {
        "api_base": "https://integrate.api.nvidia.com/v1",
        "api_key": os.environ.get("NVIDIA_API_KEY"),
        "model": "nvidia/llama-3-70b-instruct"
    }
    
    # Update litellm settings
    litellm.api_base = nvidia_config["api_base"]
    
    print("✅ NVIDIA endpoint configured for LiteLLM")
    print(f"   API Base: {nvidia_config['api_base']}")
    print(f"   Model: {nvidia_config['model']}")
    
    return nvidia_config

def nvidia_completion(prompt, **kwargs):
    """Execute completion using NVIDIA endpoint."""
    config = configure_nvidia()
    
    # Use NVIDIA endpoint
    response = completion(
        model=config["model"],
        messages=[{"role": "user", "content": prompt}],
        api_base=config["api_base"],
        api_key=config["api_key"],
        **kwargs
    )
    
    return response

# Auto-configure on import
try:
    configure_nvidia()
    print("🧠 NVIDIA-BabyAGI integration ready")
except Exception as e:
    print(f"❌ NVIDIA configuration failed: {e}")
