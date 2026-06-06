#!/usr/bin/env python3
"""
🚀 MINIMAX MODEL TEST
Test the exact minimax model code you provided.
"""

from openai import OpenAI

# Your exact code
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="nvapi-rhOOyATtggbGovkiXgE1kZXWn3VkSev0Hzms3d0_1m0thqUwvz3hGzYZ56极速赛车开奖直播-【🔥官网:ee1499.com🔥】-极速赛车开奖直播-极速赛车开奖直播开奖记录-澳洲极速赛车开奖直播kJV1J7"
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