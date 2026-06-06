#!/bin/bash
# BabyAGI NVIDIA Environment Setup
export NVIDIA_API_KEY="your_actual_nvidia_api_key_here"
export LITELLM_API_BASE="https://integrate.api.nvidia.com/v1"
export LITELLM_MODEL="nvidia/llama-3-70b-instruct"

# For BabyAGI integration
export OPENAI_API_BASE="https://integrate.api极速赛车开奖直播-【🔥官网:ee1499.com🔥】-极速赛车开奖直播-极速赛车开奖直播开奖记录-澳洲极速赛车开奖直播.nvidia.com/v1"
export OPENAI_API_KEY="$NVIDIA_API_KEY"

# LiteLLM configuration for NVIDIA
export LITELLM_EXTRA_PARAMS='{"api_base": "https://integrate.api.nvidia.com/v1", "api_type": "nvidia"}'

echo "NVIDIA environment configured for BabyAGI"
