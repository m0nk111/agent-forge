"""Team manager for automated collaborator management.

This module handles inviting bot accounts to repositories and auto-accepting
invitations. Part of the Project Bootstrap Agent system.
"""

import logging
import time
from typing import List, Dict, Optional
from engine.operations.github_api_helper import GitHubAPIHelper

logger = logging.getLogger(__name__)


class TeamManager:
    """Manages repository collaborators and invitations."""
    
    def __init__(self, admin_token: str, bot_tokens: Optional[Dict[str, str]] = None):
        """Initialize team manager.
        
        Args:
            admin_token: GitHub token with admin:org and repo scope
            bot_tokens: Dictionary mapping bot usernames to their tokens
                       Format: {"bot-username": "ghp_token123", ...}
        """
        self.admin_api = GitHubAPIHelper(token=admin_token)
        self.bot_tokens = bot_tokens or {}
        self.bot_apis = {}
        
        # Initialize API helpers for each bot
        for username, token in self.bot_tokens.items():
            self.bot_apis[username] = GitHubAPIHelper(token=token)
        
        logger.info(f"👥 Team Manager initialized with {len(self.bot_tokens)} bot accounts")
    
    def invite_collaborators(self,
                           owner: str,
                           repo: str,
                           collaborators: List[Dict[str, str]],
                           retry_delay: int = 2) -> Dict[str, bool]:
        """Invite multiple collaborators to a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            collaborators: List of dicts with 'username' and 'permission'
                          Example: [{"username": "bot1", "permission": "push"}]
            retry_delay: Delay in seconds between invitations
            
        Returns:
            Dictionary mapping usernames to invitation success status
            
        Raises:
            RuntimeError: If any critical invitations fail
        """
        logger.info(f"📨 Inviting {len(collaborators)} collaborators to {owner}/{repo}")
        
        results = {}
        failed = []
        
        for collab in collaborators:
            username = collab.get('username')
            permission = collab.get('permission', 'push')
            
            if not username:
                logger.warning("⚠️ Skipping collaborator with no username")
                continue
            
            try:
                logger.info(f"📬 Inviting {username} with {permission} permission")
                self.admin_api.add_collaborator(owner, repo, username, permission)
                results[username] = True
                logger.info(f"✅ Invitation sent to {username}")
                
                # Small delay to avoid rate limiting
                if retry_delay > 0:
                    time.sleep(retry_delay)
                
            except Exception as e:
                logger.error(f"❌ Failed to invite {username}: {e}")
                results[username] = False
                failed.append(username)
        
        if failed:
            logger.warning(f"⚠️ Failed to invite: {', '.join(failed)}")
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"✅ Invited {success_count}/{len(collaborators)} collaborators")
        
        return results
    
    def auto_accept_invitations(self,
                               bot_usernames: Optional[List[str]] = None,
                               max_retries: int = 3,
                               retry_delay: int = 5) -> Dict[str, List[str]]:
        """Automatically accept pending repository invitations for bot accounts.
        
        Args:
            bot_usernames: List of bot usernames to process (all bots if None)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay in seconds between retries
            
        Returns:
            Dictionary mapping bot usernames to list of accepted repositories
            Format: {"bot1": ["owner/repo1", "owner/repo2"], ...}
            
        Raises:
            RuntimeError: If invitation acceptance fails after retries
        """
        if bot_usernames is None:
            bot_usernames = list(self.bot_apis.keys())
        
        logger.info(f"🤖 Auto-accepting invitations for {len(bot_usernames)} bots")
        
        results = {}
        
        for username in bot_usernames:
            if username not in self.bot_apis:
                logger.warning(f"⚠️ No API token for bot {username}, skipping")
                continue
            
            bot_api = self.bot_apis[username]
            accepted_repos = []
            
            for attempt in range(max_retries):
                try:
                    # Fetch pending invitations
                    invitations = bot_api.list_repository_invitations()
                    
                    if not invitations:
                        logger.info(f"✅ No pending invitations for {username}")
                        break
                    
                    logger.info(f"📬 Found {len(invitations)} invitations for {username}")
                    
                    # Accept each invitation
                    for invitation in invitations:
                        inv_id = invitation['id']
                        repo_full_name = invitation['repository']['full_name']
                        
                        try:
                            bot_api.accept_repository_invitation(inv_id)
                            accepted_repos.append(repo_full_name)
                            logger.info(f"✅ {username} accepted invitation to {repo_full_name}")
                            
                            # Small delay between acceptances
                            time.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to accept invitation {inv_id}: {e}")
                    
                    # Success, break retry loop
                    break
                    
                except Exception as e:
                    logger.error(f"❌ Attempt {attempt + 1}/{max_retries} failed for {username}: {e}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"❌ Max retries reached for {username}")
            
            results[username] = accepted_repos
        
        total_accepted = sum(len(repos) for repos in results.values())
        logger.info(f"✅ Auto-accepted {total_accepted} invitations across {len(results)} bots")
        
        return results
    
    def setup_team(self,
                   owner: str,
                   repo: str,
                   bot_configs: List[Dict[str, str]],
                   auto_accept: bool = True,
                   accept_delay: int = 10) -> bool:
        """Complete team setup: invite and auto-accept for all bots.
        
        Args:
            owner: Repository owner
            repo: Repository name
            bot_configs: List of bot configurations with username and permission
            auto_accept: Whether to automatically accept invitations
            accept_delay: Delay in seconds before attempting auto-accept
            
        Returns:
            True if all steps succeeded
            
        Raises:
            RuntimeError: On setup failure
        """
        logger.info(f"🚀 Setting up team for {owner}/{repo}")
        
        try:
            # Step 1: Send invitations
            invite_results = self.invite_collaborators(owner, repo, bot_configs)
            
            invited_bots = [username for username, success in invite_results.items() if success]
            
            if not invited_bots:
                logger.error("❌ No bots were successfully invited")
                return False
            
            # Step 2: Auto-accept invitations (if enabled)
            if auto_accept:
                logger.info(f"⏳ Waiting {accept_delay} seconds for invitations to propagate...")
                time.sleep(accept_delay)
                
                accept_results = self.auto_accept_invitations(bot_usernames=invited_bots)
                
                # Verify all accepted
                for bot in invited_bots:
                    if bot not in accept_results or not accept_results[bot]:
                        logger.warning(f"⚠️ Bot {bot} did not accept invitation")
            
            logger.info(f"✅ Team setup complete for {owner}/{repo}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Team setup failed for {owner}/{repo}: {e}")
            raise RuntimeError(f"Team setup failed: {e}")
