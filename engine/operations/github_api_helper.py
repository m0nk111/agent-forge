"""GitHub REST API helper for agent-forge services.

This module provides a clean interface to GitHub's REST API without requiring
the gh CLI tool. Designed to work in environments without persistent home directories
(e.g., systemd DynamicUser services).

Includes anti-spam protection and rate limiting.
"""

import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

from engine.core.rate_limiter import get_rate_limiter, OperationType

logger = logging.getLogger(__name__)


class GitHubAPIHelper:
    """Helper class for GitHub REST API interactions with rate limiting."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub API helper.
        
        Args:
            token: GitHub personal access token (reads from env if not provided)
        """
        self.token = token or os.getenv("BOT_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token not provided and not found in environment")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
        
        # Get rate limiter instance
        self.rate_limiter = get_rate_limiter()
        
        logger.info("🔒 GitHub API helper initialized with rate limiting")
    
    def _update_rate_limit_from_response(self, response: requests.Response):
        """Update rate limiter from GitHub API response headers."""
        remaining = int(response.headers.get('X-RateLimit-Remaining', 5000))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if reset_time:
            self.rate_limiter.update_github_rate_limit(remaining, reset_time)
    
    def _check_rate_limit(self, operation_type: OperationType, target: str, content: Optional[str] = None) -> bool:
        """Check if operation is allowed by rate limiter."""
        allowed, reason = self.rate_limiter.check_rate_limit(operation_type, target, content)
        
        if not allowed:
            logger.warning(f"🛡️ Rate limit blocked: {reason}")
            return False
        
        return True
    
    def _record_operation(self, operation_type: OperationType, target: str, content: Optional[str] = None, success: bool = True):
        """Record operation in rate limiter."""
        self.rate_limiter.record_operation(operation_type, target, content, success)
    
    def list_issues(
        self,
        owner: str,
        repo: str,
        assignee: Optional[str] = None,
        state: str = "open",
        labels: Optional[List[str]] = None,
        per_page: int = 100
    ) -> List[Dict]:
        """List issues in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            assignee: Filter by assignee username
            state: Issue state (open, closed, all)
            labels: Filter by label names
            per_page: Results per page (max 100)
            
        Returns:
            List of issue dictionaries
        """
        target = f"{owner}/{repo}"
        
        # Check rate limit for read operations
        if not self._check_rate_limit(OperationType.API_READ, target):
            logger.warning(f"⚠️ Rate limit prevents listing issues for {target}")
            return []
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        
        params = {
            'state': state,
            'per_page': min(per_page, 100)
        }
        
        if assignee:
            params['assignee'] = assignee
        
        if labels:
            params['labels'] = ','.join(labels)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Update rate limit from response
            self._update_rate_limit_from_response(response)
            
            # Record operation
            self._record_operation(OperationType.API_READ, target, success=True)
            
            issues = response.json()
            
            # Convert to format matching gh CLI output
            formatted_issues = []
            for issue in issues:
                # Skip pull requests (they appear in issues endpoint)
                if 'pull_request' in issue:
                    continue
                
                formatted_issues.append({
                    'number': issue['number'],
                    'title': issue['title'],
                    'labels': [{'name': label['name']} for label in issue['labels']],
                    'assignees': [{'login': assignee['login']} for assignee in issue['assignees']],
                    'url': issue['html_url'],
                    'createdAt': issue['created_at'],
                    'updatedAt': issue['updated_at'],
                    'state': issue['state'],
                    'body': issue.get('body', '')
                })
            
            return formatted_issues
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list issues for {owner}/{repo}: {e}")
            raise
    
    def get_issue_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> List[Dict]:
        """Get comments for an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            List of comment dictionaries
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            comments = response.json()
            
            # Format to match gh CLI output
            formatted_comments = []
            for comment in comments:
                formatted_comments.append({
                    'author': {'login': comment['user']['login']},
                    'body': comment['body'],
                    'createdAt': comment['created_at'],
                    'updatedAt': comment['updated_at']
                })
            
            return formatted_comments
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get comments for {owner}/{repo}#{issue_number}: {e}")
            raise
    
    def create_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str
    ) -> Dict:
        """Create a comment on an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: Comment text
            
        Returns:
            Created comment dictionary
            
        Raises:
            RuntimeError: If rate limit blocks the operation
        """
        target = f"{owner}/{repo}#{issue_number}"
        
        # Check rate limit BEFORE making API call
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target, body):
            raise RuntimeError(f"Rate limit prevents comment on {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        
        try:
            response = self.session.post(
                url,
                json={'body': body},
                timeout=30
            )
            response.raise_for_status()
            
            # Update rate limit from response
            self._update_rate_limit_from_response(response)
            
            # Record successful operation
            self._record_operation(OperationType.ISSUE_COMMENT, target, body, success=True)
            
            logger.info(f"✅ Comment added to {target}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Record failed operation
            self._record_operation(OperationType.ISSUE_COMMENT, target, body, success=False)
            
            logger.error(f"Failed to comment on {owner}/{repo}#{issue_number}: {e}")
            raise
    
    def get_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> Dict:
        """Get details of a specific issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Issue dictionary
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            issue = response.json()
            
            return {
                'number': issue['number'],
                'title': issue['title'],
                'body': issue.get('body', ''),
                'state': issue['state'],
                'labels': [{'name': label['name']} for label in issue['labels']],
                'assignees': [{'login': assignee['login']} for assignee in issue['assignees']],
                'url': issue['html_url'],
                'createdAt': issue['created_at'],
                'updatedAt': issue['updated_at']
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get issue {owner}/{repo}#{issue_number}: {e}")
            raise
