#!/usr/bin/env python3
"""
🚀 NVIDIA MINIMAX INTEGRATION
Direct integration with NVIDIA's OpenAI-compatible API using minimax model.
"""

import os
from openai import OpenAI

def test_minimax_model():
    """Test the minimax model with NVIDIA endpoint."""
    print("🚀 Testing minimax model with NVIDIA endpoint...")
    
    # Initialize client with your NVIDIA endpoint and API key
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ.get("NVIDIA_NIM_KEY", "")
    )
    
    # Test completion with minimax model
    try:
        completion = client.chat.completions.create(
            model="minimaxai/minimax-m2.7",
            messages=[{"role": "user", "content": "Hello! Explain how this minimax model works with NVIDIA's API."}],
            temperature=1,
            top_p=0.95,
            max_tokens=8192,
            stream=True
        )
        
        print("✅ minimax model connected successfully!")
        print("📝 Response:")
        
        full_response = ""
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        
        print("\n\n✅ minimax model test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing minimax model: {e}")
        return False

def create_minimax_integration():
    """Create integration script for minimax model."""
    print("🔧 Creating minimax model integration...")
    
    integration_code = '''
#!/usr/bin/env python3
"""
🚀 MINIMAX MODEL INTEGRATION
Ready-to-use minimax model with NVIDIA endpoint.
"""

import os
from openai import OpenAI

class MinimaxClient:
    """Client for minimax model through NVIDIA endpoint."""
    
    def __init__(self):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.environ.get("NVIDIA_NIM_KEY", "")
        )
        self.model = "minimaxai/minimax-m2.7"
    
    def chat_completion(self, messages, **kwargs):
        """Create chat completion with minimax model."""
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get('temperature', 1),
            top_p=kwargs.get('top_p', 0.95),
            max_tokens=kwargs.get('max_tokens', 8192),
            stream=kwargs.get('stream', True)
        )
    
    def generate_response(self, prompt, **kwargs):
        """Generate response for a single prompt."""
        messages = [{"role": "user", "content": prompt}]
        completion = self.chat_completion(messages, **kwargs)
        
        response = ""
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content
        
        return response

# Create global client instance
minimax_client = MinimaxClient()

def minimax_chat(messages, **kwargs):
    """Global function for minimax chat completions."""
    return minimax_client.chat_completion(messages, **kwargs)

def minimax_generate(prompt, **kwargs):
    """Global function for minimax text generation."""
    return minimax_client.generate_response(prompt, **kwargs)

if __name__ == "__main__":
    # Test the integration
    print("Testing minimax integration...")
    response = minimax_generate("Hello! How does this minimax model work?")
    print("Response:", response)
'''
    
    # Save integration script
    with open("/home/aryan/free-claude/bittensor/clean_rehoboam_project/minimax_integration.py", "w") as f:
        f.write(integration_code)
    
    print("✅ minimax integration script created!")
    return True

def main():
    """Main function."""
    print("=" * 60)
    print("🚀 MINIMAX MODEL INTEGRATION WITH NVIDIA")
    print("=" * 60)
    
    # Test the minimax model
    if test_minimax_model():
        # Create integration script
        if create_minimax_integration():
            print("\n" + "=" * 60)
            print("🎉 MINIMAX INTEGRATION COMPLETE!")
            print("minimaxai/minimax-m2.7 model is now ready to use")
            print("Access via: from minimax_integration import minimax_client")
            print("=" * 60)
            return True
    
    print("❌ Integration failed")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)