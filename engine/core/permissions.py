#!/usr/bin/env python3
"""
Agent Permission System

Manages granular permissions for agents with role-based presets.
Critical for security when granting shell access and other sensitive capabilities.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)


class PermissionCategory(Enum):
    """Permission categories for organizational grouping"""
    FILE_SYSTEM = "file_system"
    TERMINAL = "terminal"
    GITHUB = "github"
    API = "api"
    SYSTEM = "system"


class Permission(Enum):
    """Individual permissions agents can be granted"""
    
    # File System Permissions
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_EXECUTE = "file_execute"
    
    # Terminal Permissions (NEW - Issue #64)
    TERMINAL_READ = "terminal_read"          # View terminal output
    TERMINAL_EXECUTE = "terminal_execute"    # Run commands
    TERMINAL_INSTALL = "terminal_install"    # Install packages (apt/pip/npm)
    TERMINAL_BACKGROUND = "terminal_background"  # Start background processes
    TERMINAL_KILL = "terminal_kill"          # Kill processes
    
    # GitHub Permissions
    GITHUB_READ = "github_read"
    GITHUB_CREATE_ISSUE = "github_create_issue"
    GITHUB_CREATE_PR = "github_create_pr"
    GITHUB_MERGE_PR = "github_merge_pr"      # Dangerous
    GITHUB_CLOSE_ISSUE = "github_close_issue"
    GITHUB_ASSIGN = "github_assign"
    
    # API Permissions
    API_EXTERNAL = "api_external"
    API_LLM = "api_llm"
    API_WEBHOOK = "api_webhook"
    
    # System Permissions
    SYSTEM_CONFIG = "system_config"
    SYSTEM_LOGS = "system_logs"
    SYSTEM_RESTART = "system_restart"        # Dangerous


@dataclass
class PermissionMetadata:
    """Metadata about a permission"""
    permission: Permission
    category: PermissionCategory
    description: str
    is_dangerous: bool = False
    warning_message: Optional[str] = None
    required_for: List[str] = field(default_factory=list)


# Permission metadata registry
PERMISSION_METADATA: Dict[Permission, PermissionMetadata] = {
    # File System
    Permission.FILE_READ: PermissionMetadata(
        permission=Permission.FILE_READ,
        category=PermissionCategory.FILE_SYSTEM,
        description="Read file contents from the repository",
        is_dangerous=False,
        required_for=["Code analysis", "File inspection"]
    ),
    Permission.FILE_WRITE: PermissionMetadata(
        permission=Permission.FILE_WRITE,
        category=PermissionCategory.FILE_SYSTEM,
        description="Create and modify files in the repository",
        is_dangerous=False,
        required_for=["Code generation", "File editing"]
    ),
    Permission.FILE_DELETE: PermissionMetadata(
        permission=Permission.FILE_DELETE,
        category=PermissionCategory.FILE_SYSTEM,
        description="Delete files from the repository",
        is_dangerous=True,
        warning_message="⚠️ Allows permanent file deletion. Use with caution!",
        required_for=["File cleanup", "Refactoring"]
    ),
    Permission.FILE_EXECUTE: PermissionMetadata(
        permission=Permission.FILE_EXECUTE,
        category=PermissionCategory.FILE_SYSTEM,
        description="Execute script files directly",
        is_dangerous=True,
        warning_message="⚠️ Can execute arbitrary scripts. Security risk!",
        required_for=["Script execution", "Automation"]
    ),
    
    # Terminal (Issue #64)
    Permission.TERMINAL_READ: PermissionMetadata(
        permission=Permission.TERMINAL_READ,
        category=PermissionCategory.TERMINAL,
        description="View terminal command output and results",
        is_dangerous=False,
        required_for=["Command monitoring", "Log viewing"]
    ),
    Permission.TERMINAL_EXECUTE: PermissionMetadata(
        permission=Permission.TERMINAL_EXECUTE,
        category=PermissionCategory.TERMINAL,
        description="Execute shell commands in repository directory",
        is_dangerous=True,
        warning_message="🚨 CRITICAL: Enables shell command execution. Allows running tests, builds, and system commands. Use safety guardrails!",
        required_for=["pytest", "npm test", "make", "cargo test"]
    ),
    Permission.TERMINAL_INSTALL: PermissionMetadata(
        permission=Permission.TERMINAL_INSTALL,
        category=PermissionCategory.TERMINAL,
        description="Install packages via apt, pip, npm, etc.",
        is_dangerous=True,
        warning_message="⚠️ Can modify system packages. May require sudo. Use with extreme caution!",
        required_for=["pip install", "npm install", "apt install"]
    ),
    Permission.TERMINAL_BACKGROUND: PermissionMetadata(
        permission=Permission.TERMINAL_BACKGROUND,
        category=PermissionCategory.TERMINAL,
        description="Start long-running background processes",
        is_dangerous=True,
        warning_message="⚠️ Processes continue running after command ends. Monitor resource usage!",
        required_for=["Development servers", "Background tasks"]
    ),
    Permission.TERMINAL_KILL: PermissionMetadata(
        permission=Permission.TERMINAL_KILL,
        category=PermissionCategory.TERMINAL,
        description="Terminate running processes",
        is_dangerous=True,
        warning_message="⚠️ Can kill important processes. Use carefully!",
        required_for=["Process cleanup", "Resource management"]
    ),
    
    # GitHub
    Permission.GITHUB_READ: PermissionMetadata(
        permission=Permission.GITHUB_READ,
        category=PermissionCategory.GITHUB,
        description="Read repository contents, issues, and PRs",
        is_dangerous=False,
        required_for=["Code review", "Issue monitoring"]
    ),
    Permission.GITHUB_CREATE_ISSUE: PermissionMetadata(
        permission=Permission.GITHUB_CREATE_ISSUE,
        category=PermissionCategory.GITHUB,
        description="Create new GitHub issues",
        is_dangerous=False,
        required_for=["Issue creation", "Bug reporting"]
    ),
    Permission.GITHUB_CREATE_PR: PermissionMetadata(
        permission=Permission.GITHUB_CREATE_PR,
        category=PermissionCategory.GITHUB,
        description="Create pull requests",
        is_dangerous=False,
        required_for=["Code submission", "Feature PRs"]
    ),
    Permission.GITHUB_MERGE_PR: PermissionMetadata(
        permission=Permission.GITHUB_MERGE_PR,
        category=PermissionCategory.GITHUB,
        description="Merge pull requests to main branch",
        is_dangerous=True,
        warning_message="🚨 CRITICAL: Can merge code to production. Use strict review process!",
        required_for=["Auto-merge", "PR automation"]
    ),
    Permission.GITHUB_CLOSE_ISSUE: PermissionMetadata(
        permission=Permission.GITHUB_CLOSE_ISSUE,
        category=PermissionCategory.GITHUB,
        description="Close and resolve issues",
        is_dangerous=False,
        required_for=["Issue management", "Cleanup"]
    ),
    Permission.GITHUB_ASSIGN: PermissionMetadata(
        permission=Permission.GITHUB_ASSIGN,
        category=PermissionCategory.GITHUB,
        description="Assign issues and PRs to users",
        is_dangerous=False,
        required_for=["Task assignment", "Coordination"]
    ),
    
    # API
    Permission.API_EXTERNAL: PermissionMetadata(
        permission=Permission.API_EXTERNAL,
        category=PermissionCategory.API,
        description="Make HTTP requests to external APIs",
        is_dangerous=True,
        warning_message="⚠️ Can call external services. Monitor API usage and costs!",
        required_for=["External integrations", "API calls"]
    ),
    Permission.API_LLM: PermissionMetadata(
        permission=Permission.API_LLM,
        category=PermissionCategory.API,
        description="Access LLM provider APIs (OpenAI, Anthropic, etc.)",
        is_dangerous=False,
        required_for=["Code generation", "AI assistance"]
    ),
    Permission.API_WEBHOOK: PermissionMetadata(
        permission=Permission.API_WEBHOOK,
        category=PermissionCategory.API,
        description="Send and receive webhook notifications",
        is_dangerous=False,
        required_for=["Event notifications", "Integrations"]
    ),
    
    # System
    Permission.SYSTEM_CONFIG: PermissionMetadata(
        permission=Permission.SYSTEM_CONFIG,
        category=PermissionCategory.SYSTEM,
        description="Modify agent-forge configuration",
        is_dangerous=True,
        warning_message="⚠️ Can change system behavior. Verify changes carefully!",
        required_for=["Configuration management"]
    ),
    Permission.SYSTEM_LOGS: PermissionMetadata(
        permission=Permission.SYSTEM_LOGS,
        category=PermissionCategory.SYSTEM,
        description="View system logs and audit trails",
        is_dangerous=False,
        required_for=["Debugging", "Monitoring"]
    ),
    Permission.SYSTEM_RESTART: PermissionMetadata(
        permission=Permission.SYSTEM_RESTART,
        category=PermissionCategory.SYSTEM,
        description="Restart agent-forge services",
        is_dangerous=True,
        warning_message="🚨 CRITICAL: Causes service downtime. Use only when necessary!",
        required_for=["Service management", "Updates"]
    ),
}


class PermissionPreset(Enum):
    """Pre-defined permission sets for common roles and agent types"""
    # Generic presets
    READ_ONLY = "read_only"
    DEVELOPER = "developer"
    ADMIN = "admin"
    CUSTOM = "custom"
    
    # Agent role presets (match AgentRole enum in coordinator_agent.py)
    COORDINATOR = "coordinator"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    BOT = "bot"
    RESEARCHER = "researcher"


# Permission preset definitions
PERMISSION_PRESETS: Dict[PermissionPreset, Set[Permission]] = {
    # Generic presets
    PermissionPreset.READ_ONLY: {
        Permission.FILE_READ,
        Permission.TERMINAL_READ,
        Permission.GITHUB_READ,
        Permission.SYSTEM_LOGS,
    },
    
    PermissionPreset.DEVELOPER: {
        # File System
        Permission.FILE_READ,
        Permission.FILE_WRITE,
        Permission.FILE_DELETE,  # Needed for refactoring
        
        # Terminal (Issue #64 - Enable testing)
        Permission.TERMINAL_READ,
        Permission.TERMINAL_EXECUTE,  # CRITICAL: Enable shell access for testing
        Permission.TERMINAL_INSTALL,  # Allow installing test dependencies
        
        # GitHub
        Permission.GITHUB_READ,
        Permission.GITHUB_CREATE_ISSUE,
        Permission.GITHUB_CREATE_PR,
        Permission.GITHUB_CLOSE_ISSUE,
        
        # API
        Permission.API_LLM,
        Permission.API_WEBHOOK,
        
        # System
        Permission.SYSTEM_LOGS,
    },
    
    PermissionPreset.ADMIN: set(Permission),  # All permissions
    
    # Agent role-specific presets
    PermissionPreset.COORDINATOR: {
        # File System - Read only (no code changes)
        Permission.FILE_READ,
        
        # Terminal - Read only
        Permission.TERMINAL_READ,
        
        # GitHub - Full coordination access
        Permission.GITHUB_READ,
        Permission.GITHUB_CREATE_ISSUE,
        Permission.GITHUB_ASSIGN,
        Permission.GITHUB_CLOSE_ISSUE,
        
        # API
        Permission.API_LLM,
        Permission.API_WEBHOOK,
        
        # System
        Permission.SYSTEM_LOGS,
        Permission.SYSTEM_CONFIG,  # Coordinators can modify config
    },
    
    PermissionPreset.REVIEWER: {
        # File System - Read only
        Permission.FILE_READ,
        
        # Terminal - Read only
        Permission.TERMINAL_READ,
        
        # GitHub - Review permissions
        Permission.GITHUB_READ,
        Permission.GITHUB_CREATE_ISSUE,  # Can create issues for problems found
        Permission.GITHUB_CREATE_PR,  # Can create PRs with review feedback
        
        # API
        Permission.API_LLM,
        
        # System
        Permission.SYSTEM_LOGS,
    },
    
    PermissionPreset.TESTER: {
        # File System - Write for test files only (checked by validator)
        Permission.FILE_READ,
        Permission.FILE_WRITE,
        
        # Terminal - Full testing access
        Permission.TERMINAL_READ,
        Permission.TERMINAL_EXECUTE,  # Run tests
        Permission.TERMINAL_INSTALL,  # Install test dependencies
        
        # GitHub
        Permission.GITHUB_READ,
        Permission.GITHUB_CREATE_ISSUE,  # Report test failures
        
        # API
        Permission.API_LLM,
        
        # System
        Permission.SYSTEM_LOGS,
    },
    
    PermissionPreset.DOCUMENTER: {
        # File System - Write for docs only (checked by validator)
        Permission.FILE_READ,
        Permission.FILE_WRITE,
        
        # Terminal - Read only
        Permission.TERMINAL_READ,
        
        # GitHub
        Permission.GITHUB_READ,
        Permission.GITHUB_CREATE_ISSUE,
        Permission.GITHUB_CREATE_PR,  # Can create PRs with doc updates
        
        # API
        Permission.API_LLM,
        
        # System
        Permission.SYSTEM_LOGS,
    },
    
    PermissionPreset.BOT: {
        # File System - READ ONLY (bots cannot modify code)
        Permission.FILE_READ,
        
        # Terminal - READ ONLY (no shell access for bots)
        Permission.TERMINAL_READ,
        
        # GitHub - Automation permissions
        Permission.GITHUB_READ,
        Permission.GITHUB_CREATE_ISSUE,
        Permission.GITHUB_ASSIGN,
        Permission.GITHUB_CLOSE_ISSUE,
        # NOTE: NO MERGE_PR - bots should not merge PRs automatically
        
        # API
        Permission.API_WEBHOOK,  # For notifications
        
        # System
        Permission.SYSTEM_LOGS,
    },
    
    PermissionPreset.RESEARCHER: {
        # File System - Read only
        Permission.FILE_READ,
        
        # Terminal - Read only
        Permission.TERMINAL_READ,
        
        # GitHub
        Permission.GITHUB_READ,
        Permission.GITHUB_CREATE_ISSUE,  # Can create issues with research findings
        
        # API - Full external access for research
        Permission.API_EXTERNAL,
        Permission.API_LLM,
        Permission.API_WEBHOOK,
        
        # System
        Permission.SYSTEM_LOGS,
    },
}


def get_preset_for_role(role: str) -> PermissionPreset:
    """
    Map agent role to permission preset.
    
    Args:
        role: Agent role (coordinator, developer, reviewer, tester, documenter, bot, researcher)
    
    Returns:
        Corresponding PermissionPreset
    
    Example:
        >>> get_preset_for_role("bot")
        PermissionPreset.BOT
        >>> get_preset_for_role("developer")
        PermissionPreset.DEVELOPER
    """
    role_lower = role.lower()
    
    # Direct mapping for agent roles
    role_to_preset = {
        "coordinator": PermissionPreset.COORDINATOR,
        "developer": PermissionPreset.DEVELOPER,
        "reviewer": PermissionPreset.REVIEWER,
        "tester": PermissionPreset.TESTER,
        "documenter": PermissionPreset.DOCUMENTER,
        "bot": PermissionPreset.BOT,
        "researcher": PermissionPreset.RESEARCHER,
    }
    
    preset = role_to_preset.get(role_lower, PermissionPreset.DEVELOPER)
    
    if role_lower not in role_to_preset:
        logger.warning(f"⚠️ Unknown agent role '{role}', defaulting to DEVELOPER preset")
    
    return preset


@dataclass
class AgentPermissions:
    """Agent permission configuration"""
    agent_id: str
    preset: PermissionPreset = PermissionPreset.DEVELOPER
    custom_permissions: Set[Permission] = field(default_factory=set)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if agent has specific permission"""
        if self.preset == PermissionPreset.CUSTOM:
            return permission in self.custom_permissions
        else:
            return permission in PERMISSION_PRESETS[self.preset]
    
    def get_permissions(self) -> Set[Permission]:
        """Get all active permissions"""
        if self.preset == PermissionPreset.CUSTOM:
            return self.custom_permissions.copy()
        else:
            return PERMISSION_PRESETS[self.preset].copy()
    
    def set_preset(self, preset: PermissionPreset):
        """Change to a different preset"""
        self.preset = preset
        if preset != PermissionPreset.CUSTOM:
            self.custom_permissions = PERMISSION_PRESETS[preset].copy()
        logger.info(f"🔐 Agent {self.agent_id} permissions set to preset: {preset.value}")
    
    def grant_permission(self, permission: Permission):
        """Grant a single permission (switches to CUSTOM preset)"""
        self.preset = PermissionPreset.CUSTOM
        self.custom_permissions.add(permission)
        
        metadata = PERMISSION_METADATA[permission]
        if metadata.is_dangerous:
            logger.warning(
                f"⚠️ Granted dangerous permission '{permission.value}' to agent {self.agent_id}: "
                f"{metadata.warning_message}"
            )
        else:
            logger.info(f"✅ Granted permission '{permission.value}' to agent {self.agent_id}")
    
    def revoke_permission(self, permission: Permission):
        """Revoke a single permission (switches to CUSTOM preset)"""
        self.preset = PermissionPreset.CUSTOM
        self.custom_permissions.discard(permission)
        logger.info(f"❌ Revoked permission '{permission.value}' from agent {self.agent_id}")
    
    def get_dangerous_permissions(self) -> Set[Permission]:
        """Get list of dangerous permissions agent has"""
        active = self.get_permissions()
        return {
            perm for perm in active
            if PERMISSION_METADATA[perm].is_dangerous
        }
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            'agent_id': self.agent_id,
            'preset': self.preset.value,
            'permissions': [p.value for p in self.get_permissions()],
            'dangerous_permissions': [p.value for p in self.get_dangerous_permissions()],
        }


class PermissionValidator:
    """Validates operations against agent permissions"""
    
    @staticmethod
    def require_permission(permissions: AgentPermissions, required: Permission, operation: str):
        """
        Check if agent has required permission for operation.
        Raises PermissionError if not authorized.
        """
        if not permissions.has_permission(required):
            raise PermissionError(
                f"🚫 Agent {permissions.agent_id} does not have permission '{required.value}' "
                f"required for operation: {operation}"
            )
        
        metadata = PERMISSION_METADATA[required]
        if metadata.is_dangerous:
            logger.warning(
                f"⚠️ Agent {permissions.agent_id} executing dangerous operation: {operation} "
                f"(requires {required.value})"
            )
    
    @staticmethod
    def check_shell_command(permissions: AgentPermissions, command: str) -> bool:
        """
        Check if agent can execute shell command.
        Returns True if authorized, False otherwise.
        """
        if not permissions.has_permission(Permission.TERMINAL_EXECUTE):
            logger.error(
                f"🚫 Agent {permissions.agent_id} attempted shell execution without permission: {command}"
            )
            return False
        
        # Check for install commands
        install_keywords = ['pip install', 'npm install', 'apt install', 'apt-get install', 'cargo install']
        if any(keyword in command.lower() for keyword in install_keywords):
            if not permissions.has_permission(Permission.TERMINAL_INSTALL):
                logger.error(
                    f"🚫 Agent {permissions.agent_id} attempted package install without permission: {command}"
                )
                return False
        
        logger.info(f"✅ Shell command authorized for agent {permissions.agent_id}: {command[:100]}")
        return True


def get_permissions_by_category() -> Dict[PermissionCategory, List[PermissionMetadata]]:
    """Group permissions by category for UI display"""
    categorized: Dict[PermissionCategory, List[PermissionMetadata]] = {}
    
    for metadata in PERMISSION_METADATA.values():
        if metadata.category not in categorized:
            categorized[metadata.category] = []
        categorized[metadata.category].append(metadata)
    
    return categorized


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create agent with developer preset
    perms = AgentPermissions(agent_id="test-agent", preset=PermissionPreset.DEVELOPER)
    
    print("\n🔐 Developer Preset Permissions:")
    for perm in perms.get_permissions():
        metadata = PERMISSION_METADATA[perm]
        danger_mark = " ⚠️" if metadata.is_dangerous else ""
        print(f"  ✅ {perm.value}{danger_mark}")
    
    print("\n🚨 Dangerous Permissions:")
    for perm in perms.get_dangerous_permissions():
        metadata = PERMISSION_METADATA[perm]
        print(f"  ⚠️ {perm.value}: {metadata.warning_message}")
    
    # Test shell command validation
    print("\n🧪 Testing Shell Command Validation:")
    print(f"  pytest: {PermissionValidator.check_shell_command(perms, 'pytest tests/')}")
    print(f"  pip install: {PermissionValidator.check_shell_command(perms, 'pip install requests')}")
    
    # Test permission requirement
    try:
        PermissionValidator.require_permission(perms, Permission.GITHUB_MERGE_PR, "merge PR #123")
    except PermissionError as e:
        print(f"\n❌ Expected permission error: {e}")
