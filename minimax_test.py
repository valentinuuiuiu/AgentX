#!/usr/bin/env python3
"""
🚀 MINIMAX MODEL TEST
Test the exact minimax model code you provided.
"""
import os

from openai import OpenAI

# Your exact code
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_NIM_API_KEY")
)

completion = client.chat.completions.create(
    model="minimaxai/minimax-m2.7",
    messages=[{"role":"user","content":"Hello! How does this minimax model work with NVIDIA?"}],
    temperature=1,
    top_p=0.95,
    max_tokens=8192,
    stream=True
)

print("🚀 Streaming response from minimax model:")
print("=" * 50)

for chunk in completion:
    if not getattr(chunk, "choices", None):
        continue
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")

print("\n" + "=" * 50)
print("✅ minimax model test completed!")