import os
import requests, json

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = True

headers = {
  "Authorization": f"Bearer {os.environ.get('NVIDIA_NIM_KEY', '')}",
  "Accept": "text/event-stream" if stream else "application/json"
}

payload = {
  "model": "moonshotai/kimi-k2.5",
  "messages": [{"role":"user","content":"Hello! Testing Kimi model with NVIDIA."}],
  "max_tokens": 16384,
  "temperature": 1.00,
  "top_p": 1.00,
  "stream": stream,
  "chat_template_kwargs": {"thinking":True},
}

print("🚀 Testing Kimi model with NVIDIA API...")
print("=" * 60)

response = requests.post(invoke_url, headers=headers, json=payload)

if stream:
    full_response = ""
    reasoning = ""
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode("utf-8")
            if line_str.startswith("data: {"):
                try:
                    data = json.loads(line_str[6:])  # Remove "data: " prefix
                    
                    if "choices" in data and data["choices"]:
                        choice = data["choices"][0]
                        
                        if "delta" in choice:
                            delta = choice["delta"]
                            
                            # Capture reasoning process
                            if "reasoning" in delta:
                                reasoning += delta["reasoning"]
                            
                            # Capture final response
                            if "content" in delta:
                                full_response += delta["content"]
                                print(delta["content"], end="", flush=True)
                                
                except json.JSONDecodeError:
                    continue
                    
    print("\n" + "=" * 60)
    print("✅ Kimi model test successful!")
    
    # Show the reasoning process if you want to see it
    if reasoning:
        print("\n🤔 Reasoning Process:")
        print(reasoning)
        
else:
    print(response.json())