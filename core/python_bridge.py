import os
import requests

def get_deepseek_reasoning(market_data, ta_signals):
    """Get reasoning from Deepseek API"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ.get('DEEPSEEK_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a financial analyst AI."},
            {"role": "user", "content": f"Analyze this market data: {market_data} and these technical signals: {ta_signals}."}
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]
