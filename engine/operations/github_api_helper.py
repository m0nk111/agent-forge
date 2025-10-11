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
    
    def _check_rate_limit(
        self, 
        operation_type: OperationType, 
        target: str, 
        content: Optional[str] = None,
        bypass: bool = False
    ) -> bool:
        """
        Check if operation is allowed by rate limiter.
        
        Args:
            operation_type: Type of operation
            target: Target (repo, issue, etc.)
            content: Optional content for duplicate detection
            bypass: If True, bypass rate limits (for internal operations)
        """
        allowed, reason = self.rate_limiter.check_rate_limit(
            operation_type, target, content, bypass=bypass
        )
        
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
        per_page: int = 100,
        bypass_rate_limit: bool = False
    ) -> List[Dict]:
        """List issues in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            assignee: Filter by assignee username
            state: Issue state (open, closed, all)
            labels: Filter by label names
            per_page: Results per page (max 100)
            bypass_rate_limit: Bypass rate limits (for internal polling)
            
        Returns:
            List of issue dictionaries
        """
        target = f"{owner}/{repo}"
        
        # Check rate limit for read operations (bypass for internal polling)
        if not self._check_rate_limit(OperationType.API_READ, target, bypass=bypass_rate_limit):
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


    # ================== PR REVIEW METHODS ==================
    
    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> Dict:
        """Get pull request details.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            PR dictionary with metadata
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get PR {owner}/{repo}#{pr_number}: {e}")
            raise
    
    def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> List[Dict]:
        """Get files changed in a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            List of file change dictionaries with diffs
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get PR files {owner}/{repo}#{pr_number}: {e}")
            raise
    
    def create_pull_request_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        event: str = "COMMENT",
        comments: Optional[List[Dict]] = None
    ) -> Dict:
        """Create a pull request review.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            body: Review summary/body
            event: Review event type (APPROVE, REQUEST_CHANGES, COMMENT)
            comments: List of line-specific comments (optional)
                Format: [{'path': 'file.py', 'line': 10, 'body': 'comment', 'side': 'RIGHT'}]
        
        Returns:
            Created review dictionary
        """
        target = f"{owner}/{repo}#{pr_number}"
        
        # Check rate limit
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target, body):
            raise RuntimeError(f"Rate limit prevents review on {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        
        payload = {
            'body': body,
            'event': event
        }
        
        if comments:
            payload['comments'] = comments
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            # Update rate limit
            self._update_rate_limit_from_response(response)
            
            # Record operation
            self._record_operation(OperationType.ISSUE_COMMENT, target, body, success=True)
            
            logger.info(f"✅ Review posted to {target}: {event}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Record failed operation
            self._record_operation(OperationType.ISSUE_COMMENT, target, body, success=False)
            
            logger.error(f"Failed to post review to {owner}/{repo}#{pr_number}: {e}")
            raise
    
    def create_pull_request_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
        side: str = "RIGHT"
    ) -> Dict:
        """Create a single review comment on a specific line.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            body: Comment text
            commit_id: SHA of commit to comment on
            path: File path
            line: Line number
            side: Side of diff (RIGHT for new, LEFT for old)
            
        Returns:
            Created comment dictionary
        """
        target = f"{owner}/{repo}#{pr_number}"
        
        # Check rate limit
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target, body):
            raise RuntimeError(f"Rate limit prevents comment on {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        
        payload = {
            'body': body,
            'commit_id': commit_id,
            'path': path,
            'line': line,
            'side': side
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            # Update rate limit
            self._update_rate_limit_from_response(response)
            
            # Record operation
            self._record_operation(OperationType.ISSUE_COMMENT, target, body, success=True)
            
            logger.info(f"✅ Review comment posted to {target}:{path}:{line}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Record failed operation
            self._record_operation(OperationType.ISSUE_COMMENT, target, body, success=False)
            
            logger.error(f"Failed to post review comment to {owner}/{repo}#{pr_number}: {e}")
            raise

    def create_pull_request(self, owner: str, repo: str, title: str, body: str, 
                           head: str, base: str = "main") -> Dict:
        """Create a new pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head: Branch containing changes
            base: Target branch (default: main)
            
        Returns:
            Dict containing PR details (number, url, etc.)
            
        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        target = f"{owner}/{repo}"
        
        # Check rate limit
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target):
            logger.warning(f"⚠️ Rate limit reached, cannot create PR in {target}")
            raise RuntimeError("Rate limit exceeded for GitHub operations")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        
        payload = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            # Update rate limit
            self._update_rate_limit_from_response(response)
            
            # Record operation
            self._record_operation(OperationType.ISSUE_COMMENT, target, 
                                 f"Created PR: {title}", success=True)
            
            pr_data = response.json()
            logger.info(f"✅ PR #{pr_data['number']} created: {pr_data['html_url']}")
            return pr_data
            
        except requests.exceptions.RequestException as e:
            # Record failed operation
            self._record_operation(OperationType.ISSUE_COMMENT, target, 
                                 f"Failed to create PR: {title}", success=False)
            
            logger.error(f"Failed to create PR in {owner}/{repo}: {e}")
            raise
    
    def list_pull_requests(self, owner: str, repo: str, state: str = 'open', bypass_rate_limit: bool = False) -> List[Dict]:
        """
        List pull requests in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state filter ('open', 'closed', 'all')
            bypass_rate_limit: Bypass rate limits (for internal polling)
            
        Returns:
            List of PR dictionaries
        """
        target = f"{owner}/{repo}"
        
        if not self._check_rate_limit(OperationType.API_READ, target, bypass=bypass_rate_limit):
            raise RuntimeError(f"Rate limit exceeded for {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        params = {'state': state, 'per_page': 100}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            self._update_rate_limit_from_response(response)
            
            self._record_operation(OperationType.API_READ, target,
                                 f"Listed {state} PRs", success=True)
            
            prs = response.json()
            logger.debug(f"🔍 Retrieved {len(prs)} {state} PRs from {target}")
            return prs
            
        except requests.exceptions.RequestException as e:
            self._record_operation(OperationType.API_READ, target,
                                 f"Failed to list PRs", success=False)
            logger.error(f"Failed to list PRs in {target}: {e}")
            raise

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict:
        """
        Get pull request details.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            Dict with PR details
        """
        target = f"{owner}/{repo}"
        
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target):
            raise RuntimeError(f"Rate limit exceeded for {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            self._update_rate_limit_from_response(response)
            
            pr_data = response.json()
            logger.info(f"✅ Fetched PR #{pr_number}: {pr_data['title']}")
            return pr_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch PR #{pr_number} from {owner}/{repo}: {e}")
            raise

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Get files changed in a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            List of file change dicts
        """
        target = f"{owner}/{repo}"
        
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target):
            raise RuntimeError(f"Rate limit exceeded for {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            self._update_rate_limit_from_response(response)
            
            files = response.json()
            logger.info(f"✅ Fetched {len(files)} changed files from PR #{pr_number}")
            return files
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch PR files from {owner}/{repo}#{pr_number}: {e}")
            raise

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """
        Get unified diff for a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            Diff string
        """
        target = f"{owner}/{repo}"
        
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target):
            raise RuntimeError(f"Rate limit exceeded for {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.session.headers, "Accept": "application/vnd.github.v3.diff"}
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            self._update_rate_limit_from_response(response)
            
            diff = response.text
            logger.info(f"✅ Fetched diff for PR #{pr_number} ({len(diff)} bytes)")
            return diff
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch PR diff from {owner}/{repo}#{pr_number}: {e}")
            raise

    def add_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict:
        """
        Add a general comment to a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            body: Comment text
            
        Returns:
            Dict with comment details
        """
        target = f"{owner}/{repo}"
        
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target):
            raise RuntimeError(f"Rate limit exceeded for {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = {"body": body}
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            self._update_rate_limit_from_response(response)
            
            self._record_operation(OperationType.ISSUE_COMMENT, target,
                                 f"Posted comment on PR #{pr_number}", success=True)
            
            comment_data = response.json()
            logger.info(f"✅ Posted comment on PR #{pr_number}")
            return comment_data
            
        except requests.exceptions.RequestException as e:
            self._record_operation(OperationType.ISSUE_COMMENT, target,
                                 f"Failed to post comment on PR #{pr_number}", success=False)
            logger.error(f"Failed to post PR comment to {owner}/{repo}#{pr_number}: {e}")
            raise

    def submit_pr_review(self, owner: str, repo: str, pr_number: int, 
                        event: str, body: str, commit_id: Optional[str] = None) -> Dict:
        """
        Submit a pull request review.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            event: Review event (APPROVE, REQUEST_CHANGES, COMMENT)
            body: Review body text
            commit_id: Optional specific commit SHA to review
            
        Returns:
            Dict with review details
        """
        target = f"{owner}/{repo}"
        
        if not self._check_rate_limit(OperationType.ISSUE_COMMENT, target):
            raise RuntimeError(f"Rate limit exceeded for {target}")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "body": body if body else "Automated review",  # GitHub requires non-empty body
            "event": event
        }
        
        if commit_id:
            payload["commit_id"] = commit_id
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            self._update_rate_limit_from_response(response)
            
            self._record_operation(OperationType.ISSUE_COMMENT, target,
                                 f"Submitted {event} review on PR #{pr_number}", success=True)
            
            review_data = response.json()
            logger.info(f"✅ Submitted {event} review on PR #{pr_number}")
            return review_data
            
        except requests.exceptions.RequestException as e:
            # Log response body for debugging 422 errors
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"GitHub API error details: {error_detail}")
                except:
                    logger.error(f"GitHub API error response: {e.response.text}")
            
            self._record_operation(OperationType.ISSUE_COMMENT, target,
                                 f"Failed to submit review on PR #{pr_number}", success=False)
            logger.error(f"Failed to submit PR review to {owner}/{repo}#{pr_number}: {e}")
            raise
    
    # ========================================
    # Repository Management Methods
    # ========================================
    
    def create_repository(self, name: str, description: str = "", 
                         private: bool = False, organization: Optional[str] = None,
                         auto_init: bool = True, gitignore_template: Optional[str] = None,
                         license_template: Optional[str] = None) -> Dict:
        """Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether repository should be private
            organization: Organization name (creates user repo if None)
            auto_init: Initialize with README.md
            gitignore_template: .gitignore template (e.g., 'Python', 'Node')
            license_template: License template (e.g., 'mit', 'apache-2.0')
            
        Returns:
            Repository data from GitHub API
            
        Raises:
            requests.RequestException: On API error
        """
        target = f"{organization or 'user'}/{name}"
        
        # Check rate limit first
        if not self._check_rate_limit(OperationType.REPOSITORY_ACTION, target):
            raise RuntimeError(f"⏳ Rate limit reached for repository creation")
        
        # Build request payload
        payload = {
            'name': name,
            'description': description,
            'private': private,
            'auto_init': auto_init
        }
        
        if gitignore_template:
            payload['gitignore_template'] = gitignore_template
        if license_template:
            payload['license_template'] = license_template
        
        # Choose endpoint based on organization
        if organization:
            url = f"{self.BASE_URL}/orgs/{organization}/repos"
        else:
            url = f"{self.BASE_URL}/user/repos"
        
        try:
            logger.info(f"🔨 Creating repository: {target}")
            response = self.session.post(url, json=payload)
            self._update_rate_limit_from_response(response)
            response.raise_for_status()
            
            repo_data = response.json()
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Created repository {name}")
            logger.info(f"✅ Repository created: {repo_data['html_url']}")
            return repo_data
            
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 422:
                    logger.error(f"❌ Repository creation failed: {e.response.text}")
            
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Failed to create repository {name}", success=False)
            logger.error(f"Failed to create repository {target}: {e}")
            raise
    
    def add_collaborator(self, owner: str, repo: str, username: str, 
                        permission: str = "push") -> bool:
        """Add a collaborator to a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            username: GitHub username to add
            permission: Permission level ('pull', 'push', 'admin', 'maintain', 'triage')
            
        Returns:
            True if successful
            
        Raises:
            requests.RequestException: On API error
        """
        target = f"{owner}/{repo}"
        
        # Check rate limit first
        if not self._check_rate_limit(OperationType.REPOSITORY_ACTION, target):
            raise RuntimeError(f"⏳ Rate limit reached for collaborator management")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/collaborators/{username}"
        payload = {'permission': permission}
        
        try:
            logger.info(f"👥 Adding collaborator {username} to {target} ({permission})")
            response = self.session.put(url, json=payload)
            self._update_rate_limit_from_response(response)
            response.raise_for_status()
            
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Added collaborator {username}")
            logger.info(f"✅ Collaborator {username} added to {target}")
            return True
            
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ Failed to add collaborator: {e.response.text}")
            
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Failed to add collaborator {username}", success=False)
            logger.error(f"Failed to add collaborator {username} to {target}: {e}")
            raise
    
    def list_repository_invitations(self) -> List[Dict]:
        """List pending repository invitations for authenticated user.
        
        Returns:
            List of invitation dictionaries
            
        Raises:
            requests.RequestException: On API error
        """
        target = "user/invitations"
        
        # Check rate limit first
        if not self._check_rate_limit(OperationType.REPOSITORY_ACTION, target):
            raise RuntimeError(f"⏳ Rate limit reached for invitation listing")
        
        url = f"{self.BASE_URL}/user/repository_invitations"
        
        try:
            logger.info(f"📬 Fetching repository invitations")
            response = self.session.get(url)
            self._update_rate_limit_from_response(response)
            response.raise_for_status()
            
            invitations = response.json()
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Listed {len(invitations)} invitations")
            logger.info(f"✅ Found {len(invitations)} pending invitations")
            return invitations
            
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ Failed to list invitations: {e.response.text}")
            
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 "Failed to list invitations", success=False)
            logger.error(f"Failed to list repository invitations: {e}")
            raise
    
    def accept_repository_invitation(self, invitation_id: int) -> bool:
        """Accept a repository invitation.
        
        Args:
            invitation_id: Invitation ID from list_repository_invitations()
            
        Returns:
            True if successful
            
        Raises:
            requests.RequestException: On API error
        """
        target = f"invitation/{invitation_id}"
        
        # Check rate limit first
        if not self._check_rate_limit(OperationType.REPOSITORY_ACTION, target):
            raise RuntimeError(f"⏳ Rate limit reached for invitation acceptance")
        
        url = f"{self.BASE_URL}/user/repository_invitations/{invitation_id}"
        
        try:
            logger.info(f"✉️ Accepting repository invitation {invitation_id}")
            response = self.session.patch(url)
            self._update_rate_limit_from_response(response)
            response.raise_for_status()
            
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Accepted invitation {invitation_id}")
            logger.info(f"✅ Invitation {invitation_id} accepted")
            return True
            
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ Failed to accept invitation: {e.response.text}")
            
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Failed to accept invitation {invitation_id}", success=False)
            logger.error(f"Failed to accept invitation {invitation_id}: {e}")
            raise
    
    def update_branch_protection(self, owner: str, repo: str, branch: str,
                                required_reviews: int = 1,
                                enforce_admins: bool = False,
                                require_code_owner_reviews: bool = False) -> Dict:
        """Configure branch protection rules.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (e.g., 'main', 'master')
            required_reviews: Number of required approving reviews
            enforce_admins: Enforce protections for administrators
            require_code_owner_reviews: Require CODEOWNERS review
            
        Returns:
            Branch protection data
            
        Raises:
            requests.RequestException: On API error
        """
        target = f"{owner}/{repo}:{branch}"
        
        # Check rate limit first
        if not self._check_rate_limit(OperationType.REPOSITORY_ACTION, target):
            raise RuntimeError(f"⏳ Rate limit reached for branch protection")
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/branches/{branch}/protection"
        
        payload = {
            'required_status_checks': None,  # Can be configured later
            'enforce_admins': enforce_admins,
            'required_pull_request_reviews': {
                'required_approving_review_count': required_reviews,
                'require_code_owner_reviews': require_code_owner_reviews,
                'dismiss_stale_reviews': True
            },
            'restrictions': None  # No push restrictions
        }
        
        try:
            logger.info(f"🔒 Configuring branch protection for {target}")
            response = self.session.put(url, json=payload)
            self._update_rate_limit_from_response(response)
            response.raise_for_status()
            
            protection_data = response.json()
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Updated branch protection for {branch}")
            logger.info(f"✅ Branch protection configured for {target}")
            return protection_data
            
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ Branch protection failed: {e.response.text}")
            
            self._record_operation(OperationType.REPOSITORY_ACTION, target,
                                 f"Failed to update branch protection", success=False)
            logger.error(f"Failed to configure branch protection for {target}: {e}")
            raise


