"""
Bot Agent for automated GitHub operations.

This agent handles GitHub operations using a dedicated bot account (m0nk111-post)
to prevent email spam to admin accounts. Includes rate limiting, error handling,
and comprehensive monitoring integration.

Example:
    bot = BotAgent()
    issue = await bot.create_issue(
        repo="owner/repo",
        title="New feature request",
        body="Description",
        labels=["enhancement"]
    )
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import json
import yaml

logger = logging.getLogger(__name__)


@dataclass
class BotOperation:
    """Record of a bot operation."""
    operation_type: str
    timestamp: datetime
    repo: str
    target_id: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    response_time: float = 0.0


@dataclass
class BotMetrics:
    """Metrics tracking for bot operations."""
    operations_total: int = 0
    operations_by_type: Dict[str, int] = field(default_factory=dict)
    issues_created: int = 0
    comments_added: int = 0
    assignments_made: int = 0
    labels_updated: int = 0
    issues_closed: int = 0
    api_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_response_time: float = 0.0
    rate_limit_remaining: int = 5000
    rate_limit_reset: Optional[datetime] = None
    last_operation: Optional[datetime] = None


class BotAgent:
    """
    Automated bot agent for GitHub operations.
    
    Uses dedicated bot account to prevent email spam and provide
    automated task management capabilities.
    
    Attributes:
        agent_id: Unique identifier for bot
        username: GitHub username for bot account
        github_token: Personal access token for bot
        metrics: Operation metrics tracking
        config: Bot configuration
    """
    
    def __init__(
        self,
        agent_id: str = "m0nk111-post",
        username: Optional[str] = None,
        github_token: Optional[str] = None,
        config_file: Optional[Path] = None,
        monitor: Optional[Any] = None
    ):
        """
        Initialize bot agent.
        
        Args:
            agent_id: Unique bot identifier
            username: GitHub username (defaults to BOT_GITHUB_USERNAME env)
            github_token: GitHub token (defaults to BOT_GITHUB_TOKEN env)
            config_file: Path to bot configuration YAML
            monitor: MonitorService instance for metrics
        """
        self.agent_id = agent_id
        self.username = username or os.getenv("BOT_GITHUB_USERNAME", "m0nk111-post")
        self.github_token = github_token or os.getenv("BOT_GITHUB_TOKEN")
        self.monitor = monitor
        
        if not self.github_token:
            logger.warning("No GitHub token configured for bot agent")
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize metrics
        self.metrics = BotMetrics()
        
        # Rate limiting
        self.rate_limit_threshold = self.config.get("rate_limiting", {}).get(
            "pause_threshold", 4800
        )
        self.retry_attempts = self.config.get("behavior", {}).get("retry_attempts", 3)
        self.retry_delay = self.config.get("behavior", {}).get("retry_delay", 5)
        
        # Operation history (last 100 operations)
        self.operation_history: List[BotOperation] = []
        self.max_history_size = 100
        
        logger.info(f"Bot agent initialized: {self.agent_id} ({self.username})")
    
    def _load_config(self, config_file: Optional[Path]) -> Dict:
        """Load bot configuration from YAML file."""
        if config_file and config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f).get('bot', {})
        
        # Default configuration
        return {
            "capabilities": [
                "create_issues",
                "add_comments",
                "assign_tasks",
                "update_labels",
                "close_issues",
                "update_projects"
            ],
            "rate_limiting": {
                "max_operations_per_hour": 500,
                "pause_threshold": 4800
            },
            "behavior": {
                "retry_attempts": 3,
                "retry_delay": 5
            },
            "monitoring": {
                "enabled": True,
                "report_interval": 60
            }
        }
    
    async def _execute_gh_command(
        self,
        command: List[str],
        operation_type: str,
        repo: str,
        target_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute GitHub CLI command with error handling and metrics.
        
        Args:
            command: GitHub CLI command parts
            operation_type: Type of operation for metrics
            repo: Repository name
            target_id: Optional target ID (issue/PR number)
        
        Returns:
            Parsed JSON response from GitHub API
        
        Raises:
            RuntimeError: If command fails after retries
        """
        start_time = datetime.now()
        
        # Set bot token for authentication
        env = os.environ.copy()
        if self.github_token:
            env["GH_TOKEN"] = self.github_token
        
        # Check rate limit before operation
        await self._check_rate_limit()
        
        # Retry loop
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30
                )
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                if result.returncode == 0:
                    # Parse JSON response
                    response = json.loads(result.stdout) if result.stdout else {}
                    
                    # Record successful operation
                    self._record_operation(
                        operation_type=operation_type,
                        repo=repo,
                        target_id=target_id,
                        success=True,
                        response_time=response_time
                    )
                    
                    return response
                else:
                    last_error = result.stderr
                    logger.warning(
                        f"Command failed (attempt {attempt + 1}/{self.retry_attempts}): {last_error}"
                    )
                    
                    # Wait before retry
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self.retry_delay)
            
            except subprocess.TimeoutExpired:
                last_error = "Command timeout"
                logger.warning(f"Command timeout (attempt {attempt + 1}/{self.retry_attempts})")
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
            
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}"
                logger.error(last_error)
                break
        
        # All retries failed
        response_time = (datetime.now() - start_time).total_seconds()
        self._record_operation(
            operation_type=operation_type,
            repo=repo,
            target_id=target_id,
            success=False,
            error=last_error,
            response_time=response_time
        )
        
        raise RuntimeError(f"GitHub operation failed after {self.retry_attempts} attempts: {last_error}")
    
    async def _check_rate_limit(self):
        """Check GitHub API rate limit and pause if needed."""
        try:
            result = subprocess.run(
                ["gh", "api", "rate_limit"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                rate_data = json.loads(result.stdout)
                core = rate_data.get("resources", {}).get("core", {})
                
                remaining = core.get("remaining", 5000)
                reset_timestamp = core.get("reset", 0)
                
                self.metrics.rate_limit_remaining = remaining
                if reset_timestamp:
                    self.metrics.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
                
                # Pause if below threshold
                if remaining < self.rate_limit_threshold:
                    wait_time = (self.metrics.rate_limit_reset - datetime.now()).total_seconds()
                    if wait_time > 0:
                        logger.warning(
                            f"Rate limit low ({remaining} remaining). Pausing for {wait_time:.0f}s"
                        )
                        await asyncio.sleep(wait_time)
        
        except Exception as e:
            logger.warning(f"Failed to check rate limit: {e}")
    
    def _record_operation(
        self,
        operation_type: str,
        repo: str,
        target_id: Optional[int],
        success: bool,
        error: Optional[str] = None,
        response_time: float = 0.0
    ):
        """Record operation in history and update metrics."""
        # Create operation record
        operation = BotOperation(
            operation_type=operation_type,
            timestamp=datetime.now(),
            repo=repo,
            target_id=target_id,
            success=success,
            error=error,
            response_time=response_time
        )
        
        # Add to history (keep last 100)
        self.operation_history.append(operation)
        if len(self.operation_history) > self.max_history_size:
            self.operation_history.pop(0)
        
        # Update metrics
        self.metrics.operations_total += 1
        self.metrics.api_calls += 1
        self.metrics.last_operation = datetime.now()
        self.metrics.total_response_time += response_time
        
        # Update operation type counter
        if operation_type not in self.metrics.operations_by_type:
            self.metrics.operations_by_type[operation_type] = 0
        self.metrics.operations_by_type[operation_type] += 1
        
        # Update success/failure counters
        if success:
            self.metrics.success_count += 1
            
            # Update specific counters
            if operation_type == "create_issue":
                self.metrics.issues_created += 1
            elif operation_type == "add_comment":
                self.metrics.comments_added += 1
            elif operation_type == "assign_issue":
                self.metrics.assignments_made += 1
            elif operation_type == "update_labels":
                self.metrics.labels_updated += 1
            elif operation_type == "close_issue":
                self.metrics.issues_closed += 1
        else:
            self.metrics.failure_count += 1
        
        # Report to monitor if available
        if self.monitor and success:
            try:
                # Log metric to monitor
                self.monitor.log_metric(
                    agent_id=self.agent_id,
                    metric_name=f"bot_{operation_type}",
                    value=1
                )
            except Exception as e:
                logger.debug(f"Failed to report to monitor: {e}")
    
    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue using bot account.
        
        Args:
            repo: Repository name (owner/repo)
            title: Issue title
            body: Issue body/description
            labels: List of labels to apply
            assignees: List of usernames to assign
            milestone: Milestone number
        
        Returns:
            Created issue data with number, url, etc.
        
        Example:
            issue = await bot.create_issue(
                repo="owner/repo",
                title="New feature request",
                body="Please add feature X",
                labels=["enhancement"],
                assignees=["developer1"]
            )
            print(f"Created issue #{issue['number']}")
        """
        command = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
        
        if labels:
            command.extend(["--label", ",".join(labels)])
        
        if assignees:
            command.extend(["--assignee", ",".join(assignees)])
        
        if milestone:
            command.extend(["--milestone", str(milestone)])
        
        command.append("--json")
        command.append("number,url,title")
        
        logger.info(f"Creating issue in {repo}: {title}")
        return await self._execute_gh_command(command, "create_issue", repo)
    
    async def add_comment(
        self,
        repo: str,
        issue_number: int,
        body: str
    ) -> Dict[str, Any]:
        """
        Add comment to issue or PR using bot account.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue or PR number
            body: Comment body
        
        Returns:
            Created comment data
        
        Example:
            await bot.add_comment(
                repo="owner/repo",
                issue_number=42,
                body="✅ Task completed successfully"
            )
        """
        command = [
            "gh", "issue", "comment", str(issue_number),
            "--repo", repo,
            "--body", body
        ]
        
        logger.info(f"Adding comment to {repo}#{issue_number}")
        return await self._execute_gh_command(command, "add_comment", repo, issue_number)
    
    async def assign_issue(
        self,
        repo: str,
        issue_number: int,
        assignees: List[str]
    ) -> Dict[str, Any]:
        """
        Assign issue to users.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            assignees: List of usernames to assign
        
        Returns:
            Updated issue data
        
        Example:
            await bot.assign_issue(
                repo="owner/repo",
                issue_number=42,
                assignees=["developer1", "reviewer1"]
            )
        """
        command = [
            "gh", "issue", "edit", str(issue_number),
            "--repo", repo,
            "--add-assignee", ",".join(assignees)
        ]
        
        logger.info(f"Assigning {repo}#{issue_number} to {', '.join(assignees)}")
        return await self._execute_gh_command(command, "assign_issue", repo, issue_number)
    
    async def update_labels(
        self,
        repo: str,
        issue_number: int,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update issue labels.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            add_labels: Labels to add
            remove_labels: Labels to remove
        
        Returns:
            Updated issue data
        
        Example:
            await bot.update_labels(
                repo="owner/repo",
                issue_number=42,
                add_labels=["in-progress"],
                remove_labels=["pending"]
            )
        """
        command = [
            "gh", "issue", "edit", str(issue_number),
            "--repo", repo
        ]
        
        if add_labels:
            command.extend(["--add-label", ",".join(add_labels)])
        
        if remove_labels:
            command.extend(["--remove-label", ",".join(remove_labels)])
        
        logger.info(f"Updating labels for {repo}#{issue_number}")
        return await self._execute_gh_command(command, "update_labels", repo, issue_number)
    
    async def close_issue(
        self,
        repo: str,
        issue_number: int,
        state_reason: str = "completed",
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close an issue.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            state_reason: Reason for closing ("completed" or "not_planned")
            comment: Optional closing comment
        
        Returns:
            Closed issue data
        
        Example:
            await bot.close_issue(
                repo="owner/repo",
                issue_number=42,
                state_reason="completed",
                comment="✅ All tasks completed. Closing issue."
            )
        """
        # Add comment first if provided
        if comment:
            await self.add_comment(repo, issue_number, comment)
        
        command = [
            "gh", "issue", "close", str(issue_number),
            "--repo", repo,
            "--reason", state_reason
        ]
        
        logger.info(f"Closing {repo}#{issue_number} ({state_reason})")
        return await self._execute_gh_command(command, "close_issue", repo, issue_number)
    
    async def reopen_issue(
        self,
        repo: str,
        issue_number: int,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reopen a closed issue.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            comment: Optional reopening comment
        
        Returns:
            Reopened issue data
        """
        # Add comment first if provided
        if comment:
            await self.add_comment(repo, issue_number, comment)
        
        command = [
            "gh", "issue", "reopen", str(issue_number),
            "--repo", repo
        ]
        
        logger.info(f"Reopening {repo}#{issue_number}")
        return await self._execute_gh_command(command, "reopen_issue", repo, issue_number)
    
    async def update_project(
        self,
        repo: str,
        issue_number: int,
        project_id: str,
        field_name: str,
        field_value: str
    ) -> bool:
        """
        Update project field for issue (GitHub Projects v2).
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            project_id: Project ID
            field_name: Field name to update
            field_value: New field value
        
        Returns:
            True if successful
        
        Note:
            Requires gh CLI with project extension or API access
        """
        # This is a simplified implementation
        # Full implementation would use GitHub GraphQL API
        logger.info(f"Updating project field for {repo}#{issue_number}")
        logger.warning("Project updates not fully implemented yet")
        return False
    
    def get_metrics(self) -> BotMetrics:
        """
        Get current bot metrics.
        
        Returns:
            BotMetrics object with all tracked metrics
        """
        return self.metrics
    
    def get_recent_operations(self, limit: int = 10) -> List[BotOperation]:
        """
        Get recent operation history.
        
        Args:
            limit: Maximum number of operations to return
        
        Returns:
            List of recent BotOperation objects
        """
        return self.operation_history[-limit:]
    
    def get_success_rate(self) -> float:
        """
        Calculate operation success rate.
        
        Returns:
            Success rate as percentage (0.0 - 100.0)
        """
        total = self.metrics.success_count + self.metrics.failure_count
        if total == 0:
            return 100.0
        return (self.metrics.success_count / total) * 100.0
    
    def get_average_response_time(self) -> float:
        """
        Calculate average response time for operations.
        
        Returns:
            Average response time in seconds
        """
        if self.metrics.api_calls == 0:
            return 0.0
        return self.metrics.total_response_time / self.metrics.api_calls
    
    def format_status(self) -> str:
        """
        Format bot status for dashboard display.
        
        Returns:
            Formatted status string
        """
        success_rate = self.get_success_rate()
        avg_response = self.get_average_response_time()
        
        status = f"🤖 {self.username} | BOT | ACTIVE\n"
        status += f"├─ Operations: {self.metrics.operations_total:,}\n"
        status += f"├─ Issues Created: {self.metrics.issues_created}\n"
        status += f"├─ Comments: {self.metrics.comments_added}\n"
        status += f"├─ Assignments: {self.metrics.assignments_made}\n"
        status += f"├─ Success Rate: {success_rate:.1f}%\n"
        status += f"├─ Avg Response: {avg_response:.2f}s\n"
        status += f"├─ Rate Limit: {self.metrics.rate_limit_remaining:,}/5,000\n"
        
        if self.metrics.last_operation:
            time_since = (datetime.now() - self.metrics.last_operation).total_seconds()
            if time_since < 60:
                status += f"└─ Last Active: {time_since:.0f}s ago"
            elif time_since < 3600:
                status += f"└─ Last Active: {time_since/60:.0f}m ago"
            else:
                status += f"└─ Last Active: {time_since/3600:.1f}h ago"
        else:
            status += "└─ Last Active: Never"
        
        return status


async def main():
    """CLI interface for testing bot operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bot Agent CLI")
    parser.add_argument("operation", choices=["create", "comment", "assign", "labels", "close", "status"])
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument("--issue", type=int, help="Issue number")
    parser.add_argument("--title", help="Issue title")
    parser.add_argument("--body", help="Issue body or comment")
    parser.add_argument("--labels", help="Comma-separated labels")
    parser.add_argument("--assignees", help="Comma-separated assignees")
    parser.add_argument("--config", type=Path, help="Config file path")
    
    args = parser.parse_args()
    
    # Initialize bot
    bot = BotAgent(config_file=args.config)
    
    try:
        if args.operation == "create":
            if not args.title or not args.body:
                print("Error: --title and --body required for create")
                return
            
            labels = args.labels.split(",") if args.labels else None
            assignees = args.assignees.split(",") if args.assignees else None
            
            result = await bot.create_issue(
                repo=args.repo,
                title=args.title,
                body=args.body,
                labels=labels,
                assignees=assignees
            )
            print(f"✅ Created issue #{result['number']}: {result['url']}")
        
        elif args.operation == "comment":
            if not args.issue or not args.body:
                print("Error: --issue and --body required for comment")
                return
            
            await bot.add_comment(args.repo, args.issue, args.body)
            print(f"✅ Added comment to {args.repo}#{args.issue}")
        
        elif args.operation == "assign":
            if not args.issue or not args.assignees:
                print("Error: --issue and --assignees required for assign")
                return
            
            assignees = args.assignees.split(",")
            await bot.assign_issue(args.repo, args.issue, assignees)
            print(f"✅ Assigned {args.repo}#{args.issue} to {', '.join(assignees)}")
        
        elif args.operation == "labels":
            if not args.issue or not args.labels:
                print("Error: --issue and --labels required for labels")
                return
            
            labels = args.labels.split(",")
            await bot.update_labels(args.repo, args.issue, add_labels=labels)
            print(f"✅ Updated labels for {args.repo}#{args.issue}")
        
        elif args.operation == "close":
            if not args.issue:
                print("Error: --issue required for close")
                return
            
            await bot.close_issue(args.repo, args.issue, comment=args.body)
            print(f"✅ Closed {args.repo}#{args.issue}")
        
        elif args.operation == "status":
            print(bot.format_status())
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
