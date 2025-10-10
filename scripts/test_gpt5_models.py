#!/usr/bin/env python3
"""Test GPT-5 model availability and performance.

Tests all GPT-5 variants to determine which is best for coordinator role.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.core.key_manager import KeyManager
from engine.runners.code_agent import CodeAgent
import time


def test_gpt5_model(model_name: str, test_prompt: str = None):
    """Test a specific GPT-5 model variant."""
    
    if test_prompt is None:
        test_prompt = "Write a Python function to calculate fibonacci numbers. Just code, no explanation."
    
    print(f"\n{'='*80}")
    print(f"🧪 Testing {model_name}")
    print(f"{'='*80}")
    
    try:
        # Create agent with specified model
        start_time = time.time()
        agent = CodeAgent(
            project_root=str(PROJECT_ROOT),
            llm_provider="openai",
            model=model_name
        )
        init_time = time.time() - start_time
        print(f"✅ Agent initialized ({init_time:.2f}s)")
        
        # Test query
        print(f"\n📝 Prompt: {test_prompt[:80]}...")
        
        start_time = time.time()
        response = agent.query_llm(prompt=test_prompt, stream=False)
        response_time = time.time() - start_time
        
        print(f"\n🤖 Response ({response_time:.2f}s):")
        print("-" * 80)
        print(response[:500])
        if len(response) > 500:
            print(f"... ({len(response) - 500} more characters)")
        print("-" * 80)
        
        # Estimate tokens and cost
        est_tokens = len(response.split())
        print(f"\n📊 Stats:")
        print(f"  - Response time: {response_time:.2f}s")
        print(f"  - Response length: {len(response)} chars, ~{est_tokens} tokens")
        print(f"  - Speed: ~{est_tokens/response_time:.0f} tokens/sec")
        
        print(f"\n✅ {model_name} test successful!")
        return {
            'success': True,
            'model': model_name,
            'response_time': response_time,
            'response_length': len(response),
            'tokens': est_tokens,
            'speed': est_tokens/response_time
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ {model_name} test failed!")
        print(f"   Error: {error_msg[:200]}")
        
        # Check if model doesn't exist
        if 'does not exist' in error_msg or 'model_not_found' in error_msg:
            print(f"   Status: Model not available yet")
        else:
            print(f"   Status: API error or quota issue")
        
        return {
            'success': False,
            'model': model_name,
            'error': error_msg[:200]
        }


def test_all_gpt5_models():
    """Test all GPT-5 model variants."""
    
    print("\n" + "="*80)
    print("🚀 GPT-5 MODEL AVAILABILITY TEST")
    print("="*80)
    
    # All GPT-5 variants from user's info
    gpt5_models = [
        # Main models
        ('gpt-5', 'GPT-5 (latest/default)'),
        ('gpt-5-chat-latest', 'GPT-5 Chat Latest'),
        
        # Dated versions
        ('gpt-5-2025-08-07', 'GPT-5 (August 2025)'),
        
        # Specialized variants
        ('gpt-5-pro', 'GPT-5 Pro (highest quality)'),
        ('gpt-5-pro-2025-10-06', 'GPT-5 Pro (October 2025)'),
        ('gpt-5-codex', 'GPT-5 Codex (coding specialist)'),
        
        # Smaller/faster variants
        ('gpt-5-mini', 'GPT-5 Mini (fast/cheap)'),
        ('gpt-5-mini-2025-08-07', 'GPT-5 Mini (August 2025)'),
        ('gpt-5-nano', 'GPT-5 Nano (smallest/fastest)'),
        ('gpt-5-nano-2025-08-07', 'GPT-5 Nano (August 2025)'),
    ]
    
    results = []
    
    print(f"\n📋 Testing {len(gpt5_models)} GPT-5 variants...")
    print(f"   This will take a few minutes...\n")
    
    for model_id, model_desc in gpt5_models:
        print(f"\n[{len(results)+1}/{len(gpt5_models)}] {model_desc}")
        result = test_gpt5_model(model_id)
        results.append(result)
        
        # Add small delay between tests
        if result['success']:
            time.sleep(1)
    
    return results


def print_summary(results):
    """Print summary of all test results."""
    
    print("\n" + "="*80)
    print("📊 GPT-5 MODEL COMPARISON SUMMARY")
    print("="*80)
    
    # Separate successful and failed tests
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n✅ Available Models: {len(successful)}/{len(results)}")
    print(f"❌ Unavailable Models: {len(failed)}/{len(results)}")
    
    if successful:
        print("\n" + "-"*80)
        print("Available GPT-5 Models (sorted by speed):")
        print("-"*80)
        
        # Sort by speed
        successful.sort(key=lambda x: x['speed'], reverse=True)
        
        print(f"\n{'Model':<30} {'Speed':<15} {'Time':<10} {'Length':<10}")
        print("-"*80)
        
        for r in successful:
            model = r['model'][:28]
            speed = f"{r['speed']:.0f} tok/s"
            resp_time = f"{r['response_time']:.2f}s"
            length = f"{r['tokens']} tok"
            
            print(f"{model:<30} {speed:<15} {resp_time:<10} {length:<10}")
    
    if failed:
        print("\n" + "-"*80)
        print("Unavailable Models:")
        print("-"*80)
        for r in failed:
            print(f"  ❌ {r['model']}")
            print(f"     {r['error'][:70]}...")
    
    # Recommendations
    if successful:
        print("\n" + "="*80)
        print("🎯 RECOMMENDATIONS FOR COORDINATOR ROLE")
        print("="*80)
        
        # Find best models
        fastest = max(successful, key=lambda x: x['speed'])
        
        print(f"\n🚀 Fastest: {fastest['model']}")
        print(f"   Speed: {fastest['speed']:.0f} tokens/sec")
        print(f"   Time: {fastest['response_time']:.2f}s")
        
        # Check for Pro and Codex variants
        pro_models = [r for r in successful if 'pro' in r['model']]
        codex_models = [r for r in successful if 'codex' in r['model']]
        
        if pro_models:
            print(f"\n⭐ Best Quality: {pro_models[0]['model']}")
            print(f"   (Pro variant - highest quality)")
        
        if codex_models:
            print(f"\n💻 Best for Code: {codex_models[0]['model']}")
            print(f"   (Codex variant - coding specialist)")
        
        print("\n📝 Usage:")
        print(f"   python3 scripts/launch_agent.py --agent coordinator-gpt5")
        print(f"   (after creating config with best model)")


def compare_with_gpt4o():
    """Compare GPT-5 with current GPT-4o."""
    
    print("\n" + "="*80)
    print("⚖️  GPT-5 vs GPT-4o COMPARISON")
    print("="*80)
    
    test_prompt = "Write a Python function to find all prime numbers up to n. Just code."
    
    print("\n📝 Test: Prime number finder function\n")
    
    # Test GPT-4o
    print("Testing current coordinator model (GPT-4o)...")
    gpt4o_result = test_gpt5_model("gpt-4o", test_prompt)
    
    # Test GPT-5 (default)
    print("\nTesting GPT-5 (default)...")
    gpt5_result = test_gpt5_model("gpt-5", test_prompt)
    
    # Compare
    if gpt4o_result['success'] and gpt5_result['success']:
        print("\n" + "="*80)
        print("📊 DIRECT COMPARISON")
        print("="*80)
        
        print(f"\n{'Metric':<25} {'GPT-4o':<20} {'GPT-5':<20} {'Winner':<10}")
        print("-"*80)
        
        # Response time
        time_diff = ((gpt5_result['response_time'] - gpt4o_result['response_time']) / 
                     gpt4o_result['response_time'] * 100)
        time_winner = "GPT-5" if gpt5_result['response_time'] < gpt4o_result['response_time'] else "GPT-4o"
        print(f"{'Response Time':<25} {gpt4o_result['response_time']:.2f}s{'':<15} "
              f"{gpt5_result['response_time']:.2f}s{'':<15} {time_winner:<10}")
        
        # Speed
        speed_winner = "GPT-5" if gpt5_result['speed'] > gpt4o_result['speed'] else "GPT-4o"
        print(f"{'Speed':<25} {gpt4o_result['speed']:.0f} tok/s{'':<11} "
              f"{gpt5_result['speed']:.0f} tok/s{'':<11} {speed_winner:<10}")
        
        print(f"\n💡 Performance: GPT-5 is {abs(time_diff):.0f}% {'faster' if time_diff < 0 else 'slower'} than GPT-4o")
        
        if time_diff < -10:
            print("   ✅ GPT-5 is significantly faster - RECOMMENDED upgrade!")
        elif time_diff < 10:
            print("   ⚖️  Similar performance - consider other factors (quality, cost)")
        else:
            print("   ⚠️  GPT-5 is slower - may want to stick with GPT-4o")


def main():
    """Main test runner."""
    
    # Check API key
    km = KeyManager()
    api_key = km.get_key('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key found!")
        print("   Add OPENAI_API_KEY to keys.json")
        return 1
    
    print(f"✅ OpenAI API Key found: {api_key[:8]}...{api_key[-6:]}")
    
    # Run tests
    print("\n" + "="*80)
    print("Starting GPT-5 model tests...")
    print("="*80)
    
    # Test all GPT-5 variants
    results = test_all_gpt5_models()
    
    # Print summary
    print_summary(results)
    
    # Compare with GPT-4o
    if any(r['success'] for r in results):
        compare_with_gpt4o()
    
    print("\n" + "="*80)
    print("✅ GPT-5 Testing Complete!")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
