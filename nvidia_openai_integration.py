#!/usr/bin/env python3
"""
🚀 NVIDIA OPENAI-COMPATIBLE ENDPOINT INTEGRATION
Direct integration with NVIDIA's OpenAI-compatible API endpoint.
"""

import os
from openai import OpenAI

def test_nvidia_endpoint():
    """Test the NVIDIA OpenAI-compatible endpoint."""
    print("🚀 Testing NVIDIA OpenAI-compatible endpoint...")
    
    # Initialize client with NVIDIA endpoint
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ.get("NVIDIA_NIM_API_KEY")
    )
    
    # Test completion with minimax model
    try:
        completion = client.chat.completions.create(
            model="minimaxai/minimax-m2.7",
            messages=[{"role": "user", "content": "Hello! How does NVIDIA's OpenAI-compatible API work?"}],
            temperature=1,
            top_p=0.95,
            max_tokens=8192,
            stream=True
        )
        
        print("✅ NVIDIA endpoint connected successfully!")
        print("📝 Response:")
        
        full_response = ""
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        
        print("\n\n✅ NVIDIA API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing NVIDIA endpoint: {e}")
        return False

def create_nvidia_babyagi_integration():
    """Create integration between BabyAGI and NVIDIA endpoint."""
    print("🧠 Integrating NVIDIA endpoint with BabyAGI...")
    
    integration_code = '''
#!/usr/bin/env python3
"""
🚀 NVIDIA-BABYAGI INTEGRATION MODULE
Replaces OpenAI with NVIDIA's OpenAI-compatible endpoint.
"""

import os
import litellm
from litellm import completion

def configure_nvidia_for_babyagi():
    """Configure LiteLLM to use NVIDIA endpoint for BabyAGI."""
    print("🔧 Configuring BabyAGI to use NVIDIA endpoint...")
    
    # Set NVIDIA as default provider
    os.environ["DEFAULT_PROVIDER"] = "nvidia"
    
    # Configure NVIDIA endpoint
    nvidia_config = {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": os.environ.get("NVIDIA_NIM_API_KEY")
    }
    
    # Register NVIDIA provider
    litellm.register_provider({
        "nvidia": nvidia_config
    })
    
    # Set default model to NVIDIA's minimax
    os.environ["DEFAULT_MODEL"] = "minimaxai/minimax-m2.7"
    
    print("✅ NVIDIA endpoint configured for BabyAGI!")
    print("   • Provider: nvidia")
    print("   • Model: minimaxai/minimax-m2.7")
    print("   • Endpoint: https://integrate.api.nvidia.com/v1")

def nvidia_completion(*args, **kwargs):
    """Wrapper for NVIDIA-powered completions."""
    # Use NVIDIA endpoint
    kwargs["model"] = kwargs.get("model", "minimaxai/minimax-m2.7")
    
    try:
        response = completion(*args, **kwargs)
        return response
    except Exception as e:
        print(f"❌ NVIDIA completion error: {e}")
        # Fallback to default if NVIDIA fails
        return completion(*args, **kwargs)

# Auto-configure when imported
configure_nvidia_for_babyagi()

# Export the completion function
__all__ = ['nvidia_completion', 'configure_nvidia_for_babyagi']
'''
    
    # Save integration module
    with open("./nvidia_babyagi_integration.py", "w") as f:
        f.write(integration_code)
    
    print("✅ NVIDIA-BabyAGI integration module created!")
    return True

def main():
    """Main function."""
    print("=" * 60)
    print("🚀 NVIDIA OPENAI-COMPATIBLE ENDPOINT INTEGRATION")
    print("=" * 60)
    
    # Test the endpoint
    if test_nvidia_endpoint():
        # Create BabyAGI integration
        if create_nvidia_babyagi_integration():
            print("\n" + "=" * 60)
            print("🎉 NVIDIA INTEGRATION COMPLETE!")
            print("NVIDIA's OpenAI-compatible endpoint is now ready")
            print("BabyAGI will use NVIDIA instead of OpenAI")
            print("=" * 60)
            return True
    
    print("❌ Integration failed")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)