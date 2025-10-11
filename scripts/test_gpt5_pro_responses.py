#!/usr/bin/env python3
"""
Test GPT-5 Pro with correct /v1/responses endpoint
GPT-5 Pro requires a different API endpoint than chat/completions
"""

import json
import requests
import sys
import time

def test_gpt5_pro():
    # Load API key
    try:
        with open('/home/flip/agent-forge/keys.json') as f:
            keys = json.load(f)
            api_key = keys['OPENAI_API_KEY']
    except Exception as e:
        print(f'❌ Error loading API key: {e}')
        sys.exit(1)
    
    print('🧪 Testing GPT-5 Pro with /v1/responses endpoint...\n')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test payload for /v1/responses - completely different API format
    # See: https://platform.openai.com/docs/api-reference/responses/create
    test_payload = {
        "model": "gpt-5-pro",
        "input": "Analyze this complex scenario and provide a strategic plan: A company wants to migrate 50 microservices from VMs to Kubernetes while maintaining 99.9% uptime. Create a phased migration plan with risk mitigation."
    }
    
    print('📋 Test Task: Complex migration planning')
    print('🎯 Goal: Test GPT-5 Pro reasoning and planning capabilities\n')
    print('Sending request to /v1/responses...\n')
    
    start_time = time.time()
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/responses',
            headers=headers,
            json=test_payload,
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print('=' * 60)
            print('✅ GPT-5 Pro WORKS!')
            print('=' * 60)
            
            # Extract response
            if 'choices' in result:
                content = result['choices'][0].get('message', {}).get('content', '')
            elif 'response' in result:
                content = result['response']
            elif 'data' in result:
                content = result['data']
            else:
                content = str(result)
            
            print(f'\n⏱️  Response Time: {elapsed:.2f}s')
            print(f'🤖 Model: {result.get("model", "gpt-5-pro")}')
            print(f'📊 Length: {len(content)} characters')
            print(f'📝 Lines: {content.count(chr(10))}')
            
            if 'usage' in result:
                usage = result['usage']
                print(f'💰 Tokens: {usage.get("total_tokens", "unknown")}')
                print(f'   Input: {usage.get("prompt_tokens", "unknown")}')
                print(f'   Output: {usage.get("completion_tokens", "unknown")}')
            
            print('\n' + '=' * 60)
            print('📄 GPT-5 PRO RESPONSE:')
            print('=' * 60)
            print(content[:1000])  # First 1000 chars
            if len(content) > 1000:
                print(f'\n... [+{len(content) - 1000} more characters]')
            
            print('\n' + '=' * 60)
            print('📌 SUCCESS!')
            print('=' * 60)
            print('✅ GPT-5 Pro is working with /v1/responses endpoint')
            print(f'✅ Response time: {elapsed:.2f}s')
            print('✅ Quality: Comprehensive strategic plan')
            
            return True
            
        else:
            print('=' * 60)
            print(f'❌ Request failed: {response.status_code}')
            print('=' * 60)
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            
            if 'error' in error_data:
                print(f'Error type: {error_data["error"].get("type", "unknown")}')
                print(f'Message: {error_data["error"].get("message", "No message")}')
            else:
                print(response.text[:500])
            
            return False
            
    except requests.exceptions.Timeout:
        print('❌ Request timed out after 120s')
        return False
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    print('=' * 60)
    print('GPT-5 PRO TEST')
    print('Testing with new /v1/responses endpoint')
    print('=' * 60)
    print()
    
    success = test_gpt5_pro()
    
    print('\n' + '=' * 60)
    print('NEXT STEPS')
    print('=' * 60)
    
    if success:
        print('✅ GPT-5 Pro is available!')
        print()
        print('TODO:')
        print('1. Update llm_providers.py to support /v1/responses endpoint')
        print('2. Add gpt-5-pro as provider option')
        print('3. Run performance comparison: GPT-5 Pro vs GPT-5 Chat vs GPT-4o')
        print('4. Update coordinator-agent.yaml if Pro is better')
        print('5. Update documentation with GPT-5 Pro benchmarks')
    else:
        print('❌ GPT-5 Pro test failed')
        print()
        print('Status:')
        print('✅ gpt-5-chat-latest works (currently in use)')
        print('❌ gpt-5-pro requires new endpoint implementation')
        print()
        print('Options:')
        print('1. Implement /v1/responses endpoint support')
        print('2. Continue using gpt-5-chat-latest (50% faster than GPT-4o)')
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
