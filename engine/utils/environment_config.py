"""
Environment Configuration Loader

Manages different environments (dev/test/prod) for Agent-Forge.
Prevents test commits from reaching production.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml


logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """Load and manage environment configuration."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize environment configuration.
        
        Args:
            project_root: Path to project root (auto-detected if not provided)
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Auto-detect from module location
            self.project_root = Path(__file__).parent.parent.parent.resolve()
        
        self.config_path = self.project_root / 'config' / 'system' / 'environments.yaml'
        self.config = self._load_config()
        self.active_env = self._get_active_environment()
        
        logger.info(f"🌍 Environment: {self.active_env}")
    
    def _load_config(self) -> Dict:
        """Load environment configuration from YAML."""
        if not self.config_path.exists():
            logger.warning(f"⚠️  Environment config not found: {self.config_path}")
            logger.warning("   Using default production settings")
            return self._get_default_config()
        
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _get_default_config(self) -> Dict:
        """Get default configuration (production)."""
        return {
            'active': 'production',
            'environments': {
                'production': {
                    'description': 'Production environment',
                    'dry_run': False,
                    'repositories': ['m0nk111/agent-forge'],
                    'max_concurrent_issues': 3,
                    'claim_timeout_minutes': 1440,
                    'auto_merge': False,
                    'notifications': {'enabled': True}
                }
            },
            'settings': {
                'test_only_repos': ['m0nk111/agent-forge-test'],
                'production_only_repos': ['m0nk111/agent-forge']
            }
        }
    
    def _get_active_environment(self) -> str:
        """
        Get active environment from config or environment variable.
        
        Priority:
        1. AGENT_FORGE_ENV environment variable
        2. environments.yaml 'active' field
        3. Default to 'production'
        """
        # Check environment variable first
        env_var = os.getenv('AGENT_FORGE_ENV')
        if env_var:
            if env_var in self.config.get('environments', {}):
                logger.info(f"🔧 Using environment from AGENT_FORGE_ENV: {env_var}")
                return env_var
            else:
                logger.warning(f"⚠️  Invalid AGENT_FORGE_ENV '{env_var}', using config default")
        
        # Use config file
        active = self.config.get('active', 'production')
        
        if active not in self.config.get('environments', {}):
            logger.warning(f"⚠️  Invalid active environment '{active}', defaulting to production")
            return 'production'
        
        return active
    
    def get_environment_config(self) -> Dict:
        """Get configuration for active environment."""
        return self.config['environments'][self.active_env]
    
    def get_repositories(self) -> List[str]:
        """Get repositories for active environment."""
        env_config = self.get_environment_config()
        return env_config.get('repositories', [])
    
    def is_test_mode(self) -> bool:
        """Check if running in test mode."""
        return self.active_env in ['development', 'test']
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.active_env == 'production'
    
    def is_dry_run(self) -> bool:
        """Check if dry-run mode is enabled."""
        env_config = self.get_environment_config()
        return env_config.get('dry_run', False)
    
    def can_auto_merge(self) -> bool:
        """Check if auto-merge is enabled for this environment."""
        env_config = self.get_environment_config()
        return env_config.get('auto_merge', False)
    
    def get_max_concurrent_issues(self) -> int:
        """Get max concurrent issues for this environment."""
        env_config = self.get_environment_config()
        return env_config.get('max_concurrent_issues', 3)
    
    def get_claim_timeout(self) -> int:
        """Get claim timeout in minutes for this environment."""
        env_config = self.get_environment_config()
        return env_config.get('claim_timeout_minutes', 1440)
    
    def is_test_only_repo(self, repo: str) -> bool:
        """Check if repository is test-only (never for production)."""
        test_repos = self.config.get('settings', {}).get('test_only_repos', [])
        return repo in test_repos
    
    def is_production_only_repo(self, repo: str) -> bool:
        """Check if repository is production-only (never for testing)."""
        prod_repos = self.config.get('settings', {}).get('production_only_repos', [])
        return repo in prod_repos
    
    def validate_repository_access(self, repo: str) -> bool:
        """
        Validate that repository is appropriate for current environment.
        
        Returns:
            True if repository can be accessed in current environment
        """
        # Test-only repos can't be accessed in production
        if self.is_production() and self.is_test_only_repo(repo):
            logger.error(f"❌ Cannot access test-only repo '{repo}' in production environment")
            return False
        
        # Production-only repos can't be accessed in test
        if self.is_test_mode() and self.is_production_only_repo(repo):
            logger.error(f"❌ Cannot access production repo '{repo}' in test environment")
            return False
        
        return True
    
    def get_environment_info(self) -> Dict:
        """Get comprehensive information about current environment."""
        env_config = self.get_environment_config()
        
        return {
            'environment': self.active_env,
            'description': env_config.get('description', ''),
            'dry_run': self.is_dry_run(),
            'test_mode': self.is_test_mode(),
            'production': self.is_production(),
            'repositories': self.get_repositories(),
            'max_concurrent_issues': self.get_max_concurrent_issues(),
            'claim_timeout_minutes': self.get_claim_timeout(),
            'auto_merge': self.can_auto_merge(),
            'notifications': env_config.get('notifications', {})
        }
    
    def print_environment_info(self):
        """Print environment information to console."""
        info = self.get_environment_info()
        
        print("\n" + "="*70)
        print(f"🌍 AGENT-FORGE ENVIRONMENT: {info['environment'].upper()}")
        print("="*70)
        print(f"\n📝 Description: {info['description']}")
        print(f"\n🔧 Mode:")
        print(f"   • Test Mode: {'✅ Yes' if info['test_mode'] else '❌ No'}")
        print(f"   • Production: {'✅ Yes' if info['production'] else '❌ No'}")
        print(f"   • Dry Run: {'✅ Yes' if info['dry_run'] else '❌ No'}")
        print(f"\n📦 Repositories ({len(info['repositories'])}):")
        for repo in info['repositories']:
            print(f"   • {repo}")
        print(f"\n⚙️  Settings:")
        print(f"   • Max Concurrent Issues: {info['max_concurrent_issues']}")
        print(f"   • Claim Timeout: {info['claim_timeout_minutes']} minutes")
        print(f"   • Auto-Merge: {'✅ Enabled' if info['auto_merge'] else '❌ Disabled'}")
        print(f"   • Notifications: {'✅ Enabled' if info['notifications'].get('enabled') else '❌ Disabled'}")
        print("="*70 + "\n")


if __name__ == '__main__':
    """Test environment configuration loading."""
    logging.basicConfig(level=logging.INFO)
    
    env = EnvironmentConfig()
    env.print_environment_info()
    
    # Test validation
    print("\n🧪 Repository Validation Tests:")
    print(f"   • agent-forge-test in test: {env.validate_repository_access('m0nk111/agent-forge-test')}")
    print(f"   • agent-forge in test: {env.validate_repository_access('m0nk111/agent-forge')}")
