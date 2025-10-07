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
    name: str
    model: str
    enabled: bool = True
    max_concurrent_tasks: int = 1
    polling_interval: int = 60  # seconds
    capabilities: List[str] = None
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
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.custom_settings is None:
            self.custom_settings = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


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
    """
    
    def __init__(self, config_dir: str = "/home/flip/agent-forge/config"):
        self.config_dir = Path(config_dir)
        self.agents_file = self.config_dir / "agents.yaml"
        self.repos_file = self.config_dir / "repositories.yaml"
        self.system_file = self.config_dir / "system.yaml"
        self.backup_dir = self.config_dir / "backups"
        
        # Create directories if they don't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty configs if files don't exist
        self._initialize_configs()
        
        logger.info(f"ConfigManager initialized: {self.config_dir}")
    
    def _initialize_configs(self):
        """Initialize configuration files with defaults if they don't exist"""
        if not self.agents_file.exists():
            self._save_yaml(self.agents_file, {"agents": []})
            logger.info("Created agents.yaml with empty configuration")
        
        if not self.repos_file.exists():
            self._save_yaml(self.repos_file, {"repositories": []})
            logger.info("Created repositories.yaml with empty configuration")
        
        if not self.system_file.exists():
            default_system = asdict(SystemConfig())
            self._save_yaml(self.system_file, default_system)
            logger.info("Created system.yaml with default configuration")
    
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
        """Get all agent configurations"""
        data = self._load_yaml(self.agents_file)
        agents = []
        for agent_data in data.get("agents", []):
            try:
                agents.append(AgentConfig(**agent_data))
            except Exception as e:
                logger.error(f"Failed to parse agent config: {e}")
        return agents
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get specific agent configuration"""
        agents = self.get_agents()
        for agent in agents:
            if agent.agent_id == agent_id:
                return agent
        return None
    
    def add_agent(self, agent: AgentConfig) -> bool:
        """Add new agent configuration"""
        try:
            data = self._load_yaml(self.agents_file)
            agents = data.get("agents", [])
            
            # Check if agent already exists
            if any(a.get("agent_id") == agent.agent_id for a in agents):
                logger.warning(f"Agent {agent.agent_id} already exists")
                return False
            
            # Add new agent
            agents.append(asdict(agent))
            data["agents"] = agents
            self._save_yaml(self.agents_file, data)
            
            logger.info(f"Added agent: {agent.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add agent: {e}")
            return False
    
    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent configuration"""
        try:
            data = self._load_yaml(self.agents_file)
            agents = data.get("agents", [])
            
            # Find and update agent
            for i, agent in enumerate(agents):
                if agent.get("agent_id") == agent_id:
                    agent.update(updates)
                    agent["updated_at"] = datetime.now().isoformat()
                    agents[i] = agent
                    data["agents"] = agents
                    self._save_yaml(self.agents_file, data)
                    logger.info(f"Updated agent: {agent_id}")
                    return True
            
            logger.warning(f"Agent {agent_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            return False
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent configuration"""
        try:
            data = self._load_yaml(self.agents_file)
            agents = data.get("agents", [])
            
            # Filter out the agent
            new_agents = [a for a in agents if a.get("agent_id") != agent_id]
            
            if len(new_agents) == len(agents):
                logger.warning(f"Agent {agent_id} not found")
                return False
            
            data["agents"] = new_agents
            self._save_yaml(self.agents_file, data)
            
            logger.info(f"Deleted agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
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
