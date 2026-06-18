#!/usr/bin/env python3
"""
Minimax test with OpenAI client and longer timeout
"""
import os

from openai import OpenAI
import time

print("Testing minimax with OpenAI client...")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_NIM_API_KEY")
)

try:
    start_time = time.time()
    
    # Try with a very simple request and longer timeout
    completion = client.chat.completions.create(
        model="minimaxai/minimax-m2.7",
        messages=[{"role":"user","content":"Hello"}],
        temperature=0.7,
        max_tokens=10,
        stream=False,
        timeout=30  # Longer timeout
    )
    
    end_time = time.time()
    
    print(f"✅ Success! Response time: {end_time - start_time:.2f} seconds")
    print("Response:", completion.choices[0].message.content)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")