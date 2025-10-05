"""Autonomous polling service for GitHub issue monitoring and automatic workflow initiation.

This module implements periodic polling to check for assigned GitHub issues and automatically
starts the IssueHandler workflow when new actionable issues are detected.

Features:
- Configurable polling intervals (default: 5 minutes)
- Multi-repository support
- Label-based filtering (agent-ready, auto-assign)
- Issue locking to prevent duplicate work by         except Exception as e:
            logger.error(f"Error during polling cycle: {e}")
            if self.monitor:
                from agents.monitor_service import AgentStatus
                self.monitor.update_agent_status(
                    agent_id="polling-service",
                    status=AgentStatus.ERROR,
                    error_message=str(e)
                )
                self.monitor.add_log(
                    agent_id="polling-service",
                    level="ERROR",
                    message=f"Polling error: {e}"
                )
        finally:
            # Cleanup old state
            self.cleanup_old_state()
            logger.info("=== Polling cycle complete ===")
            
            # Return to idle
            if self.monitor:
                from agents.monitor_service import AgentStatus
                self.monitor.update_agent_status(
                    agent_id="polling-service",
                    status=AgentStatus.IDLE,
                    current_task=f"Waiting (next poll in {self.config.interval_seconds}s)"
                )
                self.monitor.add_log(
                    agent_id="polling-service",
                    level="INFO",
                    message="Polling cycle complete"
                )le agents
- State persistence across restarts
- Graceful error handling with retry logic
- Structured logging for all events
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import subprocess

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
    repositories: List[str] = None  # ["owner/repo", ...]
    watch_labels: List[str] = None  # ["agent-ready", "auto-assign"]
    max_concurrent_issues: int = 3
    claim_timeout_minutes: int = 60
    state_file: str = "polling_state.json"
    
    def __post_init__(self):
        """Initialize default values."""
        if self.repositories is None:
            self.repositories = []
        if self.watch_labels is None:
            self.watch_labels = ["agent-ready", "auto-assign"]
        if self.github_token is None:
            self.github_token = os.getenv("BOT_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")


@dataclass
class IssueState:
    """State tracking for a single issue."""
    
    issue_number: int
    repository: str
    claimed_by: str
    claimed_at: str
    last_error: Optional[str] = None
    error_count: int = 0
    completed: bool = False
    completed_at: Optional[str] = None


class PollingService:
    """Service for autonomous GitHub issue polling and workflow initiation."""
    
    def __init__(self, config: PollingConfig, enable_monitoring: bool = True):
        """Initialize polling service.
        
        Args:
            config: Polling configuration
            enable_monitoring: Whether to register with monitor service
        """
        self.config = config
        self.state_file = Path(config.state_file)
        self.state: Dict[str, IssueState] = {}
        self.load_state()
        self.running = False
        self.enable_monitoring = enable_monitoring
        self.monitor = None
        self.api_calls = 0  # Track API calls
        
        # Register with monitor if enabled
        if enable_monitoring:
            try:
                import psutil
                self.process = psutil.Process()
            except ImportError:
                self.process = None
                logger.warning("psutil not installed, metrics will not be available")
            
            try:
                from agents.monitor_service import get_monitor, AgentStatus
                self.monitor = get_monitor()
                self.monitor.register_agent(
                    agent_id="polling-service",
                    agent_name="GitHub Polling Service"
                )
                self.monitor.update_agent_status(
                    agent_id="polling-service",
                    status=AgentStatus.IDLE,
                    current_task="Initialized"
                )
                
                # Add custom logging handler to forward all logs to monitor
                monitor_handler = MonitorLogHandler(self.monitor, "polling-service")
                monitor_handler.setFormatter(logging.Formatter('%(message)s'))
                logger.addHandler(monitor_handler)
                logger.setLevel(logging.INFO)  # Ensure INFO level is captured
                
                logger.info("✅ Registered with monitoring service")
            except Exception as e:
                logger.warning(f"Could not register with monitor: {e}")
                self.monitor = None
        
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
        now = datetime.utcnow()
        cutoff = now - timedelta(days=7)
        
        to_remove = []
        for key, issue_state in self.state.items():
            if issue_state.completed and issue_state.completed_at:
                completed_time = datetime.fromisoformat(issue_state.completed_at)
                if completed_time < cutoff:
                    to_remove.append(key)
        
        for key in to_remove:
            del self.state[key]
            logger.info(f"Cleaned up old state: {key}")
        
        if to_remove:
            self.save_state()
    
    def update_metrics(self):
        """Update agent metrics in monitor."""
        if not self.monitor or not self.process:
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
                # Use gh CLI to query issues
                cmd = [
                    "gh", "issue", "list",
                    "--repo", repo,
                    "--assignee", self.config.github_username,
                    "--state", "open",
                    "--json", "number,title,labels,assignees,url,createdAt,updatedAt",
                    "--limit", "100"
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Increment API call counter
                self.api_calls += 1
                
                issues = json.loads(result.stdout)
                for issue in issues:
                    issue['repository'] = repo
                all_issues.extend(issues)
                
                logger.info(f"Found {len(issues)} assigned issues in {repo}")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to query issues for {repo}: {e.stderr}")
            except Exception as e:
                logger.error(f"Error checking {repo}: {e}")
        
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
        
        for issue in issues:
            issue_key = self.get_issue_key(issue['repository'], issue['number'])
            
            # Skip if already processing
            if issue_key in self.state and not self.state[issue_key].completed:
                logger.debug(f"Skipping {issue_key}: already processing")
                continue
            
            # Skip if completed recently
            if issue_key in self.state and self.state[issue_key].completed:
                logger.debug(f"Skipping {issue_key}: already completed")
                continue
            
            # Check labels
            issue_labels = [label['name'] for label in issue.get('labels', [])]
            has_watch_label = any(
                label in self.config.watch_labels
                for label in issue_labels
            )
            
            if has_watch_label:
                actionable.append(issue)
                logger.info(f"Actionable issue found: {issue_key} - {issue['title']}")
        
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
            # Query issue comments
            cmd = [
                "gh", "issue", "view", str(issue_number),
                "--repo", repo,
                "--json", "comments",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            comments = data.get('comments', [])
            
            # Check for agent claim comments
            now = datetime.utcnow()
            timeout = timedelta(minutes=self.config.claim_timeout_minutes)
            
            for comment in comments:
                body = comment.get('body', '')
                if '🤖 Agent' in body and 'started working on this issue' in body:
                    # Check timestamp
                    created_at = datetime.fromisoformat(
                        comment['createdAt'].replace('Z', '+00:00')
                    )
                    if now - created_at.replace(tzinfo=None) < timeout:
                        logger.info(f"Issue {repo}#{issue_number} claimed by another agent")
                        return True
            
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
            comment = f"🤖 Agent **{self.config.github_username}** started working on this issue at {datetime.utcnow().isoformat()}Z"
            
            cmd = [
                "gh", "issue", "comment", str(issue_number),
                "--repo", repo,
                "--body", comment
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
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
            claimed_at=datetime.utcnow().isoformat()
        )
        self.save_state()
        
        try:
            # Import here to avoid circular dependency
            from agents.issue_handler import IssueHandler
            
            # Start issue handler (this would run in background/separate process in production)
            handler = IssueHandler()
            success = await handler.handle_issue(repo, issue_number)
            
            # Update state
            self.state[issue_key].completed = success
            self.state[issue_key].completed_at = datetime.utcnow().isoformat()
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
            from agents.monitor_service import AgentStatus
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
            
            # Filter actionable
            actionable = self.filter_actionable_issues(issues)
            
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
                from agents.monitor_service import AgentStatus
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
