#!/usr/bin/env python3
"""
Get OpenAI Organization ID and GPT-5 Model Access
Simple script to check what models your OpenAI account has access to
"""

import json
import requests
import sys
import os

def main():
    # Load API key from keys.json
    try:
        with open('/home/flip/agent-forge/keys.json') as f:
            keys = json.load(f)
            api_key = keys['OPENAI_API_KEY']
    except Exception as e:
        print(f'❌ Error loading API key: {e}')
        sys.exit(1)
    
    print('🔍 Checking OpenAI Account Details...\n')
    print(f'🔑 API Key: {api_key[:15]}...\n')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Step 1: Get all models
    print('📊 Step 1: Fetching available models...')
    print('=' * 60)
    try:
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers=headers
        )
        
        if response.status_code == 200:
            models = response.json()
            all_models = models.get('data', [])
            
            # Filter GPT-5 models
            gpt5_models = [m for m in all_models if 'gpt-5' in m['id'].lower()]
            
            print(f'✅ Total models available: {len(all_models)}')
            print(f'✅ GPT-5 models found: {len(gpt5_models)}\n')
            
            if gpt5_models:
                print('GPT-5 Models:')
                for model in sorted(gpt5_models, key=lambda x: x['id']):
                    print(f'  ✅ {model["id"]}')
                    if 'owned_by' in model:
                        print(f'     Owner: {model["owned_by"]}')
                    if 'created' in model:
                        from datetime import datetime
                        created = datetime.fromtimestamp(model['created'])
                        print(f'     Created: {created.strftime("%Y-%m-%d")}')
                    print()
            else:
                print('⚠️  No GPT-5 models found in your account')
                
                # Show some GPT-4 models for comparison
                gpt4_models = [m for m in all_models if 'gpt-4' in m['id'].lower()][:5]
                print('\nGPT-4 models (for comparison):')
                for model in gpt4_models:
                    print(f'  ✅ {model["id"]}')
        else:
            print(f'❌ Failed to fetch models: {response.status_code}')
            print(f'Response: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Error: {e}')
    
    # Step 2: Test GPT-5 Pro specifically
    print('\n' + '=' * 60)
    print('🧪 Step 2: Testing GPT-5 Pro directly...')
    print('=' * 60)
    try:
        test_payload = {
            "model": "gpt-5-pro",
            "messages": [
                {"role": "user", "content": "Say hello"}
            ],
            "max_tokens": 10
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=test_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print('✅ GPT-5 Pro WORKS!')
            print(f'   Response: {result["choices"][0]["message"]["content"]}')
            print(f'   Model: {result["model"]}')
        else:
            print(f'❌ GPT-5 Pro not available: {response.status_code}')
            print(f'   Error: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Error testing GPT-5 Pro: {e}')
    
    # Step 3: Try to get organization info
    print('\n' + '=' * 60)
    print('🏢 Step 3: Getting organization info...')
    print('=' * 60)
    try:
        # Try the /me endpoint to get user info
        response = requests.get(
            'https://api.openai.com/v1/organization',
            headers=headers
        )
        
        if response.status_code == 200:
            org_data = response.json()
            print('✅ Organization data:')
            print(json.dumps(org_data, indent=2))
        else:
            # Endpoint might not exist, try getting it from account
            response = requests.get(
                'https://api.openai.com/v1/dashboard/billing/subscription',
                headers=headers
            )
            
            if response.status_code == 200:
                print('✅ Billing/Account info:')
                print(json.dumps(response.json(), indent=2))
            else:
                print(f'⚠️  Could not get org info: {response.status_code}')
                print('   (This is normal for personal accounts)')
                
    except Exception as e:
        print(f'⚠️  Could not get org info: {e}')
        print('   (This is normal for personal accounts)')
    
    print('\n' + '=' * 60)
    print('📌 SUMMARY')
    print('=' * 60)
    print('Your OpenAI account has access to the models shown above.')
    print('If GPT-5 Pro is not listed, it is not yet available for your account.')
    print('\nCurrent recommendation:')
    print('✅ Use gpt-5-chat-latest (if listed above)')
    print('⏳ Wait for GPT-5 Pro general availability')

if __name__ == '__main__':
    main()
