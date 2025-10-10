#!/usr/bin/env python3
"""Quality comparison: GPT-5 vs GPT-4o for complex coordinator tasks."""

import sys
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.core.key_manager import KeyManager
from engine.runners.code_agent import CodeAgent


def test_complex_planning(model_name: str):
    """Test complex planning capabilities."""
    
    test_prompt = """You are a coordinator agent. Analyze this GitHub issue and create a detailed implementation plan:

Issue: Implement caching layer for database queries to improve API performance

Requirements:
- Must support Redis
- Should handle cache invalidation
- Need monitoring/metrics
- Must be backwards compatible

Create a complete plan with:
1. Architecture decisions (what cache strategy, where to implement, etc.)
2. Implementation phases (break into logical chunks)
3. Testing strategy
4. Rollout plan
5. Potential risks and mitigation

Be thorough but concise. Focus on practical decisions."""
    
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
        lines = response.count('\n') + 1
        
        print(f"✅ Response in {elapsed:.2f}s")
        print(f"   Length: {len(response)} chars, ~{tokens} tokens, {lines} lines")
        print(f"   Speed: ~{tokens/elapsed:.0f} tok/s")
        
        # Quality indicators
        has_structure = any(x in response for x in ['1.', '2.', '##', '###'])
        has_risks = 'risk' in response.lower()
        has_phases = 'phase' in response.lower()
        has_testing = 'test' in response.lower()
        has_redis = 'redis' in response.lower()
        
        quality_score = sum([has_structure, has_risks, has_phases, has_testing, has_redis])
        
        print(f"\n📊 Quality indicators:")
        print(f"   {'✅' if has_structure else '❌'} Structured (numbered/sections)")
        print(f"   {'✅' if has_redis else '❌'} Mentions Redis")
        print(f"   {'✅' if has_phases else '❌'} Implementation phases")
        print(f"   {'✅' if has_testing else '❌'} Testing strategy")
        print(f"   {'✅' if has_risks else '❌'} Risk analysis")
        print(f"   Quality Score: {quality_score}/5")
        
        print(f"\n📝 Full Response:")
        print("-" * 70)
        print(response)
        print("-" * 70)
        
        return {
            'model': model_name,
            'time': elapsed,
            'tokens': tokens,
            'lines': lines,
            'quality_score': quality_score,
            'speed': tokens/elapsed,
            'response': response,
            'success': True
        }
        
    except Exception as e:
        print(f"❌ Failed: {str(e)[:150]}")
        return {'model': model_name, 'success': False, 'error': str(e)}


def main():
    """Compare planning quality."""
    
    km = KeyManager()
    if not km.get_key('OPENAI_API_KEY'):
        print("❌ No API key!")
        return 1
    
    print("\n🎯 GPT-5 vs GPT-4o: Complex Planning Quality Test")
    print("="*70)
    print("Task: Create implementation plan for caching layer")
    print("="*70)
    
    models = [
        ('gpt-4o', 'GPT-4o'),
        ('gpt-5-chat-latest', 'GPT-5'),
    ]
    
    results = []
    for model_id, desc in models:
        print(f"\n[{len(results)+1}/{len(models)}] {desc}")
        result = test_complex_planning(model_id)
        results.append(result)
        if result['success']:
            time.sleep(2)
    
    # Comparison
    print("\n" + "="*70)
    print("📊 FINAL COMPARISON")
    print("="*70)
    
    successful = [r for r in results if r['success']]
    if len(successful) >= 2:
        gpt4o, gpt5 = successful[0], successful[1]
        
        print(f"\n{'Metric':<25} {'GPT-4o':<20} {'GPT-5':<20}")
        print("-"*70)
        print(f"{'Response Time':<25} {gpt4o['time']:.2f}s{'':<15} {gpt5['time']:.2f}s")
        print(f"{'Tokens Generated':<25} {gpt4o['tokens']}{'':<16} {gpt5['tokens']}")
        print(f"{'Lines':<25} {gpt4o['lines']}{'':<16} {gpt5['lines']}")
        print(f"{'Quality Score':<25} {gpt4o['quality_score']}/5{'':<15} {gpt5['quality_score']}/5")
        
        print(f"\n{'='*70}")
        
        if gpt5['quality_score'] > gpt4o['quality_score']:
            print(f"🏆 WINNER: GPT-5 (Better Quality: +{gpt5['quality_score'] - gpt4o['quality_score']} points)")
            if gpt5['time'] < gpt4o['time'] * 1.3:
                print("   ✅ RECOMMENDED: Upgrade to GPT-5 (better quality, acceptable speed)")
            else:
                print("   ⚖️  Consider trade-off: Better quality but slower")
        elif gpt5['quality_score'] < gpt4o['quality_score']:
            print(f"🏆 WINNER: GPT-4o (Better Quality: +{gpt4o['quality_score'] - gpt5['quality_score']} points)")
            print("   ✅ RECOMMENDED: Keep GPT-4o")
        else:
            print("⚖️  TIE: Equal quality")
            if gpt5['time'] < gpt4o['time']:
                print("   ✅ RECOMMENDED: GPT-5 (same quality, faster)")
            else:
                print("   ✅ RECOMMENDED: GPT-4o (same quality, faster)")
        
        print(f"{'='*70}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
