#!/usr/bin/env python3
"""Quick comparison: GPT-5 vs GPT-4o for coordinator role."""

import sys
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.core.key_manager import KeyManager
from engine.runners.code_agent import CodeAgent


def quick_test(model_name: str):
    """Quick test of a model."""
    test_prompt = """Break down this task into subtasks:
Task: Add user authentication to a web application
- List 5-7 concrete implementation steps
- Be specific and actionable"""
    
    print(f"\n{'='*70}")
    print(f"Testing: {model_name}")
    print(f"{'='*70}")
    
    try:
        agent = CodeAgent(
            project_root=str(PROJECT_ROOT),
            llm_provider="openai",
            model=model_name
        )
        
        start = time.time()
        response = agent.query_llm(prompt=test_prompt, stream=False)
        elapsed = time.time() - start
        
        tokens = len(response.split())
        
        print(f"✅ Response in {elapsed:.2f}s")
        print(f"   Tokens: ~{tokens}")
        print(f"   Speed: ~{tokens/elapsed:.0f} tok/s")
        print(f"\n📝 Response preview:")
        print(response[:300] + "...")
        
        return {
            'model': model_name,
            'time': elapsed,
            'tokens': tokens,
            'speed': tokens/elapsed,
            'success': True
        }
        
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
        return {'model': model_name, 'success': False, 'error': str(e)}


def main():
    """Compare GPT-5 vs GPT-4o."""
    
    km = KeyManager()
    if not km.get_key('OPENAI_API_KEY'):
        print("❌ No API key!")
        return 1
    
    print("\n🚀 GPT-5 vs GPT-4o: Coordinator Task Comparison")
    print("="*70)
    
    # Test both models
    models_to_test = [
        ('gpt-4o', 'GPT-4o (current)'),
        ('gpt-5-chat-latest', 'GPT-5 Chat Latest'),
    ]
    
    results = []
    for model_id, desc in models_to_test:
        print(f"\n[{len(results)+1}/{len(models_to_test)}] {desc}")
        result = quick_test(model_id)
        results.append(result)
        time.sleep(1)
    
    # Summary
    print("\n" + "="*70)
    print("📊 COMPARISON SUMMARY")
    print("="*70)
    
    successful = [r for r in results if r['success']]
    if len(successful) >= 2:
        gpt4o = successful[0]
        gpt5 = successful[1]
        
        print(f"\n{'Metric':<20} {'GPT-4o':<20} {'GPT-5':<20} {'Diff'}")
        print("-"*70)
        
        time_diff = ((gpt5['time'] - gpt4o['time']) / gpt4o['time']) * 100
        print(f"{'Response Time':<20} {gpt4o['time']:.2f}s{'':<15} {gpt5['time']:.2f}s{'':<15} "
              f"{time_diff:+.0f}%")
        
        speed_diff = ((gpt5['speed'] - gpt4o['speed']) / gpt4o['speed']) * 100
        print(f"{'Speed':<20} {gpt4o['speed']:.0f} tok/s{'':<11} {gpt5['speed']:.0f} tok/s{'':<11} "
              f"{speed_diff:+.0f}%")
        
        print(f"\n{'='*70}")
        if time_diff < -10:
            print("✅ VERDICT: GPT-5 is significantly FASTER - UPGRADE RECOMMENDED!")
        elif time_diff < 10:
            print("⚖️  VERDICT: Similar performance - test quality/features")
        else:
            print("⚠️  VERDICT: GPT-4o is faster - may want to keep current")
        print(f"{'='*70}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
