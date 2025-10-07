#!/usr/bin/env python3
"""
Configuration Manager for Agent-Forge
Handles YAML-based configuration storage for agents, repositories, and system settings.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    agent_id: str
    name: Optional[str] = None  # Optional for bots
    model: Optional[str] = None  # Optional for bots
    enabled: bool = True
    max_concurrent_tasks: int = 1
    polling_interval: int = 60  # seconds
    capabilities: List[str] = None
    # Agent role for task assignment
    role: str = "developer"  # coordinator, developer, reviewer, tester, documenter, bot, researcher
    github_token: Optional[str] = None
    api_base_url: Optional[str] = None
    custom_settings: Dict[str, Any] = None
    # Shell access configuration (Issue #64)
    local_shell_enabled: bool = False
    shell_working_dir: Optional[str] = None
    shell_timeout: int = 300  # 5 minutes default
    shell_permissions: Optional[str] = "developer"  # Permission preset: read_only, developer, admin
    # LLM provider configuration (Issue #31)
    model_provider: str = "local"  # openai, anthropic, google, local
    model_name: str = "qwen2.5-coder"  # Specific model name
    api_key_name: Optional[str] = None  # Reference to key in keys.json (e.g., "OPENAI_API_KEY")
    temperature: float = 0.7  # Temperature for generation (0.0-2.0)
    max_tokens: int = 4096  # Maximum tokens to generate
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.custom_settings is None:
            self.custom_settings = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        # Auto-fill name from agent_id if not set (for bots)
        if self.name is None:
            self.name = self.agent_id.replace('-', ' ').title()
        # Model not required for bots (role == "bot")
        if self.model is None and self.role != "bot":
            self.model = "qwen2.5-coder"  # Default model


@dataclass
class RepositoryConfig:
    """Configuration for a GitHub repository"""
    repo_id: str
    owner: str
    name: str
    enabled: bool = True
    auto_assign_issues: bool = True
    issue_labels: List[str] = None
    branch_prefix: str = "feature"
    require_review: bool = True
    auto_merge: bool = False
    webhook_url: Optional[str] = None
    custom_settings: Dict[str, Any] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.issue_labels is None:
            self.issue_labels = []
        if self.custom_settings is None:
            self.custom_settings = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


@dataclass
class SystemConfig:
    """System-wide configuration"""
    monitoring_enabled: bool = True
    monitoring_port: int = 7997
    log_level: str = "INFO"
    max_log_size: int = 10000
    backup_enabled: bool = True
    backup_interval: int = 86400  # 24 hours
    notification_email: Optional[str] = None
    slack_webhook: Optional[str] = None
    custom_settings: Dict[str, Any] = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.custom_settings is None:
            self.custom_settings = {}
        self.updated_at = datetime.now().isoformat()


class ConfigManager:
    """
    Manages configuration for Agent-Forge system.
    Stores configuration in YAML files with backup support.
    Loads sensitive tokens from secrets/ directory.
    """
    
    def __init__(self, config_dir: str = None):
        # Auto-detect config directory based on current working directory
        if config_dir is None:
            # Try to find the project root by looking for a marker file
            current_dir = Path.cwd()
            # Look for config directory in current dir or parent dirs
            for parent in [current_dir] + list(current_dir.parents):
                potential_config = parent / "config"
                if potential_config.exists():
                    config_dir = str(potential_config)
                    break
            
            # Fallback to relative path if not found
            if config_dir is None:
                config_dir = str(Path(__file__).parent.parent.parent / "config")
        
        self.config_dir = Path(config_dir)
        
        # NEW: Hierarchical config structure by purpose
        self.agents_dir = self.config_dir / "agents"  # GitHub account configs
        self.services_dir = self.config_dir / "services"  # Local orchestrator configs
        self.system_dir = self.config_dir / "system"  # Core system configs
        self.rules_dir = self.config_dir / "rules"  # Policies and validation rules
        
        # Individual config files in subdirectories
        self.agents_file = self.config_dir / "agents.yaml"  # LEGACY: Fallback
        self.trusted_file = self.system_dir / "trusted_agents.yaml"  # Trust list
        self.repos_file = self.system_dir / "repositories.yaml"  # Monitored repos
        self.system_file = self.system_dir / "system.yaml"  # System settings
        self.backup_dir = self.config_dir / "backups"
        
        # Secrets directory for tokens
        self.secrets_dir = self.config_dir.parent / "secrets" / "agents"
        
        # Create directories if they don't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.services_dir.mkdir(parents=True, exist_ok=True)
        self.system_dir.mkdir(parents=True, exist_ok=True)
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty configs if files don't exist
        self._initialize_configs()
        
        logger.info(f"ConfigManager initialized: {self.config_dir}")
        logger.info(f"Agents directory: {self.agents_dir}")
        logger.info(f"Services directory: {self.services_dir}")
        logger.info(f"System directory: {self.system_dir}")
        logger.info(f"Rules directory: {self.rules_dir}")
        logger.info(f"Secrets directory: {self.secrets_dir}")
    
    def _initialize_configs(self):
        """Initialize configuration files with defaults if they don't exist"""
        # Only create legacy agents.yaml if no agents/ directory exists
        if not self.agents_file.exists() and not self.agents_dir.exists():
            self._save_yaml(self.agents_file, {"agents": []})
            logger.info("Created agents.yaml with empty configuration")
        
        if not self.repos_file.exists():
            self._save_yaml(self.repos_file, {"repositories": []})
            logger.info("Created system/repositories.yaml with empty configuration")
        
        if not self.system_file.exists():
            default_system = asdict(SystemConfig())
            self._save_yaml(self.system_file, default_system)
            logger.info("Created system/system.yaml with default configuration")
    
    def _load_yaml(self, file_path: Path) -> Dict:
        """Load YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}
    
    def _save_yaml(self, file_path: Path, data: Dict):
        """Save YAML file with backup"""
        try:
            # Create backup before saving
            if file_path.exists():
                backup_name = f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
                backup_path = self.backup_dir / backup_name
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")
            
            # Save new configuration
            with open(file_path, 'w') as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved configuration to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")
            raise
    
    # ==================== AGENT MANAGEMENT ====================
    
    def get_agents(self) -> List[AgentConfig]:
        """Get all agent configurations from agents/ directory"""
        agents = []
        
        # Load from individual agent YAML files (NEW)
        if self.agents_dir.exists():
            for agent_file in self.agents_dir.glob("*.yaml"):
                if agent_file.name == "trusted_agents.yaml":
                    continue  # Skip trust list
                try:
                    agent_data = self._load_yaml(agent_file)
                    if agent_data:
                        # Extract from root key if present (bot:, agent:, coordinator:, service:)
                        # Support both old format with root keys and new flat format
                        if len(agent_data) == 1 and isinstance(list(agent_data.values())[0], dict):
                            # Old format: {bot: {agent_id: ..., ...}}
                            agent_data = list(agent_data.values())[0]
                        
                        # Filter to only fields that AgentConfig supports
                        valid_fields = {
                            'agent_id', 'name', 'model', 'enabled', 'max_concurrent_tasks',
                            'polling_interval', 'capabilities', 'role', 'github_token',
                            'api_base_url', 'custom_settings', 'local_shell_enabled',
                            'shell_working_dir', 'shell_timeout', 'shell_permissions',
                            'model_provider', 'model_name', 'api_key_name', 'temperature',
                            'max_tokens', 'created_at', 'updated_at'
                        }
                        filtered_data = {k: v for k, v in agent_data.items() if k in valid_fields}
                        
                        agents.append(AgentConfig(**filtered_data))
                        logger.debug(f"✅ Loaded agent from {agent_file.name}")
                except Exception as e:
                    logger.error(f"Failed to parse {agent_file}: {e}")
        
        # Fallback to legacy agents.yaml if no individual files found
        if not agents and self.agents_file.exists():
            logger.warning("No agents found in agents/ directory, falling back to config/agents.yaml")
            data = self._load_yaml(self.agents_file)
            for agent_data in data.get("agents", []):
                try:
                    agents.append(AgentConfig(**agent_data))
                except Exception as e:
                    logger.error(f"Failed to parse agent config: {e}")
        
        return agents
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get specific agent configuration with token loaded from secrets"""
        agents = self.get_agents()
        for agent in agents:
            if agent.agent_id == agent_id:
                # Load token from secrets if not in config
                if not agent.github_token:
                    agent.github_token = self._load_token(agent_id)
                return agent
        return None
    
    def _load_token(self, agent_id: str) -> Optional[str]:
        """Load GitHub token from secrets directory"""
        token_file = self.secrets_dir / f"{agent_id}.token"
        if token_file.exists():
            try:
                token = token_file.read_text().strip()
                logger.debug(f"🔑 Loaded token for {agent_id} from secrets")
                return token
            except Exception as e:
                logger.error(f"Failed to load token for {agent_id}: {e}")
        return None
    
    def add_agent(self, agent: AgentConfig) -> bool:
        """Add new agent configuration to individual YAML file"""
        try:
            agent_file = self.agents_dir / f"{agent.agent_id}.yaml"
            
            # Check if agent already exists
            if agent_file.exists():
                logger.warning(f"Agent {agent.agent_id} already exists")
                return False
            
            # Save to individual file
            self._save_yaml(agent_file, asdict(agent))
            
            logger.info(f"✅ Added agent: {agent.agent_id} → {agent_file.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add agent: {e}")
            return False
    
    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent configuration in individual YAML file"""
        try:
            agent_file = self.agents_dir / f"{agent_id}.yaml"
            
            if not agent_file.exists():
                logger.error(f"Agent {agent_id} not found")
                return False
            
            # Load current config
            agent_data = self._load_yaml(agent_file)
            
            # Update fields
            agent_data.update(updates)
            agent_data["updated_at"] = datetime.now().isoformat()
            
            # Save updated config
            self._save_yaml(agent_file, agent_data)
            
            logger.info(f"✅ Updated agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            return False
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent configuration file"""
        try:
            agent_file = self.agents_dir / f"{agent_id}.yaml"
            
            if not agent_file.exists():
                logger.warning(f"Agent {agent_id} not found")
                return False
            
            # Delete the agent file
            agent_file.unlink()
            
            logger.info(f"✅ Deleted agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            return False
            return False
    
    # ==================== REPOSITORY MANAGEMENT ====================
    
    def get_repositories(self) -> List[RepositoryConfig]:
        """Get all repository configurations"""
        data = self._load_yaml(self.repos_file)
        repos = []
        for repo_data in data.get("repositories", []):
            try:
                repos.append(RepositoryConfig(**repo_data))
            except Exception as e:
                logger.error(f"Failed to parse repository config: {e}")
        return repos
    
    def get_repository(self, repo_id: str) -> Optional[RepositoryConfig]:
        """Get specific repository configuration"""
        repos = self.get_repositories()
        for repo in repos:
            if repo.repo_id == repo_id:
                return repo
        return None
    
    def add_repository(self, repo: RepositoryConfig) -> bool:
        """Add new repository configuration"""
        try:
            data = self._load_yaml(self.repos_file)
            repos = data.get("repositories", [])
            
            # Check if repository already exists
            if any(r.get("repo_id") == repo.repo_id for r in repos):
                logger.warning(f"Repository {repo.repo_id} already exists")
                return False
            
            # Add new repository
            repos.append(asdict(repo))
            data["repositories"] = repos
            self._save_yaml(self.repos_file, data)
            
            logger.info(f"Added repository: {repo.repo_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add repository: {e}")
            return False
    
    def update_repository(self, repo_id: str, updates: Dict[str, Any]) -> bool:
        """Update repository configuration"""
        try:
            data = self._load_yaml(self.repos_file)
            repos = data.get("repositories", [])
            
            # Find and update repository
            for i, repo in enumerate(repos):
                if repo.get("repo_id") == repo_id:
                    repo.update(updates)
                    repo["updated_at"] = datetime.now().isoformat()
                    repos[i] = repo
                    data["repositories"] = repos
                    self._save_yaml(self.repos_file, data)
                    logger.info(f"Updated repository: {repo_id}")
                    return True
            
            logger.warning(f"Repository {repo_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to update repository: {e}")
            return False
    
    def delete_repository(self, repo_id: str) -> bool:
        """Delete repository configuration"""
        try:
            data = self._load_yaml(self.repos_file)
            repos = data.get("repositories", [])
            
            # Filter out the repository
            new_repos = [r for r in repos if r.get("repo_id") != repo_id]
            
            if len(new_repos) == len(repos):
                logger.warning(f"Repository {repo_id} not found")
                return False
            
            data["repositories"] = new_repos
            self._save_yaml(self.repos_file, data)
            
            logger.info(f"Deleted repository: {repo_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete repository: {e}")
            return False
    
    # ==================== SYSTEM CONFIGURATION ====================
    
    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        data = self._load_yaml(self.system_file)
        try:
            return SystemConfig(**data)
        except Exception as e:
            logger.error(f"Failed to parse system config: {e}")
            return SystemConfig()
    
    def update_system_config(self, updates: Dict[str, Any]) -> bool:
        """Update system configuration"""
        try:
            data = self._load_yaml(self.system_file)
            data.update(updates)
            data["updated_at"] = datetime.now().isoformat()
            self._save_yaml(self.system_file, data)
            
            logger.info("Updated system configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to update system config: {e}")
            return False
    
    # ==================== BACKUP MANAGEMENT ====================
    
    def cleanup_old_backups(self, keep_days: int = 7):
        """Delete backups older than specified days"""
        try:
            cutoff_time = datetime.now().timestamp() - (keep_days * 86400)
            deleted = 0
            
            for backup_file in self.backup_dir.glob("*.yaml"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    deleted += 1
            
            logger.info(f"Cleaned up {deleted} old backups")
        except Exception as e:
            logger.error(f"Failed to cleanup backups: {e}")
    
    def restore_from_backup(self, backup_name: str):
        """Restore configuration from backup"""
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_name}")
                return False
            
            # Determine which config file to restore
            if "agents" in backup_name:
                target = self.agents_file
            elif "repositories" in backup_name:
                target = self.repos_file
            elif "system" in backup_name:
                target = self.system_file
            else:
                logger.error(f"Unknown backup type: {backup_name}")
                return False
            
            # Restore backup
            shutil.copy2(backup_path, target)
            logger.info(f"Restored {target.name} from {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False


# Singleton instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get singleton ConfigManager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


if __name__ == "__main__":
    # Test configuration manager
    logging.basicConfig(level=logging.INFO)
    
    manager = get_config_manager()
    
    # Test agent management
    test_agent = AgentConfig(
        agent_id="test_agent_1",
        name="Test Agent",
        model="gpt-4",
        capabilities=["code_review", "issue_triage"]
    )
    
    print("\n=== Testing Agent Management ===")
    manager.add_agent(test_agent)
    agents = manager.get_agents()
    print(f"Total agents: {len(agents)}")
    
    agent = manager.get_agent("test_agent_1")
    print(f"Retrieved agent: {agent.name}")
    
    manager.update_agent("test_agent_1", {"enabled": False})
    updated = manager.get_agent("test_agent_1")
    print(f"Updated agent enabled: {updated.enabled}")
    
    # Test repository management
    test_repo = RepositoryConfig(
        repo_id="test_repo_1",
        owner="m0nk111",
        name="agent-forge",
        issue_labels=["bug", "enhancement"]
    )
    
    print("\n=== Testing Repository Management ===")
    manager.add_repository(test_repo)
    repos = manager.get_repositories()
    print(f"Total repositories: {len(repos)}")
    
    # Test system config
    print("\n=== Testing System Configuration ===")
    system = manager.get_system_config()
    print(f"Monitoring enabled: {system.monitoring_enabled}")
    print(f"Monitoring port: {system.monitoring_port}")
    
    manager.update_system_config({"log_level": "DEBUG"})
    updated_system = manager.get_system_config()
    print(f"Updated log level: {updated_system.log_level}")
    
    print("\n=== Configuration Manager Test Complete ===")
