#!/usr/bin/env python3
"""
Launch GPT-4 Coding Agent

Uses OpenAI GPT-4 for code generation with m0nk111-qwen-agent GitHub identity.

Usage:
    python3 scripts/launch_gpt4_agent.py                    # Interactive mode
    python3 scripts/launch_gpt4_agent.py --issue 92         # Specific issue
    python3 scripts/launch_gpt4_agent.py --help             # Show options

Requirements:
    - OPENAI_API_KEY in keys.json
    - CODEAGENT_GITHUB_TOKEN in environment

Author: Agent Forge
Date: 2025-10-10
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.runners.code_agent import CodeAgent
from engine.core.key_manager import KeyManager


def check_requirements():
    """Verify all requirements are met."""
    print("🔍 Checking requirements...")
    
    issues = []
    
    # Check OpenAI API key
    km = KeyManager()
    openai_key = km.get_key("OPENAI_API_KEY")
    if not openai_key:
        issues.append("❌ OPENAI_API_KEY not found in keys.json")
    else:
        print(f"   ✅ OpenAI key found: {km.mask_key(openai_key)}")
    
    # Check GitHub token
    github_token = os.getenv("CODEAGENT_GITHUB_TOKEN")
    if not github_token:
        issues.append("❌ CODEAGENT_GITHUB_TOKEN not found in environment")
        issues.append("   Run: export CODEAGENT_GITHUB_TOKEN='ghp_...'")
        issues.append("   Or: source /etc/agent-forge/tokens.env")
    else:
        print(f"   ✅ GitHub token found: {github_token[:10]}...")
    
    if issues:
        print("\n⚠️  Requirements not met:")
        for issue in issues:
            print(f"   {issue}")
        return False
    
    print("   ✅ All requirements met\n")
    return True


def create_gpt4_agent(config_path: str = None):
    """Create GPT-4 coding agent with configuration."""
    
    config_file = config_path or str(project_root / "config/agents/gpt4-coding-agent.yaml")
    
    print(f"🤖 Initializing GPT-4 Coding Agent...")
    print(f"   Config: {config_file}")
    
    agent = CodeAgent(
        config_path=config_file,
        llm_provider="openai",        # Force OpenAI
        model="gpt-4",                 # Use GPT-4
        project_root=str(project_root),
        enable_monitoring=True,
        agent_id="gpt4-coding-agent"
    )
    
    print(f"   ✅ Agent initialized")
    print(f"   📊 Provider: {agent.llm_provider_name}")
    print(f"   🎯 Model: {agent.model}")
    print(f"   📁 Project: {agent.project_root}\n")
    
    return agent


def handle_issue(agent: CodeAgent, repo: str, issue_number: int):
    """Handle specific GitHub issue."""
    print(f"📋 Handling issue #{issue_number} in {repo}...")
    
    try:
        result = agent.issue_handler.assign_to_issue(repo, issue_number)
        
        if result.get('success'):
            print(f"\n✅ Issue #{issue_number} completed successfully!")
            print(f"   PR: {result.get('pr_url')}")
            print(f"   Actions: {', '.join(result.get('actions_taken', []))}")
        else:
            print(f"\n❌ Issue #{issue_number} failed")
            print(f"   Error: {result.get('error')}")
            
        return result
        
    except Exception as e:
        print(f"\n❌ Error handling issue: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def interactive_mode(agent: CodeAgent):
    """Interactive mode for testing queries."""
    print("🎮 Interactive Mode")
    print("=" * 70)
    print("Commands:")
    print("  query <prompt>  - Query GPT-4 directly")
    print("  issue <num>     - Handle GitHub issue")
    print("  cost            - Show estimated costs")
    print("  help            - Show this help")
    print("  quit            - Exit")
    print("=" * 70)
    
    while True:
        try:
            cmd = input("\n> ").strip()
            
            if not cmd:
                continue
            
            if cmd == "quit":
                print("👋 Goodbye!")
                break
            
            elif cmd == "help":
                print("\nCommands:")
                print("  query <prompt>  - Query GPT-4")
                print("  issue <num>     - Handle issue")
                print("  cost            - Show costs")
                print("  quit            - Exit")
            
            elif cmd == "cost":
                print("\n💰 Cost Estimates:")
                print("   GPT-4: $0.03/$0.06 per 1K tokens (in/out)")
                print("   Typical issue: ~$0.25")
                print("   Simple query: ~$0.05")
            
            elif cmd.startswith("query "):
                prompt = cmd[6:].strip()
                if not prompt:
                    print("❌ Usage: query <prompt>")
                    continue
                
                print(f"\n🌐 Querying GPT-4...")
                response = agent.query_llm(prompt)
                print(f"\n💡 Response:")
                print("─" * 70)
                print(response)
                print("─" * 70)
            
            elif cmd.startswith("issue "):
                try:
                    issue_num = int(cmd[6:].strip())
                    handle_issue(agent, "m0nk111/agent-forge", issue_num)
                except ValueError:
                    print("❌ Usage: issue <number>")
            
            else:
                print(f"❌ Unknown command: {cmd}")
                print("   Type 'help' for available commands")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Launch GPT-4 Coding Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 scripts/launch_gpt4_agent.py
  
  # Handle specific issue
  python3 scripts/launch_gpt4_agent.py --issue 92
  
  # Custom config
  python3 scripts/launch_gpt4_agent.py --config config/agents/custom.yaml
        """
    )
    
    parser.add_argument('--issue', type=int, help='GitHub issue number to handle')
    parser.add_argument('--repo', default='m0nk111/agent-forge', help='Repository (owner/repo)')
    parser.add_argument('--config', help='Custom config file path')
    parser.add_argument('--interactive', action='store_true', help='Force interactive mode')
    
    args = parser.parse_args()
    
    print("\n🤖 GPT-4 Coding Agent Launcher")
    print("=" * 70)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Create agent
    agent = create_gpt4_agent(args.config)
    
    # Handle issue or interactive mode
    if args.issue:
        result = handle_issue(agent, args.repo, args.issue)
        sys.exit(0 if result.get('success') else 1)
    else:
        interactive_mode(agent)
        sys.exit(0)


if __name__ == "__main__":
    main()
