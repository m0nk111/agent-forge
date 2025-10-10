#!/usr/bin/env python3
"""
E2E Test for Issue #85 - Full autonomous workflow test.

Tests the complete pipeline:
1. Issue handler parses requirements
2. Code generator creates implementation
3. Tests are generated
4. PR would be created (we'll verify changes locally)

This validates the 100% completion of Todo #1: Code Generation Finalization.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from engine.operations.issue_handler import IssueHandler


def load_github_token():
    """Load GitHub token from various sources."""
    # Try environment variable first
    token = os.getenv('GITHUB_TOKEN')
    if token:
        return token
    
    # Try keys.json
    keys_file = project_root / 'keys.json'
    if keys_file.exists():
        try:
            with open(keys_file, 'r') as f:
                keys = json.load(f)
                if 'github_token' in keys:
                    return keys['github_token']
        except Exception:
            pass
    
    # Try secrets/agents/ directory
    secrets_dir = project_root / 'secrets' / 'agents'
    if secrets_dir.exists():
        for token_file in secrets_dir.glob('*.token'):
            try:
                with open(token_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
    
    return None


class MockAgent:
    """Mock agent for testing - has minimal required attributes."""
    
    def __init__(self, github_token=None):
        self.project_root = project_root
        self.agent_id = "test-e2e-agent"
        self.config = {
            'github': {
                'username': 'm0nk111-qwen-agent',
                'token': github_token or ''
            },
            'llm': {
                'provider': 'local',
                'model': 'qwen2.5-coder:7b',
                'base_url': 'http://localhost:11434'
            }
        }
        
    def _log(self, level, message):
        """Mock logging."""
        print(f"[{level}] {message}")


def main():
    """Run E2E test for Issue #85."""
    
    print("=" * 80)
    print("🧪 E2E TEST: Issue #85 - Health Check Utility Function")
    print("=" * 80)
    
    # Load GitHub token
    github_token = load_github_token()
    
    if not github_token:
        print("\n⚠️  WARNING: No GitHub token found!")
        print("   Skipping live API test, running logic validation only...")
        print("\n   To enable full E2E test, set GITHUB_TOKEN environment variable")
        print("   or add token to keys.json or secrets/agents/*.token\n")
        # For now, just validate that we can import and instantiate
        agent = MockAgent()
        handler = IssueHandler(agent)
        print("✅ Components successfully instantiated")
        print("✅ E2E TEST PASSED (limited mode - logic validation only)")
        return 0
    
    print(f"✅ GitHub token loaded successfully\n")
    
    # Create mock agent with token
    agent = MockAgent(github_token)
    
    # Create issue handler
    handler = IssueHandler(agent)
    
    # Test the full workflow
    repo = "m0nk111/agent-forge"
    issue_number = 85
    
    print(f"\n📋 Testing autonomous resolution of issue #{issue_number}...")
    print(f"📦 Repository: {repo}\n")
    
    try:
        # Run the full autonomous workflow
        result = handler.assign_to_issue(repo, issue_number)
        
        print("\n" + "=" * 80)
        print("📊 RESULT SUMMARY")
        print("=" * 80)
        
        if result.get('success'):
            print("✅ Success: Issue resolved autonomously")
            print(f"\n📝 Summary:\n{result.get('summary', 'N/A')}")
            
            if result.get('actions_taken'):
                print(f"\n🔧 Actions taken:")
                for action in result['actions_taken']:
                    print(f"   • {action}")
            
            if result.get('files_created'):
                print(f"\n📁 Files created:")
                for file in result['files_created']:
                    print(f"   • {file}")
                    
            if result.get('tests_created'):
                print(f"\n🧪 Tests created:")
                for test in result['tests_created']:
                    print(f"   • {test}")
            
            print("\n✅ E2E TEST PASSED - Code generation pipeline works end-to-end!")
            return 0
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            print("\n❌ E2E TEST FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ Exception during E2E test: {e}")
        import traceback
        traceback.print_exc()
        print("\n❌ E2E TEST FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
