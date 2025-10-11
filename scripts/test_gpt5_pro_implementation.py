#!/usr/bin/env python3
"""
Test GPT-5 Pro with new /v1/responses endpoint support
Comprehensive test of the implemented responses API
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.core.llm_providers import OpenAIProvider, LLMMessage
import json

def load_api_key():
    """Load API key from keys.json"""
    try:
        with open('/home/flip/agent-forge/keys.json') as f:
            keys = json.load(f)
            return keys['OPENAI_API_KEY']
    except Exception as e:
        print(f'❌ Error loading API key: {e}')
        sys.exit(1)

def test_simple_response():
    """Test 1: Simple response"""
    print('=' * 60)
    print('🧪 TEST 1: Simple Response')
    print('=' * 60)
    
    api_key = load_api_key()
    provider = OpenAIProvider(api_key=api_key)
    
    messages = [
        LLMMessage(role='user', content='Say "Hello from GPT-5 Pro!" and explain in one sentence what you are.')
    ]
    
    print('📋 Task: Simple greeting and self-description')
    print('⏱️  Starting request...\n')
    
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
        print(f'📊 Length: {len(response.content)} chars')
        print(f'💰 Tokens: {response.usage.get("total_tokens", "estimated")}')
        print(f'\n📄 Response:\n{response.content}\n')
        
        return True
        
    except Exception as e:
        print(f'❌ FAILED: {e}\n')
        return False

def test_complex_planning():
    """Test 2: Complex planning task"""
    print('=' * 60)
    print('🧪 TEST 2: Complex Planning')
    print('=' * 60)
    
    api_key = load_api_key()
    provider = OpenAIProvider(api_key=api_key)
    
    messages = [
        LLMMessage(
            role='system',
            content='You are a strategic planning expert. Provide comprehensive, structured plans.'
        ),
        LLMMessage(
            role='user',
            content='''Analyze this complex scenario and create a detailed implementation plan:

A company with 50 microservices wants to migrate from VMs to Kubernetes while maintaining 99.9% uptime. 
They have a 3-month timeline and a team of 10 engineers.

Provide:
1. Phased migration strategy (with timeline)
2. Risk assessment and mitigation
3. Testing strategy
4. Rollback procedures
5. Success metrics'''
        )
    ]
    
    print('📋 Task: Complex K8s migration planning')
    print('🎯 Expected: Multi-phase plan with risks and timeline')
    print('⏱️  Starting request...\n')
    
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
        print(f'📊 Length: {len(response.content)} chars')
        print(f'📝 Lines: {response.content.count(chr(10)) + 1}')
        print(f'💰 Tokens: {response.usage.get("total_tokens", "estimated")}')
        
        # Quality indicators
        quality_indicators = {
            'phases': 'phase' in response.content.lower() or 'stage' in response.content.lower(),
            'risks': 'risk' in response.content.lower(),
            'testing': 'test' in response.content.lower(),
            'rollback': 'rollback' in response.content.lower(),
            'metrics': 'metric' in response.content.lower()
        }
        
        print('\n📊 Quality Indicators:')
        for indicator, present in quality_indicators.items():
            status = '✅' if present else '❌'
            print(f'   {status} {indicator.capitalize()}')
        
        quality_score = sum(quality_indicators.values())
        print(f'\n🎯 Quality Score: {quality_score}/5')
        
        print(f'\n📄 Response (first 500 chars):\n{response.content[:500]}...\n')
        
        return True
        
    except Exception as e:
        print(f'❌ FAILED: {e}\n')
        import traceback
        traceback.print_exc()
        return False

def test_comparison_with_chat_latest():
    """Test 3: Compare GPT-5 Pro vs Chat Latest"""
    print('=' * 60)
    print('🧪 TEST 3: GPT-5 Pro vs Chat Latest Comparison')
    print('=' * 60)
    
    api_key = load_api_key()
    provider = OpenAIProvider(api_key=api_key)
    
    messages = [
        LLMMessage(
            role='user',
            content='Explain the key differences between microservices and monolithic architecture in 3 bullet points.'
        )
    ]
    
    results = {}
    
    for model in ['gpt-5-pro', 'gpt-5-chat-latest']:
        print(f'\n📋 Testing {model}...')
        
        start = time.time()
        
        try:
            response = provider.chat_completion(
                messages=messages,
                model=model
            )
            
            elapsed = time.time() - start
            
            results[model] = {
                'success': True,
                'time': elapsed,
                'length': len(response.content),
                'content': response.content
            }
            
            print(f'   ✅ Time: {elapsed:.2f}s, Length: {len(response.content)} chars')
            
        except Exception as e:
            results[model] = {
                'success': False,
                'error': str(e)
            }
            print(f'   ❌ Failed: {e}')
    
    print('\n' + '=' * 60)
    print('📊 COMPARISON RESULTS')
    print('=' * 60)
    
    if all(r.get('success') for r in results.values()):
        pro = results['gpt-5-pro']
        chat = results['gpt-5-chat-latest']
        
        print(f'\nGPT-5 Pro:')
        print(f'  ⏱️  Time: {pro["time"]:.2f}s')
        print(f'  📊 Length: {pro["length"]} chars')
        
        print(f'\nGPT-5 Chat Latest:')
        print(f'  ⏱️  Time: {chat["time"]:.2f}s')
        print(f'  📊 Length: {chat["length"]} chars')
        
        print(f'\n🏆 Speed Winner: {"Pro" if pro["time"] < chat["time"] else "Chat Latest"}')
        print(f'📝 More Detailed: {"Pro" if pro["length"] > chat["length"] else "Chat Latest"}')
        
        return True
    else:
        print('⚠️  One or more models failed')
        return False

def main():
    print('\n' + '=' * 60)
    print('GPT-5 PRO COMPREHENSIVE TEST')
    print('Testing new /v1/responses endpoint implementation')
    print('=' * 60)
    print()
    
    results = []
    
    # Test 1: Simple response
    results.append(('Simple Response', test_simple_response()))
    
    # Test 2: Complex planning
    results.append(('Complex Planning', test_complex_planning()))
    
    # Test 3: Comparison
    results.append(('Pro vs Chat Latest', test_comparison_with_chat_latest()))
    
    # Final summary
    print('\n' + '=' * 60)
    print('📌 FINAL SUMMARY')
    print('=' * 60)
    
    for test_name, success in results:
        status = '✅' if success else '❌'
        print(f'{status} {test_name}')
    
    total_passed = sum(1 for _, success in results if success)
    print(f'\n🎯 Tests Passed: {total_passed}/{len(results)}')
    
    if total_passed == len(results):
        print('\n' + '=' * 60)
        print('✅ ALL TESTS PASSED!')
        print('=' * 60)
        print('\nGPT-5 Pro is now fully functional!')
        print('\nNext Steps:')
        print('1. Run performance benchmarks: scripts/compare_gpt5_gpt4o.py')
        print('2. Update coordinator-agent.yaml if Pro is faster/better')
        print('3. Update documentation with Pro benchmarks')
        print('4. Add Pro to agent role configurations')
        return 0
    else:
        print('\n⚠️  Some tests failed. Check errors above.')
        return 1

if __name__ == '__main__':
    sys.exit(main())
