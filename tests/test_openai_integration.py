#!/usr/bin/env python3
"""
Test OpenAI Integration with KeyManager and LLM Providers.

Validates:
1. Key loading from keys.json
2. OpenAI connection test
3. GPT-4 chat completion
4. Error handling and fallback

Author: Agent Forge
Date: 2025-10-10
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.core.key_manager import KeyManager
from engine.core.llm_providers import OpenAIProvider, LLMMessage


def test_key_loading():
    """Test 1: Key loading from keys.json"""
    print("\n" + "="*70)
    print("🔑 TEST 1: Key Loading from keys.json")
    print("="*70)
    
    km = KeyManager()
    key = km.get_key("OPENAI_API_KEY")
    
    if key:
        masked = km.mask_key(key)
        print(f"✅ Key loaded successfully")
        print(f"📋 Masked key: {masked}")
        print(f"📏 Key length: {len(key)} chars")
        return key
    else:
        print(f"❌ Key NOT found in keys.json")
        return None


def test_connection(api_key: str):
    """Test 2: OpenAI connection test"""
    print("\n" + "="*70)
    print("🌐 TEST 2: OpenAI Connection Test")
    print("="*70)
    
    try:
        provider = OpenAIProvider(api_key=api_key)
        
        if provider.test_connection():
            print("✅ Connection successful!")
            
            # Get available models
            models = provider.get_available_models()
            print(f"📋 Available models: {len(models)}")
            for model in models:
                print(f"   - {model}")
            
            return provider
        else:
            print("❌ Connection failed")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_chat_completion(provider: OpenAIProvider):
    """Test 3: GPT-4 chat completion"""
    print("\n" + "="*70)
    print("💬 TEST 3: GPT-4 Chat Completion")
    print("="*70)
    
    try:
        messages = [
            LLMMessage(role="system", content="You are a helpful Python expert."),
            LLMMessage(role="user", content="Write a one-line Python function that adds two numbers. Just the code, no explanation.")
        ]
        
        print("📤 Sending test query to GPT-4...")
        
        response = provider.chat_completion(
            messages=messages,
            model="gpt-4",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"✅ Response received!")
        print(f"📝 Model: {response.model}")
        print(f"🎯 Finish reason: {response.finish_reason}")
        print(f"📊 Usage: {response.usage}")
        print(f"\n💡 Response content:")
        print(f"{'─'*70}")
        print(response.content)
        print(f"{'─'*70}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_generation(provider: OpenAIProvider):
    """Test 4: Code generation for calculator module"""
    print("\n" + "="*70)
    print("🔧 TEST 4: Code Generation (Calculator Module)")
    print("="*70)
    
    try:
        messages = [
            LLMMessage(
                role="system",
                content="You are an expert Python developer. Generate clean, well-documented code."
            ),
            LLMMessage(
                role="user",
                content="""Generate a Python calculator module with these functions:
- add(a, b): Add two numbers
- subtract(a, b): Subtract b from a
- multiply(a, b): Multiply two numbers
- divide(a, b): Divide a by b (handle division by zero)

Include type hints, docstrings, and proper error handling.
Output ONLY the Python code, no markdown blocks."""
            )
        ]
        
        print("📤 Generating calculator module...")
        
        response = provider.chat_completion(
            messages=messages,
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
        
        print(f"✅ Code generated!")
        print(f"📏 Length: {len(response.content)} chars")
        print(f"📊 Tokens: {response.usage}")
        print(f"\n💡 Generated code (first 500 chars):")
        print(f"{'─'*70}")
        print(response.content[:500] + "...")
        print(f"{'─'*70}")
        
        return True
        
    except Exception as e:
        print(f"❌ Code generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all OpenAI integration tests"""
    print("\n🤖 OpenAI Integration Test Suite")
    print("="*70)
    
    # Test 1: Key loading
    api_key = test_key_loading()
    if not api_key:
        print("\n❌ FAILED: Cannot proceed without API key")
        return False
    
    # Test 2: Connection
    provider = test_connection(api_key)
    if not provider:
        print("\n❌ FAILED: Cannot connect to OpenAI")
        return False
    
    # Test 3: Chat completion
    if not test_chat_completion(provider):
        print("\n❌ FAILED: Chat completion error")
        return False
    
    # Test 4: Code generation
    if not test_code_generation(provider):
        print("\n❌ FAILED: Code generation error")
        return False
    
    # All tests passed
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\n📋 Summary:")
    print("   ✅ Key loading works")
    print("   ✅ OpenAI connection works")
    print("   ✅ Chat completion works")
    print("   ✅ Code generation works")
    print("\n🎉 OpenAI integration is ready for production use!")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
