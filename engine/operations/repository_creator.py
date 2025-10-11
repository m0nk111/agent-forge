"""Repository creator for automated project bootstrapping.

This module handles the creation of new GitHub repositories with proper configuration.
Part of the Project Bootstrap Agent system.
"""

import logging
from typing import Dict, Optional
from engine.operations.github_api_helper import GitHubAPIHelper

logger = logging.getLogger(__name__)


class RepositoryCreator:
    """Creates and configures new GitHub repositories."""
    
    def __init__(self, github_token: str):
        """Initialize repository creator.
        
        Args:
            github_token: GitHub API token with repo scope
        """
        self.api = GitHubAPIHelper(token=github_token)
        logger.info("🔨 Repository Creator initialized")
    
    def create_repository(self, 
                         name: str,
                         description: str = "",
                         private: bool = False,
                         organization: Optional[str] = None,
                         template: str = "python",
                         enable_auto_init: bool = True) -> Dict:
        """Create a new repository with basic configuration.
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether repository should be private
            organization: Organization name (creates user repo if None)
            template: Project template type ('python', 'typescript', 'node', etc.)
            enable_auto_init: Initialize with README
            
        Returns:
            Dictionary with repository details:
                - full_name: e.g., "owner/repo"
                - html_url: Repository URL
                - clone_url: Git clone URL
                - default_branch: Default branch name
                
        Raises:
            RuntimeError: On repository creation failure
        """
        logger.info(f"🚀 Creating repository: {name} (template: {template})")
        
        # Map template to gitignore template
        gitignore_map = {
            'python': 'Python',
            'typescript': 'Node',
            'node': 'Node',
            'go': 'Go',
            'rust': 'Rust',
            'java': 'Java'
        }
        gitignore_template = gitignore_map.get(template.lower(), 'Python')
        
        try:
            # Create repository
            repo_data = self.api.create_repository(
                name=name,
                description=description,
                private=private,
                organization=organization,
                auto_init=enable_auto_init,
                gitignore_template=gitignore_template,
                license_template='mit'  # Default to MIT license
            )
            
            result = {
                'full_name': repo_data['full_name'],
                'html_url': repo_data['html_url'],
                'clone_url': repo_data['clone_url'],
                'default_branch': repo_data.get('default_branch', 'main'),
                'owner': repo_data['owner']['login']
            }
            
            logger.info(f"✅ Repository created: {result['html_url']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to create repository {name}: {e}")
            raise RuntimeError(f"Repository creation failed: {e}")
    
    def configure_branch_protection(self,
                                   owner: str,
                                   repo: str,
                                   branch: str = "main",
                                   required_reviews: int = 1,
                                   require_code_owner_reviews: bool = False,
                                   enforce_admins: bool = False) -> bool:
        """Configure branch protection rules.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to protect
            required_reviews: Number of required approving reviews
            require_code_owner_reviews: Require CODEOWNERS review
            enforce_admins: Enforce protections for administrators
            
        Returns:
            True if successful
            
        Raises:
            RuntimeError: On configuration failure
        """
        logger.info(f"🔒 Configuring branch protection: {owner}/{repo}:{branch}")
        
        try:
            self.api.update_branch_protection(
                owner=owner,
                repo=repo,
                branch=branch,
                required_reviews=required_reviews,
                enforce_admins=enforce_admins,
                require_code_owner_reviews=require_code_owner_reviews
            )
            
            logger.info(f"✅ Branch protection configured for {owner}/{repo}:{branch}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to configure branch protection: {e}")
            raise RuntimeError(f"Branch protection configuration failed: {e}")
