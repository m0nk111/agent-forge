"""Project bootstrap coordinator for automated repository setup.

This module orchestrates the complete repository bootstrap process:
1. Create repository with basic configuration
2. Invite bot collaborators
3. Generate project structure from template
4. Push initial files to repository
5. Configure branch protection and CI/CD

Part of the Project Bootstrap Agent system.
"""

import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Optional
from engine.operations.repository_creator import RepositoryCreator
from engine.operations.team_manager import TeamManager
from engine.operations.structure_generator import StructureGenerator

logger = logging.getLogger(__name__)


class BootstrapCoordinator:
    """Coordinates the complete repository bootstrap process."""
    
    def __init__(self, 
                 admin_token: str,
                 bot_tokens: Optional[Dict[str, str]] = None):
        """Initialize bootstrap coordinator.
        
        Args:
            admin_token: GitHub token with admin:org and repo scope
            bot_tokens: Dictionary mapping bot usernames to tokens
        """
        self.repo_creator = RepositoryCreator(admin_token)
        self.team_manager = TeamManager(admin_token, bot_tokens)
        self.structure_generator = StructureGenerator()
        self.admin_token = admin_token
        
        logger.info("🚀 Bootstrap Coordinator initialized")
    
    def bootstrap_repository(self,
                            name: str,
                            description: str = "",
                            template: str = "python",
                            private: bool = False,
                            organization: Optional[str] = None,
                            bot_collaborators: Optional[List[Dict[str, str]]] = None,
                            enable_branch_protection: bool = True,
                            required_reviews: int = 1) -> Dict:
        """Complete repository bootstrap workflow.
        
        Args:
            name: Repository name
            description: Repository description
            template: Project template ('python', 'typescript', 'go')
            private: Whether repository should be private
            organization: Organization name (user repo if None)
            bot_collaborators: List of bot configs with username and permission
            enable_branch_protection: Enable branch protection rules
            required_reviews: Number of required PR reviews
            
        Returns:
            Dictionary with bootstrap results:
                - repository: Repository details
                - team: Invitation results
                - files: Number of files created
                - protection: Branch protection status
                
        Raises:
            RuntimeError: On bootstrap failure
        """
        logger.info(f"🚀 Starting repository bootstrap: {name}")
        
        results = {
            'repository': None,
            'team': None,
            'files': 0,
            'protection': False
        }
        
        try:
            # Step 1: Create repository
            logger.info("📝 Step 1/5: Creating repository...")
            repo_data = self.repo_creator.create_repository(
                name=name,
                description=description,
                private=private,
                organization=organization,
                template=template,
                enable_auto_init=True  # Creates initial README
            )
            results['repository'] = repo_data
            logger.info(f"✅ Repository created: {repo_data['html_url']}")
            
            # Step 2: Invite bot collaborators
            if bot_collaborators:
                logger.info("👥 Step 2/5: Setting up team...")
                owner = repo_data['owner']
                repo_name = name
                
                team_setup = self.team_manager.setup_team(
                    owner=owner,
                    repo=repo_name,
                    bot_configs=bot_collaborators,
                    auto_accept=True,
                    accept_delay=10
                )
                results['team'] = team_setup
                logger.info("✅ Team setup complete")
            else:
                logger.info("⏭️  Step 2/5: No bot collaborators to invite")
            
            # Step 3: Generate project structure
            logger.info("📁 Step 3/5: Generating project structure...")
            structure = self.structure_generator.generate_structure(
                template=template,
                project_name=name,
                description=description,
                owner=repo_data['owner']
            )
            results['files'] = structure['file_count']
            logger.info(f"✅ Generated {structure['file_count']} files")
            
            # Step 4: Push files to repository
            logger.info("📤 Step 4/5: Pushing files to repository...")
            push_success = self._push_files_to_repo(
                repo_data=repo_data,
                files=structure['data'],
                template=template
            )
            
            if push_success:
                logger.info("✅ Files pushed successfully")
            else:
                logger.warning("⚠️ File push completed with warnings")
            
            # Step 5: Configure branch protection
            if enable_branch_protection:
                logger.info("🔒 Step 5/5: Configuring branch protection...")
                try:
                    protection_success = self.repo_creator.configure_branch_protection(
                        owner=repo_data['owner'],
                        repo=name,
                        branch=repo_data['default_branch'],
                        required_reviews=required_reviews,
                        require_code_owner_reviews=False,
                        enforce_admins=False
                    )
                    results['protection'] = protection_success
                    logger.info("✅ Branch protection configured")
                except Exception as e:
                    logger.warning(f"⚠️ Branch protection failed (may need manual setup): {e}")
            else:
                logger.info("⏭️  Step 5/5: Branch protection disabled")
            
            logger.info(f"🎉 Repository bootstrap complete: {repo_data['html_url']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Repository bootstrap failed: {e}")
            raise RuntimeError(f"Bootstrap failed: {e}")
    
    def _push_files_to_repo(self,
                           repo_data: Dict,
                           files: Dict[str, str],
                           template: str) -> bool:
        """Push generated files to repository using git.
        
        Args:
            repo_data: Repository information from create_repository
            files: Dictionary mapping file paths to contents
            template: Project template name
            
        Returns:
            True if successful
        """
        clone_url = repo_data['clone_url']
        default_branch = repo_data['default_branch']
        
        # Use token authentication in clone URL
        auth_clone_url = clone_url.replace(
            'https://',
            f'https://x-access-token:{self.admin_token}@'
        )
        
        # Create temporary directory for git operations
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                logger.info(f"📥 Cloning repository to temporary directory...")
                
                # Clone repository
                subprocess.run(
                    ['git', 'clone', auth_clone_url, tmpdir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Configure git
                subprocess.run(
                    ['git', 'config', 'user.name', 'Agent Forge Bot'],
                    cwd=tmpdir,
                    check=True
                )
                subprocess.run(
                    ['git', 'config', 'user.email', 'bot@agent-forge.dev'],
                    cwd=tmpdir,
                    check=True
                )
                
                # Create files
                logger.info(f"📝 Creating {len(files)} files...")
                for file_path, content in files.items():
                    full_path = os.path.join(tmpdir, file_path)
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Write file
                    with open(full_path, 'w') as f:
                        f.write(content)
                
                # Add LICENSE file
                license_content = self.structure_generator.get_license_content(
                    license_type='mit',
                    owner=repo_data['owner']
                )
                with open(os.path.join(tmpdir, 'LICENSE'), 'w') as f:
                    f.write(license_content)
                
                # Git add, commit, push
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=tmpdir,
                    check=True
                )
                
                subprocess.run(
                    ['git', 'commit', '-m', f'feat: Initialize {template} project structure\n\nGenerated by Agent Forge Bootstrap Agent'],
                    cwd=tmpdir,
                    check=True
                )
                
                subprocess.run(
                    ['git', 'push', 'origin', default_branch],
                    cwd=tmpdir,
                    check=True,
                    capture_output=True
                )
                
                logger.info("✅ Files pushed to repository")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Git operation failed: {e}")
                if e.stderr:
                    logger.error(f"Git error: {e.stderr}")
                return False
            except Exception as e:
                logger.error(f"❌ Failed to push files: {e}")
                return False
    
    def list_available_templates(self) -> List[Dict[str, str]]:
        """List available project templates.
        
        Returns:
            List of template info with name and description
        """
        return self.structure_generator.list_templates()
