#!/usr/bin/env python3
"""
Check GPT-5 Pro Availability
Quick script to test if GPT-5 Pro is available via OpenAI API
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.core.llm_providers import OpenAIProvider, LLMMessage
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('❌ OPENAI_API_KEY not found in environment')
        print('   Run: export OPENAI_API_KEY=your-key')
        sys.exit(1)
    
    org_id = os.getenv('OPENAI_ORG_ID')
    
    print('🔍 Checking GPT-5 Pro availability...\n')
    print(f'🔑 API Key: {api_key[:10]}...')
    if org_id:
        print(f'🏢 Org ID: {org_id}')
    else:
        print('⚠️  No OPENAI_ORG_ID set (may be needed for GPT-5 Pro access)')
    print()
    
    # Initialize provider
    provider = OpenAIProvider(api_key=api_key, org_id=org_id)
    
    # Step 1: Get all available models
    print('📊 Step 1: Fetching available models from OpenAI...')
    try:
        models = provider.get_available_models()
        gpt5_models = [m for m in models if 'gpt-5' in m.lower()]
        
        print(f'   Found {len(gpt5_models)} GPT-5 models:')
        for model in sorted(gpt5_models):
            print(f'   ✅ {model}')
        print()
    except Exception as e:
        print(f'   ❌ Error fetching models: {e}\n')
    
    # Step 2: Test GPT-5 Pro specifically
    print('🧪 Step 2: Testing GPT-5 Pro with actual request...')
    try:
        response = provider.chat_completion(
            model='gpt-5-pro',
            messages=[LLMMessage(role='user', content='Say "Hello from GPT-5 Pro!"')],
            temperature=0.7,
            max_tokens=20
        )
        
        print('   ✅ GPT-5 Pro WORKS!')
        print(f'   📝 Response: {response.content}')
        print(f'   🤖 Model used: {response.model}')
        print(f'   📊 Tokens: {response.usage.get("total_tokens", "unknown")}')
        print()
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f'   ❌ GPT-5 Pro NOT available')
        print(f'   Error: {error_msg}')
        
        if '404' in error_msg:
            print('   Reason: Model not found (404) - not yet released')
        elif '400' in error_msg:
            print('   Reason: Bad request (400) - model exists but has issues')
        elif '403' in error_msg:
            print('   Reason: Access denied (403) - may need special access')
        print()
        return False

if __name__ == '__main__':
    success = main()
    
    print('=' * 60)
    print('📌 SUMMARY')
    print('=' * 60)
    
    if success:
        print('✅ GPT-5 Pro is AVAILABLE and working!')
        print()
        print('Next steps:')
        print('1. Update coordinator-agent.yaml to use gpt-5-pro')
        print('2. Run comparison tests: scripts/compare_gpt5_gpt4o.py')
        print('3. Update documentation with GPT-5 Pro benchmarks')
    else:
        print('❌ GPT-5 Pro is NOT YET available')
        print()
        print('Current status:')
        print('✅ Using gpt-5-chat-latest (50% faster than GPT-4o)')
        print('⏳ Waiting for GPT-5 Pro release')
        print()
        print('Run this script daily to check for availability:')
        print('   python3 scripts/check_gpt5_pro.py')
    
    sys.exit(0 if success else 1)
