#!/usr/bin/env python3
"""
E2E Test for Phase 3B: Code Generation Pipeline
Tests issue #84 - Create string_utils.py helper module
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Enable debug mode
os.environ['DEBUG'] = '1'

# Use regular GITHUB_TOKEN for this test (BOT token may be invalid)
print(f"🔧 Using GITHUB_TOKEN for authentication")

sys.path.insert(0, '/home/flip/agent-forge')

from engine.operations.issue_handler import IssueHandler

def create_mock_agent():
    """Create mock agent with necessary attributes"""
    agent = Mock()
    agent.project_root = Path('/home/flip/agent-forge')
    agent.github_token = os.environ.get('GITHUB_TOKEN', '')
    
    # Mock query_llm to use actual Ollama
    def mock_query_llm(prompt, system_prompt="", model=None, **kwargs):
        import requests
        url = 'http://localhost:11434/api/generate'
        payload = {
            'model': model or 'qwen2.5-coder:7b',
            'prompt': prompt,
            'system': system_prompt,
            'stream': False
        }
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            print(f"⚠️ LLM query failed: {e}")
            return f"Error: {e}"
    
    agent.query_llm = mock_query_llm
    return agent

def test_issue_84_code_generation():
    """Test full pipeline: issue → code generation → PR"""
    
    print("=" * 80)
    print("Phase 3B E2E Test: Issue #84 Code Generation Pipeline")
    print("=" * 80)
    
    # Create mock agent and handler
    agent = create_mock_agent()
    handler = IssueHandler(agent)
    
    print("\n🔍 Step 1: Assign to issue #84")
    print("   Repository: m0nk111/agent-forge")
    print("   Issue: Create string_utils.py helper module")
    
    print("\n🔍 Step 2: Execute autonomous resolution")
    result = handler.assign_to_issue(
        repo='m0nk111/agent-forge',
        issue_number=84
    )
    
    print(f"\n📊 Result:")
    print(f"   Success: {result.get('success')}")
    print(f"   PR URL: {result.get('pr_url')}")
    print(f"   Summary: {result.get('summary')}")
    print(f"   Actions: {result.get('actions_taken')}")
    print("=" * 80)
    
    return result.get('success', False)

if __name__ == '__main__':
    try:
        success = test_issue_84_code_generation()
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: E2E test completed")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
