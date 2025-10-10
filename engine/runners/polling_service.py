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
"""

import asyncio
import json
import logging
import os
import time
import subprocess
from dataclasses import dataclass, asdict, field, fields, MISSING
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml


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


@dataclass
class PollingConfig:
    """Configuration for the polling service."""
    
    interval_seconds: int = 300  # 5 minutes
    github_token: Optional[str] = None
    github_username: str = "m0nk111-bot"
    repositories: List[str] = field(default_factory=list)  # ["owner/repo", ...]
    watch_labels: List[str] = field(default_factory=lambda: ["agent-ready", "auto-assign"])  # labels
    max_concurrent_issues: int = 3
    claim_timeout_minutes: int = 60
    state_file: str = "polling_state.json"
    
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
        self.agent_registry = agent_registry
        self.state_file = Path(self.config.state_file)
        self.state: Dict[str, IssueState] = {}
        self.load_state()
        self.running = False
        self.enable_monitoring = enable_monitoring
        self.monitor = None
        self.api_calls = 0  # Track API calls
        self.creative_logs_enabled = os.getenv("POLLING_CREATIVE_LOGS", "0") in {"1", "true", "TRUE"}
        
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
                cfg.repositories = [str(r) for r in repos]
            labels = data.get('watch_labels') or []
            if isinstance(labels, list) and labels:
                cfg.watch_labels = [str(l) for l in labels]
            # Concurrency & state
            cfg.max_concurrent_issues = int(data.get('max_concurrent_issues', cfg.max_concurrent_issues))
            cfg.claim_timeout_minutes = int(data.get('claim_timeout_minutes', cfg.claim_timeout_minutes))
            state_file = data.get('state_file')
            if isinstance(state_file, str) and state_file.strip():
                cfg.state_file = state_file.strip()
        except Exception as e:
            logger.error(f"❌ Error parsing YAML config values: {e}; continuing with partial defaults")
        return cfg

    def _apply_config_overrides(self, override: PollingConfig):
        """Override YAML-loaded configuration with explicitly provided override values.

        Only apply overrides for fields whose value differs from the dataclass default.
        This prevents accidental replacement of YAML values with implicit defaults
        coming from the override instance. Special-case github_token to avoid overriding
        a YAML token with environment-derived values unless explicitly set.
        """
        # Build a map of default values from the dataclass definition (no __post_init__ effects)
        defaults = {}
        for f in fields(PollingConfig):
            if f.default is not MISSING:
                defaults[f.name] = f.default
            elif f.default_factory is not MISSING:  # type: ignore[attr-defined]
                defaults[f.name] = f.default_factory()  # type: ignore[misc]
            else:
                defaults[f.name] = None

        # Apply only non-default overrides
        for field_name, default_value in defaults.items():
            value = getattr(override, field_name, None)
            # Skip if no value or value equals the dataclass default (not explicitly overridden)
            if value is None or value == default_value:
                continue

            # Avoid overriding YAML token with env-provided token unless explicitly different
            if field_name == 'github_token':
                env_token = os.getenv('BOT_GITHUB_TOKEN') or os.getenv('GITHUB_TOKEN')
                # If the override token equals the env token, it's likely implicit -> skip
                if value == env_token:
                    continue

            setattr(self.config, field_name, value)
        
    def load_state(self):
        """Load polling state from disk."""
        if self.state_file.exists():
            try:
                with self.state_file.open('r') as f:
                    data = json.load(f)
                    self.state = {
                        key: IssueState(**value)
                        for key, value in data.items()
                    }
                logger.info(f"Loaded state: {len(self.state)} tracked issues")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self.state = {}
        else:
            logger.info("No existing state file, starting fresh")
            self.state = {}
    
    def save_state(self):
        """Save polling state to disk."""
        try:
            data = {
                key: asdict(value)
                for key, value in self.state.items()
            }
            with self.state_file.open('w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved state: {len(self.state)} tracked issues")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def cleanup_old_state(self):
        """Remove old completed/closed issues from state."""
        now = _utc_now()
        cutoff = now - timedelta(days=7)
        
        to_remove = []
        for key, issue_state in self.state.items():
            if issue_state.completed and issue_state.completed_at:
                completed_time = _parse_iso_timestamp(issue_state.completed_at)
                if completed_time < cutoff:
                    to_remove.append(key)
        
        for key in to_remove:
            del self.state[key]
            logger.info(f"Cleaned up old state: {key}")
        
        if to_remove:
            self.save_state()
    
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
        """Query GitHub API for assigned issues.
        
        Returns:
            List of assigned issue dictionaries
        """
        logger.info("Checking for assigned issues...")
        
        all_issues = []
        
        for repo in self.config.repositories:
            try:
                owner, repo_name = repo.split('/')
                # Prefer gh CLI for tests and portability; fallback to REST helper
                try:
                    path = f"/repos/{owner}/{repo_name}/issues?state=open&per_page=100&assignee={self.config.github_username}"
                    stdout = subprocess.run(
                        ["gh", "api", path],
                        text=True,
                        capture_output=True
                    )
                    if stdout.returncode != 0:
                        raise RuntimeError(stdout.stderr.strip() or "gh api failed")
                    issues = json.loads(stdout.stdout or "[]")
                except Exception:
                    issues = self.github_api.list_issues(
                        owner=owner,
                        repo=repo_name,
                        assignee=self.config.github_username,
                        state="open",
                        per_page=100,
                        bypass_rate_limit=True
                    )
                    # Increment API call counter
                    self.api_calls += 1
                
                # Add repository field to each issue
                for issue in issues:
                    issue['repository'] = repo
                all_issues.extend(issues)
                
                logger.info(f"Found {len(issues)} assigned issues in {repo}")
                
            except Exception as e:
                logger.error(f"Failed to query issues for {repo}: {e}")
        
        logger.info(f"Total assigned issues found: {len(all_issues)}")
        return all_issues
    
    def filter_actionable_issues(self, issues: List[Dict]) -> List[Dict]:
        """Filter issues based on labels and state.
        
        Args:
            issues: List of issue dictionaries
            
        Returns:
            Filtered list of actionable issues
        """
        actionable = []
        
        logger.info(f"🐛 DEBUG: Filtering {len(issues)} issues")
        
        for idx, issue in enumerate(issues):
            try:
                logger.info(f"🐛 DEBUG: Processing issue {idx+1}/{len(issues)}")
                logger.info(f"🐛 DEBUG: Issue dict keys: {list(issue.keys())}")
                logger.info(f"🐛 DEBUG: Issue repository: {issue.get('repository')}")
                logger.info(f"🐛 DEBUG: Issue number: {issue.get('number')}")
                issue_key = self.get_issue_key(issue['repository'], issue['number'])
                
                logger.info(f"🔍 Evaluating issue {issue_key}: {issue['title']}")
                logger.info(f"   Labels: {[label['name'] for label in issue.get('labels', [])]}")
                logger.info(f"   Watch labels: {self.config.watch_labels}")
                logger.info(f"   In state: {issue_key in self.state}")
                
                # Skip if already processing
                if issue_key in self.state and not self.state[issue_key].completed:
                    logger.info(f"   ❌ Skipping: already processing (not completed)")
                    continue
                
                # Skip if completed recently
                if issue_key in self.state and self.state[issue_key].completed:
                    logger.info(f"   ❌ Skipping: already completed")
                    continue
                
                # Check labels
                issue_labels = [label['name'] for label in issue.get('labels', [])]
                has_watch_label = any(
                    label in self.config.watch_labels
                    for label in issue_labels
                )
                
                logger.info(f"   Has watch label: {has_watch_label}")
                
                if has_watch_label:
                    logger.info(f"   ✅ Issue is actionable!")
                    actionable.append(issue)
                    logger.info(f"Actionable issue found: {issue_key} - {issue['title']}")
                    if self.creative_logs_enabled:
                        motif = generate_issue_motif(issue.get('title', ''), [label['name'] for label in issue.get('labels', [])])
                        logger.info("🎨 Creative pulse for %s:%s%s", issue_key, os.linesep, motif)
                else:
                    logger.info(f"   ❌ Skipping: no watch labels match")
                    
            except Exception as e:
                logger.error(f"🐛 DEBUG: Error processing issue {idx+1}: {e}", exc_info=True)
                continue
        
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
        
        # Check if already claimed by another agent
        if self.is_issue_claimed(repo, issue_number):
            logger.info(f"Issue {issue_key} already claimed, skipping")
            return False
        
        # Claim the issue
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
            
            # Get the agent by agent_id (username is the agent_id in this case)
            agent = self.agent_registry.get_agent(self.config.github_username)
            if not agent:
                logger.error(f"Agent '{self.config.github_username}' not found in registry")
                return False
            
            logger.info(f"✅ Using agent: {self.config.github_username} for issue {issue_key}")
            
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
            
            # Update state
            self.state[issue_key].completed = success
            self.state[issue_key].completed_at = _utc_iso()
            self.save_state()
            
            logger.info(f"Workflow completed for {issue_key}: {'success' if success else 'failed'}")
            return success
            
        except Exception as e:
            logger.error(f"Error in workflow for {issue_key}: {e}")
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
            
            logger.info("=== Polling cycle complete ===")
    
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


async def main():
    """Main entry point for standalone polling service."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous GitHub issue polling service")
    parser.add_argument("--interval", type=int, default=300, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--repos", nargs="+", help="Repositories to monitor (owner/repo)")
    parser.add_argument("--labels", nargs="+", help="Labels to watch for")
    parser.add_argument("--max-concurrent", type=int, default=3, help="Max concurrent issues")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create config
    config = PollingConfig(
        interval_seconds=args.interval,
        repositories=args.repos or ["m0nk111/stepperheightcontrol", "m0nk111/agent-forge"],
        watch_labels=args.labels or ["agent-ready", "auto-assign"],
        max_concurrent_issues=args.max_concurrent
    )
    
    # Create and run service
    service = PollingService(config)
    
    if args.once:
        await service.poll_once()
    else:
        await service.run()


if __name__ == "__main__":
    asyncio.run(main())
