#!/usr/bin/env python3
"""
Test Qwen3 Coder 480B model via OpenRouter.

This script demonstrates how to use the free Qwen3 Coder model
for code generation and assistance.
"""

import sys
from pathlib import Path
import requests
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_api_key() -> str:
    """Load OpenRouter API key from secrets."""
    key_file = Path(__file__).parent.parent / "secrets/keys/openrouter.key"
    if not key_file.exists():
        raise FileNotFoundError(
            f"OpenRouter API key not found at {key_file}\n"
            "Please create this file with your API key."
        )
    return key_file.read_text().strip()


def chat_with_qwen(prompt: str, model: str = "qwen/qwen3-coder:free") -> dict:
    """
    Send a chat request to Qwen3 Coder via OpenRouter.
    
    Args:
        prompt: The user's question or request
        model: Model ID (default: qwen/qwen3-coder:free)
    
    Returns:
        Full API response as dict
    """
    api_key = load_api_key()
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/m0nk111/agent-forge",
            "X-Title": "Agent-Forge",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        },
        timeout=60
    )
    
    response.raise_for_status()
    return response.json()


def stream_chat_with_qwen(prompt: str, model: str = "qwen/qwen3-coder:free"):
    """
    Stream a chat request to Qwen3 Coder.
    
    Args:
        prompt: The user's question or request
        model: Model ID (default: qwen/qwen3-coder:free)
    
    Yields:
        Text chunks as they arrive
    """
    api_key = load_api_key()
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/m0nk111/agent-forge",
            "X-Title": "Agent-Forge",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": True
        },
        stream=True,
        timeout=60
    )
    
    response.raise_for_status()
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:]  # Remove 'data: ' prefix
                if data_str == '[DONE]':
                    break
                try:
                    data = json.loads(data_str)
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        if 'content' in delta:
                            yield delta['content']
                except json.JSONDecodeError:
                    continue


def main():
    """Main entry point."""
    print("🔧 Testing Qwen3 Coder 480B via OpenRouter\n")
    
    # Test 1: Simple code generation
    print("=" * 70)
    print("Test 1: Generate Python function")
    print("=" * 70)
    
    prompt1 = """Write a Python function that calculates the Fibonacci sequence 
using memoization for efficiency. Include docstring and type hints."""
    
    print(f"\n📝 Prompt: {prompt1}\n")
    print("🤖 Response (streaming):\n")
    
    for chunk in stream_chat_with_qwen(prompt1):
        print(chunk, end='', flush=True)
    
    print("\n\n")
    
    # Test 2: Code review
    print("=" * 70)
    print("Test 2: Code Review")
    print("=" * 70)
    
    prompt2 = """Review this code and suggest improvements:

def calc(x, y):
    if y == 0:
        return x
    else:
        return calc(y, x % y)

What does it do and how can it be improved?"""
    
    print(f"\n📝 Prompt: {prompt2}\n")
    print("🤖 Response:\n")
    
    response = chat_with_qwen(prompt2)
    answer = response['choices'][0]['message']['content']
    print(answer)
    
    # Show usage stats
    if 'usage' in response:
        usage = response['usage']
        print(f"\n📊 Token Usage:")
        print(f"  Prompt: {usage.get('prompt_tokens', 0)} tokens")
        print(f"  Completion: {usage.get('completion_tokens', 0)} tokens")
        print(f"  Total: {usage.get('total_tokens', 0)} tokens")
    
    print("\n✅ Tests completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
