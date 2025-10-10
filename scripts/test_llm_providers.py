#!/usr/bin/env python3
"""Test external LLM providers (OpenAI GPT-4, GPT-3.5, Anthropic, Google)

Quick test script to verify LLM connectivity and quality.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.core.key_manager import KeyManager
from engine.runners.code_agent import CodeAgent


def test_openai_gpt4():
    """Test OpenAI GPT-4."""
    print("\n" + "="*80)
    print("🧪 Testing OpenAI GPT-4")
    print("="*80)
    
    try:
        # Create agent with GPT-4
        agent = CodeAgent(
            project_root=str(PROJECT_ROOT),
            llm_provider="openai",
            model="gpt-4"
        )
        
        print("✅ Agent initialized")
        
        # Test simple query
        prompt = "Write a Python function that calculates factorial. Just the code, no explanation."
        print(f"\n📝 Prompt: {prompt}")
        print("\n🤖 Response:")
        
        response = agent.query_llm(prompt=prompt, stream=False)
        print(response)
        
        print("\n✅ GPT-4 test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ GPT-4 test failed: {e}")
        return False


def test_openai_gpt35():
    """Test OpenAI GPT-3.5-turbo."""
    print("\n" + "="*80)
    print("🧪 Testing OpenAI GPT-3.5-turbo")
    print("="*80)
    
    try:
        # Create agent with GPT-3.5
        agent = CodeAgent(
            project_root=str(PROJECT_ROOT),
            llm_provider="openai",
            model="gpt-3.5-turbo"
        )
        
        print("✅ Agent initialized")
        
        # Test simple query
        prompt = "Write a Python function that reverses a string. Just the code, no explanation."
        print(f"\n📝 Prompt: {prompt}")
        print("\n🤖 Response:")
        
        response = agent.query_llm(prompt=prompt, stream=False)
        print(response)
        
        print("\n✅ GPT-3.5-turbo test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ GPT-3.5-turbo test failed: {e}")
        return False


def test_local_ollama():
    """Test local Ollama (Qwen)."""
    print("\n" + "="*80)
    print("🧪 Testing Local Ollama (Qwen)")
    print("="*80)
    
    try:
        # Create agent with local model
        agent = CodeAgent(
            project_root=str(PROJECT_ROOT),
            llm_provider="local",
            model="qwen2.5-coder:7b"
        )
        
        print("✅ Agent initialized")
        
        # Test simple query
        prompt = "Write a Python function that checks if a number is prime. Just the code, no explanation."
        print(f"\n📝 Prompt: {prompt}")
        print("\n🤖 Response:")
        
        response = agent.query_llm(prompt=prompt, stream=False)
        print(response)
        
        print("\n✅ Local Ollama test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Local Ollama test failed: {e}")
        return False


def compare_code_quality():
    """Compare code quality across different LLMs."""
    print("\n" + "="*80)
    print("📊 Code Quality Comparison Test")
    print("="*80)
    
    prompt = """Write a Python function that finds the longest palindromic substring.
Requirements:
- Function name: longest_palindrome
- Input: string
- Output: longest palindromic substring
- Include docstring
- Type hints
- Handle edge cases
"""
    
    print(f"\n📝 Common Prompt:\n{prompt}")
    
    results = {}
    
    # Test GPT-4
    print("\n" + "-"*80)
    print("🤖 GPT-4 Response:")
    print("-"*80)
    try:
        agent = CodeAgent(project_root=str(PROJECT_ROOT), llm_provider="openai", model="gpt-4")
        response = agent.query_llm(prompt=prompt, stream=False)
        print(response)
        results['gpt4'] = len(response)
    except Exception as e:
        print(f"❌ Error: {e}")
        results['gpt4'] = 0
    
    # Test GPT-3.5
    print("\n" + "-"*80)
    print("🤖 GPT-3.5-turbo Response:")
    print("-"*80)
    try:
        agent = CodeAgent(project_root=str(PROJECT_ROOT), llm_provider="openai", model="gpt-3.5-turbo")
        response = agent.query_llm(prompt=prompt, stream=False)
        print(response)
        results['gpt35'] = len(response)
    except Exception as e:
        print(f"❌ Error: {e}")
        results['gpt35'] = 0
    
    # Test Local
    print("\n" + "-"*80)
    print("🤖 Qwen (Local) Response:")
    print("-"*80)
    try:
        agent = CodeAgent(project_root=str(PROJECT_ROOT), llm_provider="local", model="qwen2.5-coder:7b")
        response = agent.query_llm(prompt=prompt, stream=False)
        print(response)
        results['qwen'] = len(response)
    except Exception as e:
        print(f"❌ Error: {e}")
        results['qwen'] = 0
    
    # Summary
    print("\n" + "="*80)
    print("📊 Comparison Summary:")
    print("="*80)
    print(f"GPT-4 response length: {results.get('gpt4', 0)} chars")
    print(f"GPT-3.5 response length: {results.get('gpt35', 0)} chars")
    print(f"Qwen response length: {results.get('qwen', 0)} chars")


def main():
    """Main test runner."""
    print("\n🚀 LLM Provider Test Suite")
    print("="*80)
    
    # Check API keys
    km = KeyManager()
    openai_key = km.get_key("OPENAI_API_KEY")
    
    if openai_key:
        print(f"✅ OpenAI API Key found: {km.mask_key(openai_key)}")
    else:
        print("❌ OpenAI API Key not found - OpenAI tests will fail")
    
    print("\nSelect test:")
    print("  1. Quick test - GPT-4")
    print("  2. Quick test - GPT-3.5-turbo")
    print("  3. Quick test - Local Ollama")
    print("  4. Full comparison test (all models)")
    print("  5. Run all quick tests")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        test_openai_gpt4()
    elif choice == "2":
        test_openai_gpt35()
    elif choice == "3":
        test_local_ollama()
    elif choice == "4":
        compare_code_quality()
    elif choice == "5":
        test_openai_gpt4()
        test_openai_gpt35()
        test_local_ollama()
    else:
        print("❌ Invalid choice")
        return 1
    
    print("\n✅ Test suite completed!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
