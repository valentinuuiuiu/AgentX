import sys
import json
from openai import OpenAI
from ta_engine import TAEngine
from risk_manager import RiskManager

# Nvidia NIM API Setup for DeepSeek V4 Pro
NVIDIA_API_KEY = "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"

def get_deepseek_reasoning(market_data, ta_signals):
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY
    )

    prompt = f"""
    You are AgentX, a Neuromorphic Trading Syndicate mastermind.
    Analyze the following market data and Technical Analysis (TA) signals.
    Provide a definitive trading action (BUY, SELL, or HOLD) and your deep reasoning.
    
    Market Data Context:
    {json.dumps(market_data, indent=2)}
    
    TA Engine Signals:
    {json.dumps(ta_signals, indent=2)}
    
    Respond in strict JSON format:
    {{
        "action": "BUY/SELL/HOLD",
        "confidence": 0-100,
        "reasoning": "your deep analysis here"
    }}
    """

    completion = client.chat.completions.create(
        model="deepseek-ai/deepseek-v4-pro",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        top_p=0.95,
        max_tokens=2048,
        extra_body={"chat_template_kwargs": {"thinking": False}},
        stream=False
    )
    
    return completion.choices[0].message.content

def main():
    try:
        # Read input from standard input (Node.js will pipe this)
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({"error": "No input data provided"}))
            return
            
        data = json.loads(input_data)
        prices = data.get("prices", [])
        
        if len(prices) < 14:
            print(json.dumps({"error": "Not enough price data for TA (need at least 14 periods)"}))
            return

        # 1. Run Core Python TA Engine
        ta = TAEngine()
        rsi = ta.calculate_rsi(prices, period=14)
        
        # We can add more indicators here as needed
        ta_signals = {
            "RSI_14": rsi,
            "trend": "Oversold" if rsi and rsi < 30 else "Overbought" if rsi and rsi > 70 else "Neutral"
        }
        
        # 2. Run Risk Manager
        rm = RiskManager(max_position=1000.0)
        risk_status = "OK"  # Placeholder for complex risk logic
        
        # 3. Get DeepSeek V4 Pro Reasoning
        deepseek_response = get_deepseek_reasoning(data, ta_signals)
        
        # 4. Return combined result to Node.js
        result = {
            "ta_engine": ta_signals,
            "risk_manager": risk_status,
            "llm_analysis": json.loads(deepseek_response) if deepseek_response.startswith("{") else deepseek_response
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
