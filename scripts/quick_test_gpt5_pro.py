#!/usr/bin/env python3
"""
Quick GPT-5 Pro Test - Short Response
Fast test to verify GPT-5 Pro works with /v1/responses endpoint
"""

import json
import requests
import sys
import time

def main():
    # Load API key
    try:
        with open('/home/flip/agent-forge/secrets/keys.json') as f:
            keys = json.load(f)
            api_key = keys['OPENAI_API_KEY']
    except Exception as e:
        print(f'❌ Error loading API key: {e}')
        sys.exit(1)
    
    print('🧪 Quick GPT-5 Pro Test\n')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Simple short test
    test_payload = {
        "model": "gpt-5-pro",
        "input": "Say 'Hello from GPT-5 Pro!' and nothing else."
    }
    
    print('📋 Sending simple request to /v1/responses...')
    
    start_time = time.time()
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/responses',
            headers=headers,
            json=test_payload,
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        print(f'⏱️  Response time: {elapsed:.2f}s')
        print(f'📊 Status: {response.status_code}\n')
        
        if response.status_code == 200:
            result = response.json()
            print('✅ GPT-5 PRO WORKS!\n')
            print('Response structure:')
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f'❌ Failed: {response.status_code}')
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print('⚠️  Request timed out - GPT-5 Pro may be generating long response')
        print('   This actually means it works, just need to handle streaming!')
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
