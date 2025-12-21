"""Autonomous polling service for GitHub issue monitoring and automatic workflow initiation.

This module implements periodic polling to check for assigned GitHub issues and automatically
starts the IssueHandler workflow when new actionable issues are detected.

Features:
- Configurable polling intervals (default: 5 minutes)
- Multi-repository support
- Label-based filtering (agent-ready, auto-assign)
- Issue locking to prevent duplicate work by multiple agents
- State persistence across restarts
- Graceful error handling with retry logic
- Structured logging for all events
- Single instance enforcement via PID lock file
"""

import asyncio
import json
import logging
import os
import sys
import time
import subprocess
import fcntl
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

# Import refactored modules
from engine.runners.polling_models import PollingConfig, IssueState
from engine.runners.config_override_handler import ConfigOverrideHandler
from engine.runners.state_manager import StateManager
from engine.runners.issue_filter import IssueFilter
from engine.utils.environment_config import EnvironmentConfig


# PID lock file for single instance enforcement
# Use data directory (accessible with ReadWritePaths)
LOCK_FILE = "/home/flip/agent-forge/data/polling_service.lock"


def ensure_single_instance():
    """Ensure only one instance of polling service runs at a time.
    
    Uses a lock file with exclusive lock (fcntl.LOCK_EX) to prevent
    multiple instances. If lock fails, checks if existing process is
    alive and exits if so.
    
    Returns:
        File descriptor of lock file (keep open to maintain lock)
    """
    try:
        # Open lock file (create if doesn't exist, read-write mode)
        lock_fd = open(LOCK_FILE, 'a+')
        
        # Try to acquire exclusive lock (non-blocking)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Successfully acquired lock - write our PID
            lock_fd.seek(0)
            lock_fd.truncate()
            lock_fd.write(str(os.getpid()))
            lock_fd.flush()
            return lock_fd
        except IOError:
            # Lock failed - another instance is running
            lock_fd.seek(0)
            existing_pid = lock_fd.read().strip()
            
            # Check if process is actually running
            if existing_pid:
                try:
                    # Send signal 0 to check if process exists
                    os.kill(int(existing_pid), 0)
                    print(f"❌ ERROR: Polling service already running (PID: {existing_pid})")
                    print(f"   Lock file: {LOCK_FILE}")
                    print(f"   To force restart: sudo systemctl restart agent-forge-polling")
                    sys.exit(1)
                except (OSError, ValueError):
                    # Process doesn't exist - stale lock
                    print(f"⚠️  Stale lock file found (PID {existing_pid} not running)")
                    print(f"   Removing stale lock and continuing...")
                    lock_fd.close()
                    os.remove(LOCK_FILE)
                    # Retry lock acquisition
                    return ensure_single_instance()
            
            lock_fd.close()
            print(f"❌ ERROR: Could not acquire lock on {LOCK_FILE}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ ERROR: Failed to create lock file: {e}")
        sys.exit(1)


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    """Return ISO-8601 string for current UTC time (Zulu suffix)."""
    return _utc_now().isoformat().replace("+00:00", "Z")


def _parse_iso_timestamp(value: str) -> datetime:
    """Parse ISO timestamp supporting legacy naive and Zulu formats."""
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed

# Optional psutil import for metrics; gracefully handle absence
try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # type: ignore

from engine.operations.github_api_helper import GitHubAPIHelper
from engine.operations.creative_status import generate_issue_motif

logger = logging.getLogger(__name__)


class MonitorLogHandler(logging.Handler):
    """Custom log handler that forwards logs to monitor service."""
    
    def __init__(self, monitor, agent_id: str):
        super().__init__()
        self.monitor = monitor
        self.agent_id = agent_id
    
    def emit(self, record):
        """Forward log record to monitor service."""
        try:
            # Format the message
            message = self.format(record)
            
            # Map logging levels to monitor levels
            level_map = {
                logging.DEBUG: "DEBUG",
                logging.INFO: "INFO",
                logging.WARNING: "WARNING",
                logging.ERROR: "ERROR",
                logging.CRITICAL: "CRITICAL"
            }
            level = level_map.get(record.levelno, "INFO")
            
            # Send to monitor with current timestamp
            self.monitor.add_log(
                agent_id=self.agent_id,
                level=level,
                message=message
            )
        except Exception:
            # Don't let logging errors crash the application
            pass


class PollingService:
    """Service for autonomous GitHub issue polling and workflow initiation."""
    
    def __init__(self, config: Optional[PollingConfig] = None, agent_registry=None, enable_monitoring: bool = True, config_path: Optional[Path] = None):
        """Initialize polling service.
        
        Args:
            config: Polling configuration (overrides YAML if provided)
            agent_registry: AgentRegistry instance for getting agent instances
            enable_monitoring: Whether to register with monitor service
            config_path: Optional explicit path to YAML config file
        """
        # Load environment configuration first
        self.env_config = EnvironmentConfig()
        logger.info(f"🌍 Environment: {self.env_config.active_env}")
        
        # Configuration resolution strategy:
        # - If explicit config provided without config_path: use it directly (do not load YAML)
        # - If config is None: load from YAML (config_path or default)
        # - If both provided: load YAML first, then apply explicit overrides
        if config is not None and config_path is None:
            self.config = config
        else:
            self.config = self._load_config_from_yaml(config_path)
            if config is not None:
                self._apply_config_overrides(config)
        
        # Apply environment-specific overrides
        self._apply_environment_overrides()
        
        self.agent_registry = agent_registry
        self.state_file = Path(self.config.state_file)
        
        # Initialize StateManager for state persistence
        self.state_manager = StateManager(self.state_file)
        self.state_manager.load()
        
        # Keep backwards compatibility with self.state
        self.state = self.state_manager.state
        
        # Initialize IssueFilter for issue filtering logic
        self.issue_filter = IssueFilter(
            state_manager=self.state_manager,
            watch_labels=self.config.watch_labels,
            claim_timeout_minutes=self.config.claim_timeout_minutes,
            creative_logs_enabled=os.getenv("POLLING_CREATIVE_LOGS", "0") in {"1", "true", "TRUE"},
            github_claim_checker=self.is_issue_claimed  # NEW: Pass GitHub claim checker
        )
        
        self.running = False
        self.enable_monitoring = enable_monitoring
        self.monitor = None
        self.api_calls = 0  # Track API calls
        
        # Track reviewed PRs with timestamp and commit SHA to prevent memory leak
        # {pr_key: {'sha': head_sha, 'reviewed_at': timestamp}}
        self.reviewed_prs: Dict[str, Dict] = {}
        self.reviewed_prs_max_size = 1000  # Maximum entries before cleanup
        self.reviewed_prs_max_age_days = 7  # Remove entries older than 7 days
        
        # Initialize GitHub API helper
        self.github_api = GitHubAPIHelper(token=self.config.github_token)
        
        # Register with monitor if enabled
        if enable_monitoring:
            # Initialize process metrics if psutil is available
            self.process = None
            if psutil is not None:
                try:
                    self.process = psutil.Process()
                except Exception as e:
                    logger.warning(f"psutil present but could not get process: {e}")
            else:
                logger.warning("psutil not installed, metrics will not be available")
            
            try:
                from engine.runners.monitor_service import get_monitor, AgentStatus
                self.monitor = get_monitor()
                
                # Polling service is a SERVICE, not an agent - do not register as agent
                # Services register via service_manager, agents register via their own init
                
                # Add custom logging handler to forward all logs to monitor
                monitor_handler = MonitorLogHandler(self.monitor, "polling-service")
                monitor_handler.setFormatter(logging.Formatter('%(message)s'))
                logger.addHandler(monitor_handler)
                logger.setLevel(logging.INFO)  # Ensure INFO level is captured
                
                logger.info("✅ Registered with monitoring service")
            except Exception as e:
                logger.warning(f"Could not register with monitor: {e}")
                self.monitor = None

        # Log effective configuration (sanitize token)
        try:
            safe_cfg = asdict(self.config)
            if safe_cfg.get('github_token'):
                safe_cfg['github_token'] = '***'
            logger.info(f"🔧 Polling config loaded: {safe_cfg}")
        except Exception:
            pass

    def _load_config_from_yaml(self, config_path: Optional[Path]) -> PollingConfig:
        """Load polling configuration from YAML file with sensible defaults.

        Priority: explicit path -> default path config/services/polling.yaml -> defaults.
        """
        # Default values
        cfg = PollingConfig()
        # Determine path
        if not config_path:
            default_path = Path('config/services/polling.yaml')
            config_path = default_path if default_path.exists() else None
        if not config_path or not Path(config_path).exists():
            logger.warning("⚠️ polling.yaml not found; using defaults and environment variables")
            return cfg
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"❌ Failed to read YAML config: {e}; falling back to defaults")
            return cfg

        # Map YAML fields
        try:
            cfg.interval_seconds = int(data.get('interval_seconds', cfg.interval_seconds))
            # GitHub section
            gh = data.get('github', {}) or {}
            username = gh.get('username')
            if isinstance(username, str) and username.strip():
                cfg.github_username = username.strip()
            token = gh.get('token')
            if isinstance(token, str) and token.strip():
                cfg.github_token = token.strip()
            
            # Repositories & labels
            repos = data.get('repositories') or []
            if isinstance(repos, list):
                # Support both old format (strings) and new format (dicts with enabled flag)
                enabled_repos = []
                for r in repos:
                    if isinstance(r, str):
                        # Old format: simple string
                        enabled_repos.append(r)
                    elif isinstance(r, dict):
                        # New format: dict with 'repo' and 'enabled' keys
                        repo_name = r.get('repo')
                        is_enabled = r.get('enabled', True)
                        if repo_name and is_enabled:
                            enabled_repos.append(str(repo_name))
                            logger.info(f"✅ Repository enabled: {repo_name}")
                        elif repo_name:
                            logger.info(f"🚫 Repository disabled: {repo_name}")
                cfg.repositories = enabled_repos
            
            labels = data.get('watch_labels') or []
            if isinstance(labels, list) and labels:
                cfg.watch_labels = [str(l) for l in labels]
            # Concurrency & state
            cfg.max_concurrent_issues = int(data.get('max_concurrent_issues', cfg.max_concurrent_issues))
            cfg.claim_timeout_minutes = int(data.get('claim_timeout_minutes', cfg.claim_timeout_minutes))
            state_file = data.get('state_file')
            if isinstance(state_file, str) and state_file.strip():
                state_file = state_file.strip()
                # Convert relative path to absolute (relative to project root data/)
                if not state_file.startswith('/'):
                    # Get project root (3 levels up from this file)
                    project_root = Path(__file__).resolve().parent.parent.parent
                    state_file = str(project_root / "data" / state_file)
                cfg.state_file = state_file
            
            # PR Monitoring (NEW)
            pr_mon = data.get('pr_monitoring', {}) or {}
            cfg.pr_monitoring_enabled = bool(pr_mon.get('enabled', False))
            cfg.pr_monitoring_interval = int(pr_mon.get('interval_seconds', 600))
            
            auto_review_users = pr_mon.get('auto_review_users', [])
            if isinstance(auto_review_users, list):
                cfg.pr_auto_review_users = [str(u) for u in auto_review_users]
            
            skip_review_users = pr_mon.get('skip_review_users', [])
            if isinstance(skip_review_users, list):
                cfg.pr_skip_review_users = [str(u) for u in skip_review_users]
            
            review_labels = pr_mon.get('review_labels', [])
            if isinstance(review_labels, list):
                cfg.pr_review_labels = [str(l) for l in review_labels]
            
            strategy = pr_mon.get('strategy')
            if isinstance(strategy, str) and strategy.strip():
                cfg.pr_review_strategy = strategy.strip()
            
            # PR Review Configuration (NEW)
            review_config = pr_mon.get('review_config', {}) or {}
            cfg.pr_use_llm = bool(review_config.get('use_llm', True))
            cfg.pr_llm_model = str(review_config.get('llm_model', 'qwen2.5-coder:7b'))
            cfg.pr_bot_account = str(review_config.get('bot_account', 'admin'))
            cfg.pr_full_workflow = bool(review_config.get('full_workflow', True))
            cfg.pr_post_comments = bool(review_config.get('post_comments', True))
            
            # PR Merge Configuration (NEW)
            merge_config = pr_mon.get('merge_config', {}) or {}
            cfg.pr_merge_enabled = bool(merge_config.get('enabled', True))
            cfg.pr_auto_merge_if_approved = bool(merge_config.get('auto_merge_if_approved', True))
            cfg.pr_merge_with_suggestions = bool(merge_config.get('merge_with_suggestions', False))
            cfg.pr_merge_method = str(merge_config.get('merge_method', 'squash'))
            cfg.pr_merge_delay_seconds = int(merge_config.get('merge_delay_seconds', 30))
            
            reviewer_id = pr_mon.get('reviewer_agent_id')
            if isinstance(reviewer_id, str) and reviewer_id.strip():
                cfg.reviewer_agent_id = reviewer_id.strip()
            
            reviewer_agents = pr_mon.get('reviewer_agents', [])
            if isinstance(reviewer_agents, list):
                cfg.reviewer_agents = [
                    {
                        "agent_id": str(a.get('agent_id', '')), 
                        "username": str(a.get('username', '')),
                        "llm_model": str(a.get('llm_model', 'unknown'))
                    }
                    for a in reviewer_agents
                    if isinstance(a, dict)
                ]
            
            # Issue Opener Integration (NEW)
            issue_opener = data.get('issue_opener', {}) or {}
            cfg.issue_opener_enabled = bool(issue_opener.get('enabled', False))
            
            trigger_labels = issue_opener.get('trigger_labels', [])
            if isinstance(trigger_labels, list):
                cfg.issue_opener_trigger_labels = [str(l) for l in trigger_labels]
            
            skip_labels = issue_opener.get('skip_labels', [])
            if isinstance(skip_labels, list):
                cfg.issue_opener_skip_labels = [str(l) for l in skip_labels]
            
            opener_id = issue_opener.get('agent_id')
            if isinstance(opener_id, str) and opener_id.strip():
                cfg.issue_opener_agent_id = opener_id.strip()
                
        except Exception as e:
            logger.error(f"❌ Error parsing YAML config values: {e}; continuing with partial defaults")
        return cfg

    def _apply_config_overrides(self, override: PollingConfig):
        """Override YAML-loaded configuration with explicitly provided override values.
        
        Uses ConfigOverrideHandler to apply only non-default overrides.
        """
        handler = ConfigOverrideHandler(self.config)
        handler.apply_overrides(override)
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides."""
        # Override repositories from environment
        env_repos = self.env_config.get_repositories()
        if env_repos:
            logger.info(f"🌍 Environment override: repositories = {env_repos}")
            self.config.repositories = env_repos
        
        # Override max concurrent issues
        env_max = self.env_config.get_max_concurrent_issues()
        if env_max != self.config.max_concurrent_issues:
            logger.info(f"🌍 Environment override: max_concurrent_issues = {env_max}")
            self.config.max_concurrent_issues = env_max
        
        # Override claim timeout
        env_timeout = self.env_config.get_claim_timeout()
        if env_timeout != self.config.claim_timeout_minutes:
            logger.info(f"🌍 Environment override: claim_timeout_minutes = {env_timeout}")
            self.config.claim_timeout_minutes = env_timeout
        
        # Override auto-merge setting
        env_auto_merge = self.env_config.can_auto_merge()
        if env_auto_merge != self.config.pr_auto_merge_if_approved:
            logger.info(f"🌍 Environment override: auto_merge = {env_auto_merge}")
            self.config.pr_auto_merge_if_approved = env_auto_merge
        
        # Log environment info
        if self.env_config.is_dry_run():
            logger.warning("⚠️  DRY RUN MODE - No actual operations will be performed")
        if self.env_config.is_test_mode():
            logger.info("🧪 TEST MODE - Using test repository")
        if self.env_config.is_production():
            logger.info("🚀 PRODUCTION MODE - Using production repositories")
        
    def load_state(self):
        """Load polling state from disk."""
        self.state_manager.load()
        self.state = self.state_manager.state
    
    def save_state(self):
        """Save polling state to disk."""
        self.state_manager.save()
    
    def cleanup_old_state(self):
        """Remove old completed/closed issues from state."""
        self.state_manager.cleanup_old_entries(days=7)
        self.state = self.state_manager.state
    
    def update_metrics(self):
        """Update agent metrics in monitor."""
        if not self.monitor or not self.process or psutil is None:
            return
        
        try:
            # Get CPU and memory usage
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_percent = (memory_info.rss / psutil.virtual_memory().total) * 100
            
            # Update monitor
            self.monitor.update_agent_metrics(
                agent_id="polling-service",
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                api_calls=self.api_calls
            )
        except Exception as e:
            logger.debug(f"Error updating metrics: {e}")
    
    def get_issue_key(self, repo: str, issue_number: int) -> str:
        """Generate unique key for issue.
        
        Args:
            repo: Repository (owner/repo)
            issue_number: Issue number
            
        Returns:
            Unique key string
        """
        return f"{repo}#{issue_number}"
    
    async def check_assigned_issues(self) -> List[Dict]:
        """Query GitHub API for issues with agent-ready labels.
        
        This method searches for ALL open issues with watch labels (agent-ready, auto-assign)
        regardless of assignee. The polling service will then check if they're actionable
        based on claim status and other criteria.
        
        Returns:
            List of issue dictionaries with agent-ready labels
        """
        logger.info("Checking for issues with agent-ready labels...")
        
        all_issues = []
        
        for repo in self.config.repositories:
            try:
                owner, repo_name = repo.split('/')
                
                # Get ALL open issues with watch labels (not filtered by assignee)
                # This allows any agent to pick up unclaimed agent-ready issues
                # 
                # Note: GitHub API uses AND logic for comma-separated labels,
                # so we query each label separately and merge results (OR logic)
                issues = []
                seen_issue_ids = set()
                
                for label in self.config.watch_labels:
                    try:
                        # Query for each label individually
                        path = f"/repos/{owner}/{repo_name}/issues?state=open&per_page=100&labels={label}"
                        stdout = subprocess.run(
                            ["gh", "api", path],
                            text=True,
                            capture_output=True
                        )
                        if stdout.returncode != 0:
                            raise RuntimeError(stdout.stderr.strip() or "gh api failed")
                        label_issues = json.loads(stdout.stdout or "[]")
                    except Exception:
                        # Fallback to REST API helper
                        label_issues = self.github_api.list_issues(
                            owner=owner,
                            repo=repo_name,
                            labels=[label],  # Single label query
                            state="open",
                            per_page=100,
                            bypass_rate_limit=True
                        )
                        # Increment API call counter
                        self.api_calls += 1
                    
                    # Deduplicate: only add issues we haven't seen yet
                    for issue in label_issues:
                        issue_number = issue.get('number')
                        if not issue_number:
                            logger.warning(f"⚠️ Issue missing number field, skipping: {issue.get('title', 'unknown')}")
                            continue
                        if issue_number not in seen_issue_ids:
                            issues.append(issue)
                            seen_issue_ids.add(issue_number)
                
                # Add repository field to each issue
                for issue in issues:
                    issue['repository'] = repo
                all_issues.extend(issues)
                
                logger.info(f"Found {len(issues)} issues with agent-ready labels in {repo}")
                
            except Exception as e:
                logger.error(f"Failed to query issues for {repo}: {e}")
        
        logger.info(f"Total issues with agent-ready labels found: {len(all_issues)}")
        return all_issues
    
    def filter_actionable_issues(self, issues: List[Dict]) -> List[Dict]:
        """Filter issues based on labels and state.
        
        Uses IssueFilter for the filtering logic.
        
        Args:
            issues: List of issue dictionaries
            
        Returns:
            Filtered list of actionable issues
        """
        actionable = self.issue_filter.filter_actionable_issues(issues)
        
        # Sync state back (IssueFilter may have modified it)
        self.state = self.state_manager.state
        
        return actionable
    
        logger.info(f"🐛 DEBUG: filter_actionable_issues returning {len(actionable)} issues")
        return actionable
    
    def is_issue_claimed(self, repo: str, issue_number: int) -> bool:
        """Check if issue is already claimed by another agent.
        
        Args:
            repo: Repository (owner/repo)
            issue_number: Issue number
            
        Returns:
            True if already claimed and claim is still valid
        """
        try:
            owner, repo_name = repo.split('/')
            # Prefer gh CLI for tests; fallback to REST helper
            try:
                path = f"/repos/{owner}/{repo_name}/issues/{issue_number}/comments"
                stdout = subprocess.run(
                    ["gh", "api", path],
                    text=True,
                    capture_output=True
                )
                if stdout.returncode != 0:
                    raise RuntimeError(stdout.stderr.strip() or "gh api failed")
                data = json.loads(stdout.stdout or "[]")
                if isinstance(data, dict) and 'comments' in data:
                    comments = data['comments']
                else:
                    comments = data
            except Exception:
                comments = self.github_api.get_issue_comments(
                    owner=owner,
                    repo=repo_name,
                    issue_number=issue_number
                )
            
            # Check for agent claim comments
            now = _utc_now()
            timeout = timedelta(minutes=self.config.claim_timeout_minutes)
            
            logger.info(f"🐛 DEBUG: Checking {len(comments)} comments for claims (timeout: {self.config.claim_timeout_minutes}min)")
            
            for comment in comments:
                body = comment.get('body', '')
                if '🤖 Agent' in body and 'started working on this issue' in body:
                    # Check timestamp
                    created_str = comment.get('createdAt') or comment.get('created_at')
                    if not created_str:
                        # If missing, treat as not claimed
                        continue
                    created_at = _parse_iso_timestamp(created_str)
                    age_minutes = (now - created_at).total_seconds() / 60
                    logger.info(f"🐛 DEBUG: Found claim comment - age: {age_minutes:.1f} min (timeout: {self.config.claim_timeout_minutes} min)")
                    logger.info(f"🐛 DEBUG: Comment created: {created_at}, Now: {now}")
                    if now - created_at < timeout:
                        logger.info(f"Issue {repo}#{issue_number} claimed by another agent")
                        return True
                    else:
                        logger.info(f"🐛 DEBUG: Claim expired! Age {age_minutes:.1f}min > timeout {self.config.claim_timeout_minutes}min")
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking claim status: {e}")
            return False  # Assume not claimed on error
    
    def _select_reviewers(self, pr_author: str) -> List[Dict[str, str]]:
        """Select reviewer agent(s) for a PR based on configured strategy.
        
        Strategies:
        - dedicated: Always use reviewer_agent_id (single dedicated reviewer)
        - round-robin: Pick one agent from reviewer_agents list (excluding PR author)
        - all: Return all agents from reviewer_agents list (excluding PR author)
        
        Args:
            pr_author: GitHub username of PR author
            
        Returns:
            List of reviewer agent dicts with agent_id, username, llm_model
        """
        strategy = self.config.pr_review_strategy
        
        if strategy == "dedicated":
            # Use dedicated reviewer agent - need to find its config
            for agent in self.config.reviewer_agents:
                if agent.get('agent_id') == self.config.reviewer_agent_id:
                    return [agent]
            # Fallback if not in list
            return [{"agent_id": self.config.reviewer_agent_id, "username": "unknown", "llm_model": "unknown"}]
        
        elif strategy in ["round-robin", "all"]:
            # Filter out PR author from available reviewers
            available = [
                agent
                for agent in self.config.reviewer_agents
                if agent.get('username', '') != pr_author
            ]
            
            if not available:
                logger.warning(f"⚠️ No available reviewers (all agents are PR author or list empty)")
                return []
            
            if strategy == "all":
                # All available agents review
                logger.info(f"🔍 Selected {len(available)} reviewers (all strategy, excluding author {pr_author})")
                return available
            
            else:  # round-robin
                # Pick next reviewer in rotation
                if not hasattr(self, '_reviewer_index'):
                    self._reviewer_index = 0
                
                reviewer = available[self._reviewer_index % len(available)]
                self._reviewer_index = (self._reviewer_index + 1) % len(available)
                
                logger.info(f"🔍 Selected reviewer {reviewer['agent_id']} (model: {reviewer.get('llm_model', 'unknown')}, round-robin, excluding author {pr_author})")
                return [reviewer]
        
        else:
            logger.error(f"❌ Unknown review strategy: {strategy}")
            # Fallback to dedicated
            return [{"agent_id": self.config.reviewer_agent_id, "username": "unknown", "llm_model": "unknown"}]
    
    async def check_pull_requests(self):
        """Check for new PRs needing automatic review.
        
        Monitors open PRs from configured bot accounts and triggers reviewer agent.
        """
        if not self.config.pr_monitoring_enabled:
            logger.debug("🔍 PR monitoring disabled, skipping")
            return
        
        logger.info("🔍 Checking for PRs needing review...")
        
        for repo in self.config.repositories:
            try:
                owner, repo_name = repo.split('/')
                
                # Fetch open PRs (bypass rate limit for internal polling)
                logger.debug(f"🔍 Fetching open PRs for {repo}")
                prs = self.github_api.list_pull_requests(
                    owner=owner,
                    repo=repo_name,
                    state='open',
                    bypass_rate_limit=True
                )
                
                if not prs:
                    logger.debug(f"🔍 No open PRs in {repo}")
                    continue
                
                logger.info(f"🔍 Found {len(prs)} open PR(s) in {repo}")
                
                # Filter PRs for auto-review
                for pr in prs:
                    pr_number = pr.get('number')
                    if not pr_number:
                        logger.warning(f"⚠️ PR missing number field, skipping")
                        continue
                    
                    pr_title = pr.get('title', 'Untitled')
                    pr_user = pr.get('user', {}).get('login', '')
                    pr_labels = [label.get('name', '') for label in pr.get('labels', [])]
                    is_draft = pr.get('draft', False)
                    
                    logger.debug(f"🔍 Checking PR #{pr_number} by {pr_user}: {pr_title} (draft: {is_draft})")
                    
                    # Smart draft handling:
                    # - Skip draft PRs UNLESS they have 'critical-issues' or 'has-conflicts' labels
                    # - These labels indicate the PR was auto-converted by our system
                    # - We want to auto-review them when new commits are pushed (fixes)
                    if is_draft:
                        has_auto_converted_label = any(
                            label in ['critical-issues', 'has-conflicts'] 
                            for label in pr_labels
                        )
                        if not has_auto_converted_label:
                            logger.debug(f"📝 Skipping draft PR #{pr_number} - work in progress (no auto-converted labels)")
                            continue
                        else:
                            logger.info(f"🔄 Draft PR #{pr_number} has auto-converted labels - will re-review on commits")
                    
                    # Check if user is in skip list (admin accounts)
                    if pr_user in self.config.pr_skip_review_users:
                        logger.debug(f"⏭️ Skipping PR #{pr_number} - user {pr_user} in skip list")
                        continue
                    
                    # Check if user is in auto-review list (bot accounts)
                    if self.config.pr_auto_review_users and pr_user not in self.config.pr_auto_review_users:
                        logger.debug(f"⏭️ Skipping PR #{pr_number} - user {pr_user} not in auto-review list")
                        continue
                    
                    # Check if PR has required labels (if configured)
                    if self.config.pr_review_labels:
                        has_required_label = any(label in self.config.pr_review_labels for label in pr_labels)
                        if not has_required_label:
                            logger.debug(f"⏭️ Skipping PR #{pr_number} - missing required labels")
                            continue
                    
                    # Check if already reviewed (with commit SHA tracking for re-reviews)
                    pr_key = f"{repo}#{pr_number}"
                    head_sha = pr.get('head', {}).get('sha', '')
                    
                    # For draft PRs with auto-converted labels, check if HEAD commit changed
                    if is_draft and any(label in ['critical-issues', 'has-conflicts'] for label in pr_labels):
                        # Check if we've reviewed this specific commit
                        reviewed_entry = self.reviewed_prs.get(pr_key, {})
                        reviewed_sha = reviewed_entry.get('sha') if isinstance(reviewed_entry, dict) else reviewed_entry
                        if reviewed_sha == head_sha:
                            logger.debug(f"✅ Already reviewed PR #{pr_number} at commit {head_sha[:7]}")
                            continue
                        elif reviewed_sha:
                            logger.info(f"🔄 Re-reviewing PR #{pr_number} - new commits since last review")
                    else:
                        # For normal PRs, review only once
                        if pr_key in self.reviewed_prs:
                            logger.debug(f"✅ Already reviewed PR #{pr_number}")
                            continue
                    
                    # Trigger reviewer agent
                    logger.info(f"🤖 Triggering review for PR #{pr_number}: {pr_title}")
                    await self.trigger_pr_review(repo, pr_number, pr)
                    
            except Exception as e:
                logger.error(f"❌ Error checking PRs for {repo}: {e}", exc_info=True)
    
    async def check_new_issues_for_opener(self):
        """Check for new issues that should trigger Issue Opener Agent.
        
        Monitors new issues with trigger labels and dispatches to Issue Opener.
        """
        logger.info(f"🐛 DEBUG: issue_opener_enabled = {self.config.issue_opener_enabled}")
        if not self.config.issue_opener_enabled:
            logger.info("🔍 Issue Opener monitoring disabled, skipping")
            return
        
        logger.info("🔍 Checking for issues to auto-open...")
        
        for repo in self.config.repositories:
            try:
                owner, repo_name = repo.split('/')
                
                # Fetch open issues
                logger.debug(f"🔍 Fetching open issues for {repo}")
                issues = self.github_api.list_issues(
                    owner=owner,
                    repo=repo_name,
                    state='open',
                    bypass_rate_limit=True  # Internal polling operation
                )
                
                if not issues:
                    logger.debug(f"🔍 No open issues in {repo}")
                    continue
                
                logger.info(f"🔍 Found {len(issues)} open issue(s) in {repo}")
                
                # Filter issues for auto-opening
                for issue in issues:
                    issue_number = issue.get('number')
                    if not issue_number:
                        logger.warning(f"⚠️ Issue missing number field, skipping")
                        continue
                    
                    issue_title = issue.get('title', 'Untitled')
                    issue_labels = [label.get('name', '') for label in issue.get('labels', [])]
                    assignees = [user.get('login', '') for user in issue.get('assignees', [])]
                    
                    logger.debug(f"🔍 Checking issue #{issue_number}: {issue_title}")
                    
                    # Skip if already assigned
                    if assignees:
                        logger.debug(f"⏭️ Skipping issue #{issue_number} - already assigned to {assignees}")
                        continue
                    
                    # Check for skip labels
                    if any(label in self.config.issue_opener_skip_labels for label in issue_labels):
                        logger.debug(f"⏭️ Skipping issue #{issue_number} - has skip label")
                        continue
                    
                    # Check for trigger labels
                    has_trigger_label = any(label in self.config.issue_opener_trigger_labels for label in issue_labels)
                    if not has_trigger_label:
                        logger.debug(f"⏭️ Skipping issue #{issue_number} - missing trigger label")
                        continue
                    
                    # Check if already claimed or completed
                    issue_key = f"{repo}#{issue_number}"
                    
                    # Check if already processed (in state)
                    if issue_key in self.state:
                        issue_state = self.state[issue_key]
                        if issue_state.completed:
                            logger.debug(f"✅ Issue #{issue_number} already completed, skipping Issue Opener")
                            continue
                    
                    # Check if currently claimed (not expired)
                    if self.is_issue_claimed(repo, issue_number):
                        logger.debug(f"✅ Issue #{issue_number} already claimed")
                        continue
                    
                    # Trigger Issue Opener Agent
                    logger.info(f"🤖 Triggering Issue Opener for issue #{issue_number}: {issue_title}")
                    await self.trigger_issue_opener(repo, issue_number, issue)
                    
            except Exception as e:
                logger.error(f"❌ Error checking issues for {repo}: {e}", exc_info=True)
    
    async def trigger_pr_review(self, repo: str, pr_number: int, pr_data: Dict):
        """Trigger PR Reviewer Agent for a pull request with intelligent merge.
        
        Uses intelligent reviewer selection and automated merge based on config:
        - dedicated: Always use configured reviewer_agent_id
        - round-robin: Rotate between available code agents (skip PR author)
        - all: All code agents review (except PR author)
        
        After review, optionally merges PR based on merge_config settings:
        - auto_merge_if_approved: Merge if 0 issues found
        - merge_with_suggestions: Merge if only suggestions/warnings (no critical)
        
        Args:
            repo: Repository (owner/repo)
            pr_number: PR number
            pr_data: PR data dictionary from GitHub API
        """
        try:
            from engine.operations.pr_review_agent import PRReviewAgent
            
            pr_key = f"{repo}#{pr_number}"
            pr_author = pr_data.get('user', {}).get('login', '')
            
            logger.info(f"🤖 Starting automated PR review for {pr_key} (author: {pr_author})")
            
            # Initialize PR review agent with config
            review_agent = PRReviewAgent(
                use_llm=self.config.pr_use_llm,
                llm_model=self.config.pr_llm_model,
                bot_account=self.config.pr_bot_account
            )
            
            # Perform complete review + merge workflow
            if self.config.pr_merge_enabled:
                logger.info(f"🔀 Running complete review + merge workflow for {pr_key}")
                
                # Add delay before merge (safety)
                merge_delay = self.config.pr_merge_delay_seconds
                
                result = review_agent.complete_pr_review_and_merge_workflow(
                    repo=repo,
                    pr_number=pr_number,
                    post_comment=self.config.pr_post_comments,
                    auto_merge_if_approved=self.config.pr_auto_merge_if_approved,
                    merge_with_suggestions=self.config.pr_merge_with_suggestions,
                    merge_method=self.config.pr_merge_method
                )
                
                # Log merge decision
                merge_decision = result.get('merge_decision', {})
                recommendation = merge_decision.get('recommendation', 'UNKNOWN')
                merged = result.get('merged', False)
                
                logger.info(f"📊 Merge decision for {pr_key}: {recommendation}")
                if merged:
                    logger.info(f"✅ Successfully merged {pr_key} using {self.config.pr_merge_method}")
                else:
                    reasoning = merge_decision.get('reasoning', 'No reasoning provided')
                    logger.info(f"⏸️ PR {pr_key} not merged: {reasoning}")
                
            else:
                # Review only, no merge
                logger.info(f"🔍 Running review-only workflow for {pr_key} (merge disabled)")
                
                result = review_agent.complete_pr_review_workflow(
                    repo=repo,
                    pr_number=pr_number,
                    post_comment=self.config.pr_post_comments
                )
            
            # Log review results
            review_result = result.get('review_result', {})
            decision = review_result.get('decision', 'UNKNOWN')
            issue_count = len(review_result.get('issues', []))
            
            logger.info(f"✅ PR review completed for {pr_key}: {decision} ({issue_count} issues found)")
            
            # Mark as reviewed with commit SHA and timestamp (for memory leak prevention)
            import time
            head_sha = pr_data.get('head', {}).get('sha', '')
            self.reviewed_prs[pr_key] = {
                'sha': head_sha,
                'reviewed_at': time.time()
            }
            logger.debug(f"📝 Marked PR {pr_key} as reviewed at commit {head_sha[:7] if head_sha else 'unknown'}")
            
        except Exception as e:
            logger.error(f"❌ Failed to trigger PR review for {repo}#{pr_number}: {e}", exc_info=True)
    
    async def check_and_fix_draft_prs(self):
        """Check draft PRs created by bot and mark ready if approved."""
        try:
            from engine.operations.bot_operations import BotOperations
            from engine.operations.pr_review_agent import PRReviewAgent
            
            # Initialize bot operations
            bot = BotOperations()
            
            # Initialize PR review agent to access mark_ready_for_review
            pr_agent = PRReviewAgent(
                github_token=self.config.github_token,
                bot_account=self.config.pr_bot_account
            )
            
            # Check each monitored repo
            for repo in self.config.repositories:
                logger.info(f"🔍 Checking draft PRs in {repo}...")
                
                # List draft PRs by bot account
                draft_prs = bot.list_draft_prs_by_author(repo)
                
                if not draft_prs:
                    logger.debug(f"   No draft PRs found in {repo}")
                    continue
                
                logger.info(f"   Found {len(draft_prs)} draft PR(s)")
                
                for pr in draft_prs:
                    pr_number = pr.get('number')
                    if not pr_number:
                        logger.warning(f"⚠️ PR missing number: {pr}")
                        continue
                    
                    # Check if should mark ready
                    if bot.should_fix_draft_pr(pr):
                        logger.info(f"✅ PR #{pr_number} is approved with no issues - marking ready")
                        
                        # Mark ready for review
                        success = pr_agent.mark_ready_for_review(
                            repo=repo,
                            pr_number=pr_number,
                            reason="approved with no critical issues"
                        )
                        
                        if success:
                            logger.info(f"✅ Marked PR #{pr_number} ready for review")
                        else:
                            logger.warning(f"⚠️ Failed to mark PR #{pr_number} ready")
                    else:
                        logger.info(f"⏭️ PR #{pr_number} not ready yet (review: {pr.get('latest_review_state')}, issues: {len(pr.get('critical_issues', []))})")
        
        except Exception as e:
            logger.error(f"❌ Error checking draft PRs: {e}", exc_info=True)
    
    async def trigger_issue_opener(self, repo: str, issue_number: int, issue_data: Dict):
        """Trigger Issue Opener Agent for an issue.
        
        Args:
            repo: Repository (owner/repo)
            issue_number: Issue number
            issue_data: Issue data dictionary from GitHub API
        """
        issue_key = f"{repo}#{issue_number}"
        
        try:
            # Initialize state tracking for this issue
            if issue_key not in self.state:
                self.state[issue_key] = IssueState(
                    issue_number=issue_number,
                    repository=repo,
                    claimed_by=self.config.issue_opener_agent_id,
                    claimed_at=datetime.now().isoformat(),
                    completed=False
                )
                self.save_state()
            
            # Get code agent from registry (IssueHandler is accessed via CodeAgent)
            if not self.agent_registry:
                logger.warning(f"⚠️ Agent registry not available, cannot trigger Issue Opener for {issue_key}")
                # Mark as completed even on failure to prevent retry loops
                self.state[issue_key].completed = True
                self.state[issue_key].completed_at = datetime.now().isoformat()
                self.state[issue_key].last_error = "Agent registry not available"
                self.save_state()
                return
            
            # Get the code agent that has IssueHandler capability
            code_agent = self.agent_registry.get_agent(self.config.issue_opener_agent_id)
            if not code_agent:
                logger.error(f"❌ Code agent '{self.config.issue_opener_agent_id}' not found in registry")
                # Mark as completed to prevent retry loops
                self.state[issue_key].completed = True
                self.state[issue_key].completed_at = datetime.now().isoformat()
                self.state[issue_key].last_error = f"Code agent '{self.config.issue_opener_agent_id}' not found"
                self.save_state()
                return
            
            # Verify the agent has IssueHandler
            if not hasattr(code_agent, 'issue_handler'):
                logger.error(f"❌ Agent '{self.config.issue_opener_agent_id}' does not have IssueHandler capability")
                # Mark as completed to prevent retry loops
                self.state[issue_key].completed = True
                self.state[issue_key].completed_at = datetime.now().isoformat()
                self.state[issue_key].last_error = "Agent does not have IssueHandler capability"
                self.save_state()
                return
            
            logger.info(f"🤖 Starting Issue Opener with agent {self.config.issue_opener_agent_id}")
            
            # Call IssueHandler via CodeAgent
            result = code_agent.issue_handler.assign_to_issue(
                repo=repo,
                issue_number=issue_number
            )
            
            # Log result and mark as completed
            if result.get('success'):
                logger.info(f"✅ Issue Opener completed for {issue_key}")
                logger.info(f"   📝 Files modified: {len(result.get('files_modified', []))}")
                if result.get('pr_url'):
                    logger.info(f"   🔀 PR created: {result['pr_url']}")
            else:
                logger.error(f"❌ Issue Opener failed for {issue_key}: {result.get('error', 'UNKNOWN')}")
                self.state[issue_key].last_error = result.get('error', 'UNKNOWN')
            
            # Always mark as completed to prevent retry loops
            self.state[issue_key].completed = True
            self.state[issue_key].completed_at = datetime.now().isoformat()
            self.save_state()
            
        except Exception as e:
            logger.error(f"❌ Failed to trigger Issue Opener for {repo}#{issue_number}: {e}", exc_info=True)
            # Mark as completed even on exception to prevent infinite retries
            if issue_key in self.state:
                self.state[issue_key].completed = True
                self.state[issue_key].completed_at = datetime.now().isoformat()
                self.state[issue_key].last_error = str(e)
                self.save_state()
    
    async def claim_issue(self, repo: str, issue_number: int) -> bool:
        """Claim an issue by adding a comment.
        
        Args:
            repo: Repository (owner/repo)
            issue_number: Issue number
            
        Returns:
            True if successfully claimed
        """
        try:
            owner, repo_name = repo.split('/')
            comment = f"🤖 Agent **{self.config.github_username}** started working on this issue at {_utc_iso()}"
            # Prefer gh CLI for tests; fallback to REST helper
            try:
                path = f"/repos/{owner}/{repo_name}/issues/{issue_number}/comments"
                # Use -f to send form body
                res = subprocess.run(
                    ["gh", "api", "-X", "POST", path, "-f", f"body={comment}"],
                    text=True,
                    capture_output=True
                )
                if res.returncode != 0:
                    raise RuntimeError(res.stderr.strip() or "gh api failed")
            except Exception:
                self.github_api.create_issue_comment(
                    owner=owner,
                    repo=repo_name,
                    issue_number=issue_number,
                    body=comment
                )
            
            logger.info(f"Claimed issue {repo}#{issue_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to claim issue {repo}#{issue_number}: {e}")
            return False
    
    async def start_issue_workflow(self, issue: Dict) -> bool:
        """Start IssueHandler workflow for an issue.
        
        Args:
            issue: Issue dictionary
            
        Returns:
            True if workflow started successfully
        """
        repo = issue['repository']
        issue_number = issue['number']
        issue_key = self.get_issue_key(repo, issue_number)
        
        logger.info(f"Starting workflow for {issue_key}: {issue['title']}")
        
        # Check if issue is already claimed by ANY agent (not just ours)
        # This prevents spamming "started working" comments
        if self.is_issue_claimed(repo, issue_number):
            logger.info(f"✅ Issue {issue_key} already claimed, proceeding with workflow without adding new claim")
        else:
            # No valid claim exists, add one
            logger.info(f"🔖 Adding claim for {issue_key}")
            if not await self.claim_issue(repo, issue_number):
                logger.error(f"Failed to claim issue {issue_key}")
                return False

        
        # Update state
        self.state[issue_key] = IssueState(
            issue_number=issue_number,
            repository=repo,
            claimed_by=self.config.github_username,
            claimed_at=_utc_iso()
        )
        self.save_state()
        
        try:
            # Get agent from registry (wait if not available yet)
            if not self.agent_registry:
                logger.warning(f"Agent registry not available yet for workflow {issue_key}, will retry...")
                # Don't mark as failed, just skip for now - will retry in next cycle
                self.state[issue_key].claimed_by = None  # Release claim
                self.state[issue_key].claimed_at = None
                self.save_state()
                return False
            
            # Select a developer agent (not bot agent) from registry
            # Prefer agents with GitHub tokens for committing code
            developer_agents = [
                'm0nk111-qwen-agent',  # Primary: has token + Qwen model
                'm0nk111-coder1',      # Backup 1: has token + Qwen model
                'm0nk111-coder2',      # Backup 2: has token + Qwen model
                'gpt4-coding-agent',   # Backup 3: no token but GPT-4
                'developer-agent',     # Backup 4: no token
            ]
            
            agent = None
            agent_id = None
            for candidate_id in developer_agents:
                agent = self.agent_registry.get_agent(candidate_id)
                if agent:
                    agent_id = candidate_id
                    break
            
            if not agent:
                logger.error(f"No developer agent found in registry (tried: {developer_agents})")
                return False
            
            logger.info(f"✅ Using developer agent: {agent_id} for issue {issue_key}")
            
            # Use Pipeline Orchestrator for autonomous workflow
            from engine.core.pipeline_orchestrator import get_orchestrator, PipelineConfig
            
            # Get or create orchestrator instance
            pipeline_config = PipelineConfig(
                default_repos=[repo],
                auto_merge_on_approval=False,  # Safety: don't auto-merge yet
                require_tests_passing=True
            )
            orchestrator = get_orchestrator(pipeline_config, agent=agent)  # Pass agent for LLM operations
            
            # Run autonomous pipeline
            logger.info(f"🚀 Starting autonomous pipeline for {issue_key}")
            result = await orchestrator.handle_new_issue(repo, issue_number)
            success = result.get('success', False)
            
            # Update state - mark as completed regardless of success/failure
            self.state[issue_key].completed = True  # Always mark as completed to prevent infinite reprocessing
            self.state[issue_key].completed_at = _utc_iso()
            if success:
                logger.info(f"✅ Workflow succeeded for {issue_key}")
            else:
                logger.error(f"❌ Workflow failed for {issue_key}: {result.get('error', 'Unknown error')}")
                self.state[issue_key].last_error = result.get('error', 'Unknown error')
                self.state[issue_key].error_count += 1
            self.save_state()
            
            return success
            
        except Exception as e:
            logger.error(f"Error in workflow for {issue_key}: {e}")
            
            # Mark as completed even on exception to prevent infinite reprocessing
            self.state[issue_key].completed = True
            self.state[issue_key].completed_at = _utc_iso()
            self.state[issue_key].last_error = str(e)
            self.state[issue_key].error_count += 1
            self.save_state()
            
            return False
    
    def get_processing_count(self) -> int:
        """Get count of currently processing issues.
        
        Returns:
            Number of issues being processed
        """
        return sum(
            1 for state in self.state.values()
            if not state.completed
        )
    
    async def poll_once(self):
        """Perform one polling cycle."""
        logger.info("=== Starting polling cycle ===")
        
        # Update monitor status
        if self.monitor:
            from engine.runners.monitor_service import AgentStatus
            self.monitor.update_agent_status(
                agent_id="polling-service",
                status=AgentStatus.WORKING,
                current_task="Polling repositories for issues"
            )
            self.monitor.add_log(
                agent_id="polling-service",
                level="INFO",
                message="Starting polling cycle"
            )
        
        try:
            # Check assigned issues
            issues = await self.check_assigned_issues()
            
            # DEBUG: Log what we got
            logger.info(f"🐛 DEBUG: check_assigned_issues returned {len(issues)} issues")
            if issues:
                logger.info(f"🐛 DEBUG: First issue keys: {list(issues[0].keys())}")
            
            # Filter actionable
            actionable = self.filter_actionable_issues(issues)
            
            # DEBUG: Log filtering result
            logger.info(f"🐛 DEBUG: filter_actionable_issues returned {len(actionable)} issues")
            
            if not actionable:
                logger.info("No actionable issues found")
                if self.monitor:
                    self.monitor.add_log(
                        agent_id="polling-service",
                        level="INFO",
                        message="No actionable issues found"
                    )
            else:
                if self.monitor:
                    self.monitor.add_log(
                        agent_id="polling-service",
                        level="INFO",
                        message=f"Found {len(actionable)} actionable issues"
                    )
            
            # Check capacity
            processing_count = self.get_processing_count()
            available_slots = self.config.max_concurrent_issues - processing_count
            
            if available_slots <= 0:
                logger.info(f"At max capacity ({self.config.max_concurrent_issues} concurrent issues)")
                if self.monitor:
                    self.monitor.add_log(
                        agent_id="polling-service",
                        level="WARNING",
                        message=f"At max capacity ({self.config.max_concurrent_issues} concurrent)"
                    )
            elif actionable:
                # Start workflows for available slots
                for issue in actionable[:available_slots]:
                    await self.start_issue_workflow(issue)
                    # Small delay between starts
                    await asyncio.sleep(2)
            
            # Check for PRs needing review (if enabled)
            if self.config.pr_monitoring_enabled:
                logger.info("🔍 Checking for PRs needing review...")
                await self.check_pull_requests()
            
            # Check for new issues to auto-open (if enabled)
            if self.config.issue_opener_enabled:
                logger.info("🔍 Checking for issues to auto-open...")
                await self.check_new_issues_for_opener()
            
            # Check and fix draft PRs (if enabled)
            if self.config.pr_monitoring_enabled:
                await self.check_and_fix_draft_prs()
            
        except Exception as e:
            logger.error(f"Error in polling cycle: {e}")
        finally:
            # Update metrics
            self.update_metrics()
            
            # Cleanup old state
            self.cleanup_old_state()
            
            # Set back to IDLE
            if self.monitor:
                from engine.runners.monitor_service import AgentStatus
                self.monitor.update_agent_status(
                    agent_id="polling-service",
                    status=AgentStatus.IDLE,
                    current_task=None
                )
            
            # Periodic cleanup of stale review locks and old reviewed PRs
            if hasattr(self, '_cleanup_counter'):
                self._cleanup_counter += 1
                if self._cleanup_counter >= 10:  # Every 10 cycles
                    self._cleanup_stale_locks()
                    self._cleanup_old_reviewed_prs()
                    self._cleanup_counter = 0
            else:
                self._cleanup_counter = 0
            
            logger.info("=== Polling cycle complete ===")
    
    def _cleanup_stale_locks(self):
        """Clean up stale review locks."""
        try:
            from engine.utils.review_lock import ReviewLock
            lock_mgr = ReviewLock()
            lock_mgr.cleanup_stale_locks()
            logger.debug("🧹 Cleaned up stale review locks")
        except Exception as e:
            logger.error(f"❌ Error cleaning up stale locks: {e}")
    
    def _cleanup_old_reviewed_prs(self):
        """Clean up old reviewed PR entries to prevent memory leak.
        
        Removes entries:
        1. Older than max_age_days (default: 7 days)
        2. Excess entries beyond max_size (keeps most recent)
        """
        import time
        
        try:
            initial_count = len(self.reviewed_prs)
            if initial_count == 0:
                return
            
            current_time = time.time()
            max_age_seconds = self.reviewed_prs_max_age_days * 24 * 3600
            removed_count = 0
            
            # Remove old entries
            old_keys = []
            for pr_key, entry in self.reviewed_prs.items():
                if isinstance(entry, dict):
                    reviewed_at = entry.get('reviewed_at', 0)
                    age_seconds = current_time - reviewed_at
                    if age_seconds > max_age_seconds:
                        old_keys.append(pr_key)
            
            for key in old_keys:
                del self.reviewed_prs[key]
                removed_count += 1
            
            # Enforce max size (keep most recent)
            if len(self.reviewed_prs) > self.reviewed_prs_max_size:
                # Sort by timestamp (most recent first)
                sorted_entries = sorted(
                    self.reviewed_prs.items(),
                    key=lambda x: x[1].get('reviewed_at', 0) if isinstance(x[1], dict) else 0,
                    reverse=True
                )
                
                # Keep only max_size most recent entries
                self.reviewed_prs = dict(sorted_entries[:self.reviewed_prs_max_size])
                removed_count += initial_count - len(self.reviewed_prs)
            
            if removed_count > 0:
                logger.info(f"🧹 Cleaned up {removed_count} old reviewed PR entries (was {initial_count}, now {len(self.reviewed_prs)})")
            else:
                logger.debug(f"✅ No old reviewed PR entries to clean up ({initial_count} entries, all recent)")
        
        except Exception as e:
            logger.error(f"❌ Error cleaning up reviewed PRs: {e}")
    
    async def run(self):
        """Run continuous polling loop."""
        logger.info(f"Starting polling service (interval: {self.config.interval_seconds}s)")
        logger.info(f"Monitoring repositories: {self.config.repositories}")
        logger.info(f"Watching labels: {self.config.watch_labels}")
        logger.info(f"Max concurrent issues: {self.config.max_concurrent_issues}")
        
        self.running = True
        
        # Initial delay to allow agent registry injection
        logger.info("Waiting 3s for agent registry initialization...")
        await asyncio.sleep(3)
        
        try:
            while self.running:
                await self.poll_once()
                logger.info(f"Sleeping for {self.config.interval_seconds}s...")
                await asyncio.sleep(self.config.interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Polling service stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in polling service: {e}")
        finally:
            self.running = False
            logger.info("Polling service shut down")
    
    def stop(self):
        """Stop the polling service."""
        logger.info("Stopping polling service...")
        self.running = False
        
        # Cleanup lock file
        try:
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
                logger.info(f"✅ Removed lock file: {LOCK_FILE}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to remove lock file: {e}")


async def main():
    """Main entry point for standalone polling service."""
    import argparse
    
    # Configure logging FIRST (before lock check)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure only one instance runs at a time
    lock_fd = ensure_single_instance()
    logger.info(f"✅ Single instance lock acquired (PID: {os.getpid()})")
    
    parser = argparse.ArgumentParser(description="Autonomous GitHub issue polling service")
    parser.add_argument("--interval", type=int, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--repos", nargs="+", help="Repositories to monitor (owner/repo)")
    parser.add_argument("--labels", nargs="+", help="Labels to watch for")
    parser.add_argument("--max-concurrent", type=int, help="Max concurrent issues")
    parser.add_argument("--config", type=str, help="Path to YAML config file")
    
    args = parser.parse_args()
    
    # (removed duplicate logging config)
    
    # Initialize agent registry (required for workflow execution)
    logger.info("🔧 Initializing agent registry...")
    try:
        from engine.core.config_manager import get_config_manager
        from engine.core.agent_registry import AgentRegistry
        
        config_manager = get_config_manager()
        agent_registry = AgentRegistry(config_manager, monitor=None)
        
        # Load all enabled agents
        loaded = await agent_registry.load_agents()
        logger.info(f"📋 Loaded {len(loaded)} agents:")
        for agent_id, lifecycle in loaded.items():
            logger.info(f"   - {agent_id}: {lifecycle}")
        
        # Start always-on agents
        started = await agent_registry.start_always_on_agents()
        logger.info(f"✅ Started {len(started)} always-on agents")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent registry: {e}")
        logger.warning("⚠️  Polling service will run without agent registry (workflows will be skipped)")
        agent_registry = None
    
    # Create service (loads from YAML by default, CLI args override)
    config_path = Path(args.config) if args.config else None
    service = PollingService(config_path=config_path, agent_registry=agent_registry, enable_monitoring=False)
    
    # Apply CLI overrides if provided
    if args.interval is not None:
        service.config.interval_seconds = args.interval
    if args.repos:
        service.config.repositories = args.repos
    if args.labels:
        service.config.watch_labels = args.labels
    if args.max_concurrent is not None:
        service.config.max_concurrent_issues = args.max_concurrent
    
    if args.once:
        await service.poll_once()
    else:
        await service.run()


if __name__ == "__main__":
    asyncio.run(main())
