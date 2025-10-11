#!/usr/bin/env python3
"""
Launch Issue Opener Agent

Simple launcher for the autonomous Issue Opener Agent.
Resolves GitHub issues and creates pull requests automatically.

Usage:
    python3 scripts/launch_issue_opener.py <issue_number>
    python3 scripts/launch_issue_opener.py 123

Environment Variables:
    BOT_GITHUB_TOKEN or GITHUB_TOKEN - GitHub API token
    OPENAI_API_KEY - OpenAI API key
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.operations.issue_opener_agent import IssueOpenerAgent


def load_keys():
    """Load API keys from secrets/keys.json or environment."""
    keys = {}
    
    # Try secrets/keys.json first
    keys_file = project_root / 'secrets' / 'keys.json'
    if keys_file.exists():
        with open(keys_file) as f:
            file_keys = json.load(f)
            keys.update(file_keys)
    
    # Environment variables override
    if os.getenv('OPENAI_API_KEY'):
        keys['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    
    if os.getenv('BOT_GITHUB_TOKEN'):
        keys['BOT_GITHUB_TOKEN'] = os.getenv('BOT_GITHUB_TOKEN')
    elif os.getenv('GITHUB_TOKEN'):
        keys['BOT_GITHUB_TOKEN'] = os.getenv('GITHUB_TOKEN')
    
    return keys


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("🤖 ISSUE OPENER AGENT")
    print("Autonomous GitHub issue resolution powered by GPT-5")
    print("=" * 70 + "\n")
    
    # Check arguments
    if len(sys.argv) < 2:
        print("❌ Usage: python3 launch_issue_opener.py <issue_number>")
        print("\nExample:")
        print("  python3 scripts/launch_issue_opener.py 123")
        sys.exit(1)
    
    try:
        issue_number = int(sys.argv[1])
    except ValueError:
        print(f"❌ Invalid issue number: {sys.argv[1]}")
        sys.exit(1)
    
    # Load keys
    keys = load_keys()
    
    if 'OPENAI_API_KEY' not in keys:
        print("❌ OPENAI_API_KEY not found")
        print("   Set environment variable or add to secrets/keys.json")
        sys.exit(1)
    
    if 'BOT_GITHUB_TOKEN' not in keys:
        print("❌ BOT_GITHUB_TOKEN or GITHUB_TOKEN not found")
        print("   Set environment variable or add to secrets/keys.json")
        sys.exit(1)
    
    # Create config
    config = {
        'github_token': keys['BOT_GITHUB_TOKEN'],
        'openai_api_key': keys['OPENAI_API_KEY'],
        'model': 'gpt-5-chat-latest',
        'repo': 'm0nk111/agent-forge',
        'project_root': str(project_root)
    }
    
    print(f"📋 Configuration:")
    print(f"   Model: {config['model']}")
    print(f"   Repo: {config['repo']}")
    print(f"   Issue: #{issue_number}")
    print()
    
    # Create and run agent
    try:
        agent = IssueOpenerAgent(config)
        result = agent.process_issue(issue_number)
        
        # Print summary
        if result['success']:
            print("\n" + "=" * 70)
            print("✅ SUCCESS!")
            print("=" * 70)
            print(f"\n📌 Summary:")
            print(f"   PR: {result['pr_url']}")
            print(f"   Branch: {result['branch']}")
            print(f"   Commit: {result['commit'][:8]}")
            print(f"\n🎯 Actions Taken:")
            for action in result['actions']:
                print(f"   ✓ {action}")
            print()
            
            sys.exit(0)
        else:
            print("\n" + "=" * 70)
            print("❌ FAILED")
            print("=" * 70)
            print(f"\nError: {result.get('error', 'Unknown error')}")
            print(f"\n🎯 Actions Completed:")
            for action in result.get('actions', []):
                print(f"   ✓ {action}")
            print()
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
