"""
GitHub Account Configuration Manager

Centralized management of GitHub bot/agent account configurations.
Eliminates hardcoded account details throughout the codebase.

Usage:
    from engine.core.account_manager import AccountManager
    
    # Get account config
    manager = AccountManager()
    bot_account = manager.get_account('m0nk111-post')
    
    print(bot_account.username)  # m0nk111-post
    print(bot_account.email)     # aicodingtime+post@gmail.com
    print(bot_account.token)     # Loaded from token_file
    
    # Get all coders
    coders = manager.get_group('coders')
    
    # Get trusted accounts for security
    trusted = manager.get_trusted_accounts()
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GitHubAccount:
    """GitHub account configuration."""
    username: str
    email: str
    role: str
    description: str
    token_file: str
    token_env: str
    capabilities: List[str]
    _token: Optional[str] = None
    
    @property
    def token(self) -> Optional[str]:
        """Get GitHub token from env or file."""
        if self._token:
            return self._token
            
        # Try environment variable first
        token = os.getenv(self.token_env)
        if token:
            self._token = token
            return token
        
        # Fall back to token file
        token_path = Path(self.token_file)
        if token_path.exists():
            try:
                self._token = token_path.read_text().strip()
                return self._token
            except Exception as e:
                logger.warning(f"Failed to read token from {token_path}: {e}")
        
        logger.warning(f"No token found for {self.username} (env: {self.token_env}, file: {self.token_file})")
        return None
    
    def has_capability(self, capability: str) -> bool:
        """Check if account has specific capability."""
        return capability in self.capabilities


class AccountManager:
    """Manage GitHub account configurations."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize account manager.
        
        Args:
            config_path: Path to github_accounts.yaml (defaults to config/system/github_accounts.yaml)
        """
        if config_path is None:
            # Default to project root config
            config_path = Path(__file__).parent.parent.parent / "config" / "system" / "github_accounts.yaml"
        
        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
        self._accounts: Dict[str, GitHubAccount] = {}
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            
            # Parse accounts
            for username, account_data in self._config.get('accounts', {}).items():
                self._accounts[username] = GitHubAccount(
                    username=account_data['username'],
                    email=account_data['email'],
                    role=account_data['role'],
                    description=account_data['description'],
                    token_file=account_data['token_file'],
                    token_env=account_data['token_env'],
                    capabilities=account_data.get('capabilities', [])
                )
            
            logger.info(f"✅ Loaded {len(self._accounts)} GitHub accounts from {self.config_path}")
        
        except FileNotFoundError:
            logger.error(f"❌ GitHub accounts config not found: {self.config_path}")
            self._config = {'accounts': {}, 'groups': {}, 'trusted_accounts': []}
        
        except Exception as e:
            logger.error(f"❌ Failed to load GitHub accounts config: {e}")
            self._config = {'accounts': {}, 'groups': {}, 'trusted_accounts': []}
    
    def get_account(self, username: str) -> Optional[GitHubAccount]:
        """
        Get account configuration by username.
        
        Args:
            username: GitHub account username
        
        Returns:
            GitHubAccount if found, None otherwise
        """
        return self._accounts.get(username)
    
    def get_group(self, group_name: str) -> List[str]:
        """
        Get list of usernames in a group.
        
        Args:
            group_name: Group name (e.g., 'coders', 'reviewers', 'bots')
        
        Returns:
            List of usernames in the group
        """
        if not self._config:
            return []
        
        return self._config.get('groups', {}).get(group_name, [])
    
    def get_accounts_by_group(self, group_name: str) -> List[GitHubAccount]:
        """
        Get account objects for a group.
        
        Args:
            group_name: Group name
        
        Returns:
            List of GitHubAccount objects
        """
        usernames = self.get_group(group_name)
        return [self._accounts[u] for u in usernames if u in self._accounts]
    
    def get_accounts_by_role(self, role: str) -> List[GitHubAccount]:
        """
        Get all accounts with specific role.
        
        Args:
            role: Role name (e.g., 'bot', 'developer', 'reviewer')
        
        Returns:
            List of GitHubAccount objects
        """
        return [acc for acc in self._accounts.values() if acc.role == role]
    
    def get_accounts_by_capability(self, capability: str) -> List[GitHubAccount]:
        """
        Get all accounts with specific capability.
        
        Args:
            capability: Capability name (e.g., 'review_code', 'create_pull_requests')
        
        Returns:
            List of GitHubAccount objects
        """
        return [acc for acc in self._accounts.values() if acc.has_capability(capability)]
    
    def get_trusted_accounts(self) -> List[str]:
        """
        Get list of trusted account usernames.
        
        Returns:
            List of trusted usernames (includes bot accounts like dependabot)
        """
        if not self._config:
            return []
        
        return self._config.get('trusted_accounts', [])
    
    def get_default_bot_account(self) -> Optional[GitHubAccount]:
        """
        Get the default bot account.
        
        Returns:
            Default bot GitHubAccount
        """
        if not self._config:
            return None
        
        default_username = self._config.get('default_bot_account', 'm0nk111-post')
        return self.get_account(default_username)
    
    def get_repository_owner(self) -> str:
        """
        Get the repository owner username.
        
        Returns:
            Repository owner username
        """
        if not self._config:
            return 'm0nk111'
        
        return self._config.get('repository_owner', 'm0nk111')
    
    def list_accounts(self) -> List[str]:
        """
        Get list of all account usernames.
        
        Returns:
            List of all usernames
        """
        return list(self._accounts.keys())
    
    def list_groups(self) -> List[str]:
        """
        Get list of all group names.
        
        Returns:
            List of group names
        """
        if not self._config:
            return []
        
        return list(self._config.get('groups', {}).keys())


# Global instance for easy access
_global_manager: Optional[AccountManager] = None


def get_account_manager() -> AccountManager:
    """
    Get global AccountManager instance (singleton pattern).
    
    Returns:
        Global AccountManager instance
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = AccountManager()
    return _global_manager


def get_account(username: str) -> Optional[GitHubAccount]:
    """
    Convenience function to get account.
    
    Args:
        username: GitHub username
    
    Returns:
        GitHubAccount if found
    """
    return get_account_manager().get_account(username)


def get_bot_account() -> Optional[GitHubAccount]:
    """
    Convenience function to get default bot account.
    
    Returns:
        Default bot GitHubAccount
    """
    return get_account_manager().get_default_bot_account()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = AccountManager()
    
    print("\n🔍 All Accounts:")
    for username in manager.list_accounts():
        account = manager.get_account(username)
        print(f"  - {username}: {account.email} ({account.role})")
    
    print("\n👥 Groups:")
    for group in manager.list_groups():
        members = manager.get_group(group)
        print(f"  - {group}: {', '.join(members)}")
    
    print("\n🤖 Bot Account:")
    bot = manager.get_default_bot_account()
    if bot:
        print(f"  Username: {bot.username}")
        print(f"  Email: {bot.email}")
        print(f"  Token available: {'✅' if bot.token else '❌'}")
    
    print("\n💻 All Coders:")
    coders = manager.get_accounts_by_group('coders')
    for coder in coders:
        print(f"  - {coder.username}: {coder.description}")
    
    print("\n🔐 Trusted Accounts:")
    for username in manager.get_trusted_accounts():
        print(f"  - {username}")
