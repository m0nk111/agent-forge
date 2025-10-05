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
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import requests

logger = logging.getLogger(__name__)


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
    state_file: str = "/opt/agent-forge/data/polling_state.json"
    
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


class GitHubAPI:
    """Helper class for GitHub REST API calls."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str):
        """Initialize with GitHub token.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
    
    def get_issues(self, owner: str, repo: str, assignee: str, state: str = 'open', per_page: int = 100) -> List[Dict]:
        """Get issues from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            assignee: Filter by assignee
            state: Issue state (open/closed)
            per_page: Results per page
            
        Returns:
            List of issue dictionaries
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        params = {
            'assignee': assignee,
            'state': state,
            'per_page': per_page
        }
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict]:
        """Get comments for an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            List of comment dictionaries
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> Dict:
        """Create a comment on an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: Comment body
            
        Returns:
            Created comment dictionary
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = {'body': body}
        response = self.session.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()


class PollingService:
    """Service for autonomous GitHub issue polling and workflow initiation."""
    
    def __init__(self, config: PollingConfig):
        """Initialize polling service.
        
        Args:
            config: Polling configuration
        """
        self.config = config
        self.state_file = Path(config.state_file)
        self.state: Dict[str, IssueState] = {}
        
        # Initialize GitHub API client
        if not config.github_token:
            raise ValueError("GitHub token is required. Set BOT_GITHUB_TOKEN or GITHUB_TOKEN environment variable.")
        self.github_api = GitHubAPI(config.github_token)
        
        # Metrics tracking
        self.api_calls = 0
        
        self.load_state()
        self.running = False
        
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
        """Check for issues assigned to the bot.
        
        Returns:
            List of assigned issue dictionaries
        """
        logger.info("Checking for assigned issues...")
        all_issues = []
        max_retries = 3
        retry_delay = 2
        
        for repo in self.config.repositories:
            owner, repo_name = repo.split('/')
            
            for attempt in range(max_retries):
                try:
                    # Use GitHub REST API to query issues
                    issues = self.github_api.get_issues(
                        owner=owner,
                        repo=repo_name,
                        assignee=self.config.github_username,
                        state='open',
                        per_page=100
                    )
                    
                    # Increment API call counter
                    self.api_calls += 1
                    
                    # Transform API response to match expected format
                    for issue in issues:
                        issue['repository'] = repo
                        issue['createdAt'] = issue.get('created_at')
                        issue['updatedAt'] = issue.get('updated_at')
                    
                    all_issues.extend(issues)
                    logger.info(f"Found {len(issues)} assigned issues in {repo}")
                    break  # Success, exit retry loop
                    
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout querying {repo} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Max retries exceeded for {repo} (timeout)")
                        
                except requests.exceptions.HTTPError as e:
                    logger.error(f"HTTP error querying {repo}: {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                    if 'authentication' in str(e).lower() or 'token' in str(e).lower():
                        logger.error("Authentication error - skipping retries")
                        break
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Max retries exceeded for {repo}")
                        
                except Exception as e:
                    logger.error(f"Error checking {repo}: {type(e).__name__}: {e} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Max retries exceeded for {repo} (unexpected error)")
        
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
        """Check if an issue is already claimed by another agent.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            
        Returns:
            True if issue is claimed by another agent, False otherwise
        """
        try:
            owner, repo_name = repo.split('/')
            
            # Query issue comments using GitHub REST API
            comments = self.github_api.get_issue_comments(
                owner=owner,
                repo=repo_name,
                issue_number=issue_number
            )
            
            if not comments:
                return False
            
            # Check for agent claim comments
            now = datetime.utcnow()
            timeout = timedelta(minutes=self.config.claim_timeout_minutes)
            
            for comment in comments:
                body = comment.get('body', '')
                if '🤖 Agent' in body and 'started working on this issue' in body:
                    # Check timestamp
                    try:
                        created_at_str = comment.get('created_at', '')
                        created_at = datetime.fromisoformat(
                            created_at_str.replace('Z', '+00:00')
                        )
                        if now - created_at.replace(tzinfo=None) < timeout:
                            logger.info(f"Issue {repo}#{issue_number} claimed by another agent")
                            return True
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Could not parse comment timestamp: {type(e).__name__}: {e}")
                        continue
            
            return False
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout checking claim status for {repo}#{issue_number}")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error checking claim status for {repo}#{issue_number}: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Error checking claim status for {repo}#{issue_number}: {type(e).__name__}: {e}")
            return False
    
    async def claim_issue(self, repo: str, issue_number: int) -> bool:
        """Claim an issue by adding a comment.
        
        Args:
            repo: Repository (owner/repo)
            issue_number: Issue number
            
        Returns:
            True if successfully claimed
        """
        max_retries = 3
        retry_delay = 2
        owner, repo_name = repo.split('/')
        
        for attempt in range(max_retries):
            try:
                comment = f"🤖 Agent **{self.config.github_username}** started working on this issue at {datetime.utcnow().isoformat()}Z"
                
                # Use GitHub REST API to create comment
                self.github_api.create_issue_comment(
                    owner=owner,
                    repo=repo_name,
                    issue_number=issue_number,
                    body=comment
                )
                
                logger.info(f"Claimed issue {repo}#{issue_number}")
                return True
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout claiming {repo}#{issue_number} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Max retries exceeded claiming {repo}#{issue_number} (timeout)")
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error claiming {repo}#{issue_number}: {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Max retries exceeded claiming {repo}#{issue_number}")
                    
            except Exception as e:
                logger.error(f"Unexpected error claiming {repo}#{issue_number}: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Max retries exceeded claiming {repo}#{issue_number} (unexpected error)")
        
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
            from agents.qwen_agent import QwenAgent
            
            # Get or create QwenAgent instance
            # In production, this would be the already-running agent
            qwen = QwenAgent(
                project_root="/opt/agent-forge",
                model="qwen2.5-coder:32b",
                base_url="http://localhost:11434"
            )
            
            # Start issue handler with agent
            handler = IssueHandler(agent=qwen)
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
        
        try:
            # Check assigned issues
            issues = await self.check_assigned_issues()
            
            # Filter actionable
            actionable = self.filter_actionable_issues(issues)
            
            if not actionable:
                logger.info("No actionable issues found")
                return
            
            # Check capacity
            processing_count = self.get_processing_count()
            available_slots = self.config.max_concurrent_issues - processing_count
            
            if available_slots <= 0:
                logger.info(f"At max capacity ({self.config.max_concurrent_issues} concurrent issues)")
                return
            
            # Start workflows for available slots
            for issue in actionable[:available_slots]:
                await self.start_issue_workflow(issue)
                # Small delay between starts
                await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in polling cycle: {e}")
        finally:
            # Cleanup old state
            self.cleanup_old_state()
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
