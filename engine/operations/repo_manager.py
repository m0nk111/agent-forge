"""
Repository Manager - Automated repository access management for bot accounts.

This module handles:
- Inviting bot accounts to repositories
- Accepting repository invitations
- Verifying bot account access
- Managing collaborator permissions
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import yaml


logger = logging.getLogger(__name__)


class RepoManager:
    """Manage repository access for bot accounts."""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize Repository Manager.
        
        Args:
            project_root: Path to project root (auto-detected if not provided)
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Auto-detect from module location
            self.project_root = Path(__file__).parent.parent.parent.resolve()
        
        self.secrets_dir = self.project_root / 'secrets'
        self.config_dir = self.project_root / 'config'
        
        # Load configuration
        self.config = self._load_config()
        
        # Load tokens
        self.admin_token = self._load_token('m0nk111')
        self.bot_tokens = self._load_bot_tokens()
    
    def _load_config(self) -> Dict:
        """Load polling service configuration for repository list."""
        config_path = self.config_dir / 'services' / 'polling.yaml'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _load_token(self, agent_name: str) -> str:
        """
        Load GitHub token for a specific agent.
        
        Args:
            agent_name: Name of agent (e.g., 'm0nk111', 'm0nk111-post')
        
        Returns:
            GitHub personal access token
        
        Raises:
            FileNotFoundError: If token file doesn't exist
        """
        token_path = self.secrets_dir / 'agents' / f'{agent_name}.token'
        
        if not token_path.exists():
            raise FileNotFoundError(
                f"Token file not found: {token_path}\n"
                f"Create it with: echo 'ghp_xxx' > {token_path}"
            )
        
        token = token_path.read_text().strip()
        
        if not token or not token.startswith('ghp_'):
            raise ValueError(f"Invalid token in {token_path}")
        
        return token
    
    def _load_bot_tokens(self) -> Dict[str, str]:
        """
        Load all bot account tokens from secrets/agents/.
        
        Returns:
            Dictionary mapping bot names to tokens
        """
        agents_dir = self.secrets_dir / 'agents'
        bot_tokens = {}
        
        for token_file in agents_dir.glob('*.token'):
            agent_name = token_file.stem
            
            # Skip admin account
            if agent_name == 'm0nk111':
                continue
            
            try:
                token = token_file.read_text().strip()
                if token and token.startswith('ghp_'):
                    bot_tokens[agent_name] = token
                    logger.debug(f"🔑 Loaded token for {agent_name}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load token for {agent_name}: {e}")
        
        return bot_tokens
    
    def _github_request(
        self,
        method: str,
        url: str,
        token: str,
        json_data: Optional[Dict] = None
    ) -> Tuple[int, Optional[Dict]]:
        """
        Make GitHub API request.
        
        Args:
            method: HTTP method (GET, PUT, POST, PATCH)
            url: API endpoint URL
            token: GitHub token for authentication
            json_data: Optional JSON data for request body
        
        Returns:
            Tuple of (status_code, response_json)
        """
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            if method == 'GET':
                resp = requests.get(url, headers=headers)
            elif method == 'PUT':
                resp = requests.put(url, headers=headers, json=json_data)
            elif method == 'POST':
                resp = requests.post(url, headers=headers, json=json_data)
            elif method == 'PATCH':
                resp = requests.patch(url, headers=headers, json=json_data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if resp.status_code in [200, 201, 204]:
                try:
                    return resp.status_code, resp.json() if resp.text else None
                except:
                    return resp.status_code, None
            else:
                return resp.status_code, None
        
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return 0, None
    
    def get_repositories(self) -> List[str]:
        """
        Get list of repositories to manage from config.
        
        Returns:
            List of repository names (format: 'owner/repo')
        """
        return self.config.get('repositories', [])
    
    def get_bot_accounts(self) -> List[str]:
        """
        Get list of bot account names.
        
        Returns:
            List of bot account names (e.g., ['m0nk111-post', 'm0nk111-coder1'])
        """
        return list(self.bot_tokens.keys())
    
    def invite_bot_to_repo(self, repo: str, bot_name: str, permission: str = 'push') -> bool:
        """
        Invite a bot account to a repository.
        
        Args:
            repo: Repository name (format: 'owner/repo')
            bot_name: Bot account username
            permission: Permission level ('pull', 'push', 'admin')
        
        Returns:
            True if invitation sent/already member, False otherwise
        """
        # Check if already a collaborator
        check_url = f"https://api.github.com/repos/{repo}/collaborators/{bot_name}"
        status, _ = self._github_request('GET', check_url, self.admin_token)
        
        if status == 204:
            logger.info(f"✅ {bot_name} already has access to {repo}")
            return True
        
        # Invite as collaborator
        invite_url = f"https://api.github.com/repos/{repo}/collaborators/{bot_name}"
        data = {"permission": permission}
        status, _ = self._github_request('PUT', invite_url, self.admin_token, data)
        
        if status in [201, 204]:
            logger.info(f"✅ Invited {bot_name} to {repo}")
            return True
        elif status == 422:
            logger.warning(f"⚠️  {bot_name} not found or already invited to {repo}")
            return False
        else:
            logger.error(f"❌ Failed to invite {bot_name} to {repo}: status {status}")
            return False
    
    def accept_invitations(self, bot_name: str) -> int:
        """
        Accept all pending repository invitations for a bot account.
        
        Args:
            bot_name: Bot account username
        
        Returns:
            Number of invitations accepted
        """
        if bot_name not in self.bot_tokens:
            logger.error(f"❌ No token found for {bot_name}")
            return 0
        
        token = self.bot_tokens[bot_name]
        
        # Get pending invitations
        list_url = "https://api.github.com/user/repository_invitations"
        status, invites = self._github_request('GET', list_url, token)
        
        if status != 200 or not invites:
            if status == 401:
                logger.error(f"❌ Invalid token for {bot_name}")
            else:
                logger.info(f"✉️  No pending invitations for {bot_name}")
            return 0
        
        accepted = 0
        for invite in invites:
            repo_name = invite['repository']['full_name']
            invite_id = invite['id']
            
            # Accept invitation
            accept_url = f"https://api.github.com/user/repository_invitations/{invite_id}"
            status, _ = self._github_request('PATCH', accept_url, token)
            
            if status == 204:
                logger.info(f"✅ {bot_name} accepted invitation to {repo_name}")
                accepted += 1
            else:
                logger.error(f"❌ {bot_name} failed to accept {repo_name}: status {status}")
        
        return accepted
    
    def verify_access(self, repo: str, bot_name: str) -> bool:
        """
        Verify that a bot account has access to a repository.
        
        Args:
            repo: Repository name (format: 'owner/repo')
            bot_name: Bot account username
        
        Returns:
            True if bot has access, False otherwise
        """
        if bot_name not in self.bot_tokens:
            logger.error(f"❌ No token found for {bot_name}")
            return False
        
        token = self.bot_tokens[bot_name]
        
        # Try to get repository info (requires at least read access)
        repo_url = f"https://api.github.com/repos/{repo}"
        status, data = self._github_request('GET', repo_url, token)
        
        if status == 200:
            perms = data.get('permissions', {})
            has_push = perms.get('push', False)
            
            if has_push:
                logger.info(f"✅ {bot_name} has write access to {repo}")
            else:
                logger.warning(f"⚠️  {bot_name} has read-only access to {repo}")
            
            return True
        elif status == 404:
            logger.error(f"❌ {bot_name} has no access to {repo}")
            return False
        else:
            logger.error(f"❌ Failed to verify {bot_name} access to {repo}: status {status}")
            return False
    
    def setup_all_repositories(self, dry_run: bool = False) -> Dict[str, Dict]:
        """
        Invite all bot accounts to all configured repositories and accept invitations.
        
        Args:
            dry_run: If True, only show what would be done
        
        Returns:
            Dictionary with summary of operations
        """
        repos = self.get_repositories()
        bots = self.get_bot_accounts()
        
        summary = {
            'repos': len(repos),
            'bots': len(bots),
            'invited': 0,
            'accepted': 0,
            'verified': 0,
            'failed': 0
        }
        
        logger.info(f"🤖 Repository Setup: {len(repos)} repos × {len(bots)} bots")
        
        if dry_run:
            logger.info("🔍 DRY RUN - No changes will be made")
        
        # Step 1: Invite all bots to all repos
        logger.info("\n📤 Step 1: Inviting bot accounts...")
        for repo in repos:
            for bot in bots:
                if dry_run:
                    logger.info(f"   Would invite {bot} to {repo}")
                else:
                    if self.invite_bot_to_repo(repo, bot):
                        summary['invited'] += 1
                    else:
                        summary['failed'] += 1
        
        if not dry_run:
            # Wait for invitations to propagate
            logger.info("\n⏳ Waiting 5 seconds for invitations to propagate...")
            time.sleep(5)
        
        # Step 2: Accept invitations for each bot
        logger.info("\n📥 Step 2: Accepting invitations...")
        for bot in bots:
            if dry_run:
                logger.info(f"   Would accept invitations for {bot}")
            else:
                accepted = self.accept_invitations(bot)
                summary['accepted'] += accepted
        
        if not dry_run:
            # Wait for acceptances to propagate
            logger.info("\n⏳ Waiting 3 seconds for acceptances to propagate...")
            time.sleep(3)
        
        # Step 3: Verify access
        logger.info("\n✅ Step 3: Verifying access...")
        for repo in repos:
            for bot in bots:
                if dry_run:
                    logger.info(f"   Would verify {bot} access to {repo}")
                else:
                    if self.verify_access(repo, bot):
                        summary['verified'] += 1
                    else:
                        summary['failed'] += 1
        
        return summary


def main():
    """CLI entry point for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    try:
        manager = RepoManager()
        
        print("\n" + "="*60)
        print("Repository Manager - Configuration")
        print("="*60)
        print(f"Project Root: {manager.project_root}")
        print(f"Repositories: {len(manager.get_repositories())}")
        for repo in manager.get_repositories():
            print(f"  - {repo}")
        
        print(f"\nBot Accounts: {len(manager.get_bot_accounts())}")
        for bot in manager.get_bot_accounts():
            print(f"  - {bot}")
        
        print("\nRun with: python -m engine.operations.repo_manager")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
