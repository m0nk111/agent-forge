"""
Git operations for autonomous agent commits and pushes.

This module provides GitOperations class to handle:
- Git identity configuration per repository
- Commits with agent signatures
- Authenticated push operations using PAT
- Branch creation and management

Usage:
    from git_operations import GitOperations
    
    git = GitOperations()
    git.commit('/path/to/repo', 'Implement feature X', phase=2)
    git.push('/path/to/repo')
"""

import os
import subprocess
from typing import Optional
from pathlib import Path


class GitOperations:
    """Handle Git operations with agent identity."""
    
    def __init__(self):
        """Initialize with credentials from environment."""
        super().__init__()
        self.username = os.getenv('CODEAGENT_GITHUB_USERNAME', 'm0nk111-qwen-agent')
        self.email = os.getenv('CODEAGENT_GITHUB_EMAIL', 'aicodingtime@gmail.com')
        self.token = os.getenv('CODEAGENT_GITHUB_TOKEN')
        
        if not self.token:
            raise ValueError(
                "CODEAGENT_GITHUB_TOKEN not set in environment.\n"
                "Run: source ~/.agent-forge.env"
            )
        
        # Initialize instruction validator (optional)
        self.validator = None
        try:
            from engine.validation.instruction_validator import InstructionValidator
            self.validator = InstructionValidator()
        except Exception:
            # Validator is optional - continue without it
            pass
    
    def configure_identity(self, repo_path: str) -> bool:
        """
        Configure git identity for repository.
        
        Args:
            repo_path: Absolute path to git repository
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ['git', 'config', 'user.name', self.username],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'config', 'user.email', self.email],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to configure git identity: {e.stderr.decode()}")
            return False
    
    def get_status(self, repo_path: str) -> Optional[str]:
        """
        Get git status for repository.
        
        Args:
            repo_path: Absolute path to git repository
            
        Returns:
            Git status output or None on error
        """
        try:
            result = subprocess.run(
                ['git', 'status', '--short'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get git status: {e.stderr}")
            return None
    
    def commit(
        self,
        repo_path: str,
        message: str,
        phase: Optional[int] = None,
        task: Optional[str] = None
    ) -> bool:
        """
        Commit changes with agent signature.
        
        Args:
            repo_path: Absolute path to git repository
            message: Commit message
            phase: Optional phase number
            task: Optional task description
            
        Returns:
            True if successful, False otherwise
        """
        # Validate commit message format
        if self.validator:
            try:
                result = self.validator.validate_commit_message(message)
                if not result.valid:
                    print(f"⚠️  {result.message}")
                    if result.suggestions:
                        print(f"   💡 Suggestion: {result.suggestions[0]}")
                    
                    # Try auto-fix
                    if result.auto_fixable:
                        fixed = self.validator.auto_fix_commit_message(message)
                        if fixed:
                            print(f"   🔧 Auto-fixed to: {fixed.split(chr(10))[0]}")
                            message = fixed
            except Exception:
                # Don't fail on validator errors
                pass
        
        # Build commit message with agent signature
        signature = f"\n\nAgent: Qwen2.5-Coder 7B"
        if phase:
            signature += f"\nPhase: {phase}"
        if task:
            signature += f"\nTask: {task}"
        
        full_message = message + signature
        
        try:
            # Configure identity
            if not self.configure_identity(repo_path):
                return False
            
            # Check if there are changes to commit
            status = self.get_status(repo_path)
            if not status or not status.strip():
                print("ℹ️  No changes to commit")
                return True
            
            # Stage all changes
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            
            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', full_message],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Committed: {message}")
            if phase:
                print(f"   Phase: {phase}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
            print(f"❌ Commit failed: {stderr}")
            return False
    
    def push(
        self,
        repo_path: str,
        branch: str = 'main',
        force: bool = False
    ) -> bool:
        """
        Push changes to remote repository.
        
        Args:
            repo_path: Absolute path to git repository
            branch: Branch name to push (default: main)
            force: Force push (use with caution!)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get remote URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Replace URL with authenticated version
            if remote_url.startswith('https://github.com/'):
                auth_url = remote_url.replace(
                    'https://github.com/',
                    f'https://{self.token}@github.com/'
                )
            elif remote_url.startswith('git@github.com:'):
                # Convert SSH to HTTPS with token
                repo_path_str = remote_url.replace('git@github.com:', '').replace('.git', '')
                auth_url = f'https://{self.token}@github.com/{repo_path_str}.git'
            else:
                print(f"⚠️  Unexpected remote URL format: {remote_url}")
                auth_url = remote_url
            
            # Build push command
            push_cmd = ['git', 'push', auth_url, branch]
            if force:
                push_cmd.insert(2, '--force')
            
            # Push
            result = subprocess.run(
                push_cmd,
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Pushed to {branch}")
            return True
            
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
            print(f"❌ Push failed: {stderr}")
            
            # Check for common errors
            if "Permission denied" in stderr or "403" in stderr:
                print("💡 Hint: Check if agent is added as collaborator with Write access")
            elif "rejected" in stderr:
                print("💡 Hint: Remote has changes. Pull first or use force=True (careful!)")
            
            return False
    
    def create_branch(self, repo_path: str, branch_name: str) -> bool:
        """
        Create and checkout new branch.
        
        Args:
            repo_path: Absolute path to git repository
            branch_name: Name for new branch
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            print(f"✅ Created branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
            print(f"❌ Branch creation failed: {stderr}")
            return False
    
    def checkout(self, repo_path: str, branch_name: str) -> bool:
        """
        Checkout existing branch.
        
        Args:
            repo_path: Absolute path to git repository
            branch_name: Name of branch to checkout
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ['git', 'checkout', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            print(f"✅ Checked out: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
            print(f"❌ Checkout failed: {stderr}")
            return False
    
    def pull(self, repo_path: str, branch: str = 'main') -> bool:
        """
        Pull changes from remote.
        
        Args:
            repo_path: Absolute path to git repository
            branch: Branch name to pull (default: main)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ['git', 'pull', 'origin', branch],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            print(f"✅ Pulled from {branch}")
            return True
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
            print(f"❌ Pull failed: {stderr}")
            return False


if __name__ == '__main__':
    """Test git operations."""
    import sys
    
    # Test configuration
    try:
        git = GitOperations()
        print(f"✅ GitOperations initialized")
        print(f"   Username: {git.username}")
        print(f"   Email: {git.email}")
        print(f"   Token: {git.token[:20]}... (hidden)")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Test on agent-forge repo
    repo = "/home/flip/agent-forge"
    if Path(repo).exists():
        print(f"\n📂 Testing on {repo}")
        
        # Test identity configuration
        if git.configure_identity(repo):
            print("✅ Identity configured")
        
        # Test status
        status = git.get_status(repo)
        if status is not None:
            print(f"✅ Git status retrieved:")
            print(f"   {status if status else '(clean)'}")
    else:
        print(f"⚠️  Repository not found: {repo}")
