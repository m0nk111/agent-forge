#!/usr/bin/env python3
"""Universal Agent Launcher for Agent-Forge.

Automatically discovers and launches agents from config/agents/ directory.
Supports interactive mode, direct issue handling, and profile management.

Usage:
    python3 scripts/launch_agent.py --list                    # List available agents
    python3 scripts/launch_agent.py --agent gpt4-coding-agent # Launch specific agent
    python3 scripts/launch_agent.py --interactive             # Interactive mode with agent selection
    python3 scripts/launch_agent.py --agent gpt4 --issue 92   # Handle issue with specific agent

Author: Agent Forge
Date: 2025-10-10
"""

import argparse
import logging
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.core.key_manager import KeyManager
from engine.runners.code_agent import CodeAgent
from engine.operations.issue_handler import IssueHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentProfileManager:
    """Manage agent profiles from config/agents/ directory."""
    
    def __init__(self, config_dir: Path = None):
        """Initialize profile manager.
        
        Args:
            config_dir: Path to agents config directory (default: config/agents/)
        """
        self.config_dir = config_dir or PROJECT_ROOT / "config" / "agents"
        self.profiles: Dict[str, Dict] = {}
        self._scan_profiles()
    
    def _scan_profiles(self):
        """Scan config/agents/ directory for agent profiles."""
        if not self.config_dir.exists():
            logger.warning(f"⚠️  Config directory not found: {self.config_dir}")
            return
        
        logger.debug(f"🔍 Scanning for agent profiles in: {self.config_dir}")
        
        for yaml_file in self.config_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    profile = yaml.safe_load(f)
                
                agent_id = profile.get('agent_id')
                if not agent_id:
                    logger.warning(f"⚠️  Profile missing agent_id: {yaml_file.name}")
                    continue
                
                self.profiles[agent_id] = {
                    'config': profile,
                    'file': yaml_file.name,
                    'path': yaml_file
                }
                
                logger.debug(f"   ✅ Found profile: {agent_id} ({yaml_file.name})")
                
            except Exception as e:
                logger.error(f"❌ Error loading profile {yaml_file.name}: {e}")
    
    def list_profiles(self) -> List[Dict]:
        """Get list of all available profiles.
        
        Returns:
            List of profile info dicts with id, name, provider, model
        """
        profiles = []
        for agent_id, data in self.profiles.items():
            config = data['config']
            profiles.append({
                'id': agent_id,
                'name': config.get('name', agent_id),
                'role': config.get('role', 'unknown'),
                'provider': config.get('model_provider', 'unknown'),
                'model': config.get('model_name', 'unknown'),
                'file': data['file']
            })
        return sorted(profiles, key=lambda x: x['id'])
    
    def get_profile(self, agent_id: str) -> Optional[Dict]:
        """Get specific profile by ID.
        
        Args:
            agent_id: Agent ID to retrieve
            
        Returns:
            Profile config dict or None if not found
        """
        # Exact match
        if agent_id in self.profiles:
            return self.profiles[agent_id]['config']
        
        # Fuzzy match (e.g., "gpt4" matches "gpt4-coding-agent")
        matches = [aid for aid in self.profiles.keys() if agent_id in aid]
        if len(matches) == 1:
            logger.info(f"🔍 Matched '{agent_id}' to profile: {matches[0]}")
            return self.profiles[matches[0]]['config']
        elif len(matches) > 1:
            logger.error(f"❌ Ambiguous agent ID '{agent_id}', matches: {matches}")
            return None
        
        return None
    
    def validate_profile(self, profile: Dict) -> List[str]:
        """Validate profile has required configuration.
        
        Args:
            profile: Profile config dict
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Required fields
        required = ['agent_id', 'model_provider', 'model_name']
        for field in required:
            if field not in profile:
                errors.append(f"Missing required field: {field}")
        
        # Check API key if needed
        provider = profile.get('model_provider', '').lower()
        if provider in ['openai', 'anthropic', 'google']:
            api_key_name = profile.get('api_key_name')
            if not api_key_name:
                errors.append(f"Missing api_key_name for provider: {provider}")
            else:
                # Check if key exists
                km = KeyManager()
                key = km.get_key(api_key_name)
                if not key:
                    errors.append(f"API key not found: {api_key_name}")
        
        # Check GitHub token if configured
        github_config = profile.get('github', {})
        if github_config:
            token_env = github_config.get('token_env')
            if token_env and not os.getenv(token_env):
                errors.append(f"GitHub token not found in environment: {token_env}")
        
        return errors


def print_profiles_table(profiles: List[Dict]):
    """Print formatted table of available agent profiles.
    
    Args:
        profiles: List of profile info dicts
    """
    if not profiles:
        print("⚠️  No agent profiles found in config/agents/")
        return
    
    print("\n📋 Available Agent Profiles:")
    print("=" * 100)
    print(f"{'ID':<25} {'Name':<25} {'Provider':<15} {'Model':<20} {'Role':<10}")
    print("-" * 100)
    
    for profile in profiles:
        print(f"{profile['id']:<25} {profile['name']:<25} {profile['provider']:<15} "
              f"{profile['model']:<20} {profile['role']:<10}")
    
    print("=" * 100)
    print(f"\n✅ Found {len(profiles)} agent profile(s)\n")


def create_agent_from_profile(profile: Dict) -> Optional[CodeAgent]:
    """Create CodeAgent instance from profile configuration.
    
    Args:
        profile: Profile config dict
        
    Returns:
        CodeAgent instance or None on error
    """
    try:
        # Extract config
        agent_id = profile['agent_id']
        provider = profile['model_provider']
        model = profile['model_name']
        
        # Get API key if needed
        api_key = None
        if provider.lower() in ['openai', 'anthropic', 'google']:
            api_key_name = profile.get('api_key_name')
            if api_key_name:
                km = KeyManager()
                api_key = km.get_key(api_key_name)
                if not api_key:
                    logger.error(f"❌ API key not found: {api_key_name}")
                    return None
        
        # Get GitHub config
        github_config = profile.get('github', {})
        github_token = None
        if github_config:
            token_env = github_config.get('token_env')
            if token_env:
                github_token = os.getenv(token_env)
                if not github_token:
                    logger.warning(f"⚠️  GitHub token not found: {token_env}")
        
        # Create agent
        logger.info(f"🚀 Creating agent: {agent_id}")
        logger.info(f"   Provider: {provider}")
        logger.info(f"   Model: {model}")
        
        agent = CodeAgent(
            project_root=PROJECT_ROOT,
            llm_provider=provider,
            model_name=model,
            api_key=api_key,
            github_token=github_token
        )
        
        # Test connection
        logger.info("🔌 Testing agent connection...")
        if not agent.test_llm_connection():
            logger.error("❌ Agent connection test failed")
            return None
        
        logger.info("✅ Agent ready")
        return agent
        
    except Exception as e:
        logger.error(f"❌ Error creating agent: {e}")
        return None


def interactive_mode(manager: AgentProfileManager):
    """Run interactive mode with agent selection and commands.
    
    Args:
        manager: Agent profile manager
    """
    print("\n🤖 Agent-Forge Interactive Mode")
    print("=" * 60)
    
    # List available agents
    profiles = manager.list_profiles()
    print_profiles_table(profiles)
    
    # Select agent
    print("Select an agent to launch:")
    for i, profile in enumerate(profiles, 1):
        print(f"  {i}. {profile['id']} ({profile['provider']} {profile['model']})")
    
    try:
        choice = input("\nEnter number or agent ID (or 'quit'): ").strip()
        
        if choice.lower() in ['quit', 'q', 'exit']:
            print("👋 Goodbye!")
            return
        
        # Parse choice
        agent_id = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(profiles):
                agent_id = profiles[idx]['id']
        else:
            agent_id = choice
        
        if not agent_id:
            print("❌ Invalid choice")
            return
        
        # Load profile
        profile = manager.get_profile(agent_id)
        if not profile:
            print(f"❌ Agent not found: {agent_id}")
            return
        
        # Validate profile
        errors = manager.validate_profile(profile)
        if errors:
            print(f"❌ Profile validation failed:")
            for error in errors:
                print(f"   - {error}")
            return
        
        # Create agent
        agent = create_agent_from_profile(profile)
        if not agent:
            return
        
        # Interactive commands
        print(f"\n✅ Agent {agent_id} loaded successfully!")
        print("\nAvailable commands:")
        print("  query <prompt>    - Query the agent")
        print("  issue <number>    - Handle GitHub issue")
        print("  info              - Show agent info")
        print("  cost              - Show cost estimates")
        print("  help              - Show this help")
        print("  quit              - Exit")
        
        while True:
            try:
                cmd = input(f"\n[{agent_id}]> ").strip()
                
                if not cmd:
                    continue
                
                if cmd.lower() in ['quit', 'q', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                elif cmd.lower() == 'info':
                    print(f"\nAgent ID: {profile['agent_id']}")
                    print(f"Name: {profile.get('name', 'N/A')}")
                    print(f"Provider: {profile['model_provider']}")
                    print(f"Model: {profile['model_name']}")
                    print(f"Role: {profile.get('role', 'N/A')}")
                    
                elif cmd.lower() == 'cost':
                    provider = profile['model_provider'].lower()
                    model = profile['model_name'].lower()
                    
                    if provider == 'openai':
                        if 'gpt-4' in model:
                            print("\n💰 Cost Estimates (GPT-4):")
                            print("  Simple query: ~$0.05")
                            print("  Code generation: ~$0.15")
                            print("  Full issue resolution: ~$0.25")
                        elif 'gpt-3.5' in model:
                            print("\n💰 Cost Estimates (GPT-3.5):")
                            print("  Simple query: ~$0.002")
                            print("  Code generation: ~$0.005")
                            print("  Full issue resolution: ~$0.01")
                    elif provider == 'local':
                        print("\n💰 Cost: FREE (local model)")
                    else:
                        print(f"\n💰 Cost estimates not available for: {provider}")
                
                elif cmd.lower() == 'help':
                    print("\nAvailable commands:")
                    print("  query <prompt>    - Query the agent")
                    print("  issue <number>    - Handle GitHub issue")
                    print("  info              - Show agent info")
                    print("  cost              - Show cost estimates")
                    print("  help              - Show this help")
                    print("  quit              - Exit")
                
                elif cmd.startswith('query '):
                    prompt = cmd[6:].strip()
                    if not prompt:
                        print("❌ Please provide a prompt")
                        continue
                    
                    print(f"\n🤔 Querying agent...")
                    response = agent.query_llm(prompt=prompt, stream=False)
                    print(f"\n📝 Response:\n{response}\n")
                
                elif cmd.startswith('issue '):
                    issue_num = cmd[6:].strip()
                    if not issue_num.isdigit():
                        print("❌ Please provide a valid issue number")
                        continue
                    
                    print(f"\n🎫 Handling issue #{issue_num}...")
                    
                    # Get repo from environment or default
                    repo = os.getenv('GITHUB_REPO', 'm0nk111/agent-forge')
                    
                    # Create issue handler
                    handler = IssueHandler(
                        agent=agent,
                        repo=repo
                    )
                    
                    # Handle issue
                    try:
                        result = handler.handle_issue(int(issue_num))
                        if result:
                            print(f"✅ Issue #{issue_num} handled successfully!")
                        else:
                            print(f"❌ Failed to handle issue #{issue_num}")
                    except Exception as e:
                        print(f"❌ Error handling issue: {e}")
                
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("   Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Universal Agent Launcher - Launch any agent from config/agents/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available agents
  python3 scripts/launch_agent.py --list
  
  # Launch specific agent interactively
  python3 scripts/launch_agent.py --agent gpt4-coding-agent
  
  # Handle issue with specific agent
  python3 scripts/launch_agent.py --agent gpt4 --issue 92
  
  # Interactive mode with agent selection
  python3 scripts/launch_agent.py --interactive
  
  # Use custom config directory
  python3 scripts/launch_agent.py --config-dir /path/to/configs --list
        """
    )
    
    parser.add_argument('--list', action='store_true',
                       help='List all available agent profiles')
    parser.add_argument('--agent', type=str,
                       help='Agent ID to launch (supports fuzzy matching)')
    parser.add_argument('--issue', type=int,
                       help='GitHub issue number to handle')
    parser.add_argument('--repo', type=str,
                       help='GitHub repository (default: from environment or m0nk111/agent-forge)')
    parser.add_argument('--interactive', action='store_true',
                       help='Launch interactive mode with agent selection')
    parser.add_argument('--config-dir', type=str,
                       help='Custom config directory (default: config/agents/)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize profile manager
    config_dir = Path(args.config_dir) if args.config_dir else None
    manager = AgentProfileManager(config_dir=config_dir)
    
    # List profiles
    if args.list:
        profiles = manager.list_profiles()
        print_profiles_table(profiles)
        return 0
    
    # Interactive mode
    if args.interactive:
        interactive_mode(manager)
        return 0
    
    # Launch specific agent
    if args.agent:
        # Load profile
        profile = manager.get_profile(args.agent)
        if not profile:
            logger.error(f"❌ Agent not found: {args.agent}")
            logger.info("\n💡 Available agents:")
            for p in manager.list_profiles():
                logger.info(f"   - {p['id']}")
            return 1
        
        # Validate profile
        errors = manager.validate_profile(profile)
        if errors:
            logger.error("❌ Profile validation failed:")
            for error in errors:
                logger.error(f"   - {error}")
            return 1
        
        # Create agent
        agent = create_agent_from_profile(profile)
        if not agent:
            return 1
        
        # Handle issue if specified
        if args.issue:
            repo = args.repo or os.getenv('GITHUB_REPO', 'm0nk111/agent-forge')
            
            logger.info(f"🎫 Handling issue #{args.issue} in {repo}")
            
            handler = IssueHandler(
                agent=agent,
                repo=repo
            )
            
            try:
                result = handler.handle_issue(args.issue)
                if result:
                    logger.info(f"✅ Issue #{args.issue} handled successfully!")
                    return 0
                else:
                    logger.error(f"❌ Failed to handle issue #{args.issue}")
                    return 1
            except Exception as e:
                logger.error(f"❌ Error handling issue: {e}")
                return 1
        
        else:
            # Just show agent info
            logger.info(f"\n✅ Agent {profile['agent_id']} loaded successfully!")
            logger.info(f"   Provider: {profile['model_provider']}")
            logger.info(f"   Model: {profile['model_name']}")
            logger.info("\n💡 Use --issue <number> to handle an issue")
            logger.info("   Or use --interactive for interactive mode")
            return 0
    
    # No action specified
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
