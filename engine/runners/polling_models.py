"""Configuration dataclasses for polling service.

Defines PollingConfig and IssueState structures used throughout
the polling service for configuration and state tracking.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PollingConfig:
    """Configuration for the polling service."""
    
    interval_seconds: int = 300  # 5 minutes
    github_token: Optional[str] = None
    github_username: Optional[str] = None  # Must be configured via YAML or environment
    repositories: List[str] = field(default_factory=list)  # ["owner/repo", ...]
    watch_labels: List[str] = field(default_factory=lambda: ["agent-ready", "auto-assign"])  # labels
    max_concurrent_issues: int = 3
    claim_timeout_minutes: int = 60
    state_file: str = "data/polling_state.json"  # Sensible default path
    
    # PR Monitoring (NEW)
    pr_monitoring_enabled: bool = False
    pr_monitoring_interval: int = 600  # 10 minutes
    pr_auto_review_users: List[str] = field(default_factory=list)
    pr_skip_review_users: List[str] = field(default_factory=list)
    pr_review_labels: List[str] = field(default_factory=list)
    pr_review_strategy: Optional[str] = None  # Must be configured: dedicated, round-robin, all
    reviewer_agent_id: Optional[str] = None  # Must be configured via YAML
    reviewer_agents: List[Dict[str, str]] = field(default_factory=list)  # [{"agent_id": "...", "username": "...", "llm_model": "..."}]
    
    # PR Review Configuration (NEW)
    pr_use_llm: bool = True
    pr_llm_model: Optional[str] = None  # Must be configured via YAML (e.g., "qwen2.5-coder:7b")
    pr_bot_account: Optional[str] = None  # Must be configured via YAML (e.g., "admin")
    pr_full_workflow: bool = True
    pr_post_comments: bool = True
    
    # PR Merge Configuration (NEW)
    pr_merge_enabled: bool = True
    pr_auto_merge_if_approved: bool = True
    pr_merge_with_suggestions: bool = False
    pr_merge_method: Optional[str] = None  # Must be configured: merge, squash, or rebase
    pr_merge_delay_seconds: int = 30
    
    # Issue Opener Integration (NEW)
    issue_opener_enabled: bool = False
    issue_opener_trigger_labels: List[str] = field(default_factory=list)
    issue_opener_skip_labels: List[str] = field(default_factory=list)
    issue_opener_agent_id: Optional[str] = None  # Must be configured via YAML
    
    def __post_init__(self):
        """Initialize default values."""
        if self.github_token is None:
            self.github_token = os.getenv("BOT_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")


@dataclass
class IssueState:
    """State tracking for a single issue."""
    
    issue_number: int
    repository: str
    claimed_by: Optional[str]
    claimed_at: Optional[str]
    last_error: Optional[str] = None
    error_count: int = 0
    completed: bool = False
    completed_at: Optional[str] = None
