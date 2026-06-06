import asyncio
import sys
import os
from utils.agent_router import SmartRouter

async def demo_opus_query():
    print("🚀 Initiating Query to Claude Opus 4.6 (via Remix IDE)...")
    router = SmartRouter()
    
    # Example trading query
    prompt = "Analyze the ETH/USDT chart. We see a bull flag forming on the 4H timeframe. What is your strategic recommendation?"
    
    print(f"\n[USER PROMPT]: {prompt}")
    print("-" * 50)
    
    # The router is configured to use Remix Opus as STEP 0 (Primary)
    response = router.query(
        prompt=prompt,
        agent_role="strategist",
        json_mode=True
    )
    
    print(f"\n[ROUTING STATS]: {router.get_stats()}")
    print("-" * 50)
    print(f"[OPUS 4.6 RESPONSE]:\n{response}")

if __name__ == "__main__":
    # Ensure we are in the project root to find utils
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(demo_opus_query())
