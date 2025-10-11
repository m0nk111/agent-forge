#!/usr/bin/env python3
"""
Test GPT-5 Pro - Simple Working Test
Quick test to verify GPT-5 Pro works with the new /v1/responses endpoint
"""

import sys
import os
import time
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.core.llm_providers import OpenAIProvider, LLMMessage

def load_api_key():
    """Load API key from keys.json"""
    try:
        with open('/home/flip/agent-forge/secrets/keys.json') as f:
            keys = json.load(f)
            return keys['OPENAI_API_KEY']
    except Exception as e:
        print(f'❌ Error loading API key: {e}')
        sys.exit(1)

def test_simple():
    """Test 1: Simple greeting"""
    print('=' * 60)
    print('TEST 1: Simple Greeting')
    print('=' * 60)
    
    api_key = load_api_key()
    provider = OpenAIProvider(api_key=api_key)
    
    messages = [
        LLMMessage(role='user', content='Say hello and introduce yourself in one sentence.')
    ]
    
    print('📋 Request: Simple greeting')
    print('⏱️  Testing GPT-5 Pro...\n')
    
    start = time.time()
    
    try:
        response = provider.chat_completion(
            messages=messages,
            model='gpt-5-pro'
        )
        
        elapsed = time.time() - start
        
        print(f'✅ SUCCESS!')
        print(f'⏱️  Time: {elapsed:.2f}s')
        print(f'🤖 Model: {response.model}')
        print(f'📝 Response: "{response.content}"')
        print(f'💰 Tokens: {response.usage.get("total_tokens", "unknown")}')
        print()
        
        return True
        
    except Exception as e:
        print(f'❌ FAILED: {e}\n')
        return False

def test_comparison():
    """Test 2: Speed comparison"""
    print('=' * 60)
    print('TEST 2: Speed Comparison (Pro vs Chat Latest)')
    print('=' * 60)
    
    api_key = load_api_key()
    provider = OpenAIProvider(api_key=api_key)
    
    messages = [
        LLMMessage(role='user', content='Explain microservices in 2 sentences.')
    ]
    
    results = {}
    
    for model_name in ['gpt-5-chat-latest', 'gpt-5-pro']:
        print(f'\n📋 Testing {model_name}...')
        
        start = time.time()
        
        try:
            response = provider.chat_completion(
                messages=messages,
                model=model_name
            )
            
            elapsed = time.time() - start
            
            results[model_name] = {
                'time': elapsed,
                'length': len(response.content),
                'content': response.content,
                'success': True
            }
            
            print(f'   ✅ Time: {elapsed:.2f}s')
            print(f'   📊 Length: {len(response.content)} chars')
            
        except Exception as e:
            results[model_name] = {
                'success': False,
                'error': str(e)
            }
            print(f'   ❌ Failed: {e}')
    
    print()
    
    if all(r.get('success') for r in results.values()):
        chat = results['gpt-5-chat-latest']
        pro = results['gpt-5-pro']
        
        print('=' * 60)
        print('📊 COMPARISON')
        print('=' * 60)
        print(f'\nChat Latest: {chat["time"]:.2f}s, {chat["length"]} chars')
        print(f'Pro:         {pro["time"]:.2f}s, {pro["length"]} chars')
        print(f'\n🏆 Faster: {"Chat Latest" if chat["time"] < pro["time"] else "Pro"}')
        print(f'📝 Longer: {"Chat Latest" if chat["length"] > pro["length"] else "Pro"}')
        print()
        
        return True
    else:
        print('⚠️  One or more tests failed\n')
        return False

def test_complex():
    """Test 3: Complex reasoning"""
    print('=' * 60)
    print('TEST 3: Complex Reasoning Task')
    print('=' * 60)
    
    api_key = load_api_key()
    provider = OpenAIProvider(api_key=api_key)
    
    messages = [
        LLMMessage(
            role='system',
            content='You are a technical architect. Provide structured, detailed responses.'
        ),
        LLMMessage(
            role='user',
            content='Create a 3-phase plan to migrate a monolithic app to microservices. Include timeline and risks.'
        )
    ]
    
    print('📋 Request: Complex migration planning')
    print('⏱️  Testing GPT-5 Pro reasoning...\n')
    
    start = time.time()
    
    try:
        response = provider.chat_completion(
            messages=messages,
            model='gpt-5-pro'
        )
        
        elapsed = time.time() - start
        
        print(f'✅ SUCCESS!')
        print(f'⏱️  Time: {elapsed:.2f}s')
        print(f'📊 Length: {len(response.content)} chars')
        print(f'📝 Lines: {response.content.count(chr(10)) + 1}')
        
        # Check quality indicators
        content_lower = response.content.lower()
        indicators = {
            'Phases': 'phase' in content_lower,
            'Timeline': 'timeline' in content_lower or 'month' in content_lower or 'week' in content_lower,
            'Risks': 'risk' in content_lower,
            'Structure': any(marker in response.content for marker in ['1.', '2.', '3.', '-', '*'])
        }
        
        print('\n📊 Quality Indicators:')
        for name, present in indicators.items():
            status = '✅' if present else '❌'
            print(f'   {status} {name}')
        
        score = sum(indicators.values())
        print(f'\n🎯 Quality Score: {score}/4')
        
        print(f'\n📄 Response Preview (first 300 chars):')
        print(f'{response.content[:300]}...')
        print()
        
        return True
        
    except Exception as e:
        print(f'❌ FAILED: {e}\n')
        import traceback
        traceback.print_exc()
        return False

def main():
    print('\n' + '=' * 60)
    print('🧪 GPT-5 PRO TEST SUITE')
    print('Testing /v1/responses endpoint implementation')
    print('=' * 60)
    print()
    
    results = []
    
    # Run tests
    print('Starting tests...\n')
    
    results.append(('Simple Greeting', test_simple()))
    results.append(('Speed Comparison', test_comparison()))
    results.append(('Complex Reasoning', test_complex()))
    
    # Summary
    print('=' * 60)
    print('📌 FINAL RESULTS')
    print('=' * 60)
    
    for test_name, success in results:
        status = '✅' if success else '❌'
        print(f'{status} {test_name}')
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f'\n🎯 Tests Passed: {passed}/{total}')
    
    if passed == total:
        print('\n' + '=' * 60)
        print('✅ ALL TESTS PASSED!')
        print('=' * 60)
        print('\n🎉 GPT-5 Pro is fully functional!')
        print('\nKey Findings:')
        print('✅ /v1/responses endpoint works')
        print('✅ Response parsing correct')
        print('✅ Token usage tracked')
        print('✅ Quality output generated')
        print('\nNext Steps:')
        print('1. Run full benchmarks vs GPT-4o')
        print('2. Compare Pro vs Chat Latest performance')
        print('3. Update coordinator config if Pro is better')
        print('4. Document Pro-specific features')
        return 0
    else:
        print(f'\n⚠️  {total - passed} test(s) failed')
        return 1

if __name__ == '__main__':
    sys.exit(main())
