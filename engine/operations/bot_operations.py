"""
GitHub bot operations for issues, PRs, and project management.

This module provides BotOperations class for administrative tasks:
- Create and manage issues
- Create and manage pull requests
- Add labels and milestones
- Post comments and reviews

Separate from GitOperations to maintain security:
- BotOperations: No code write access (Triage role)
- GitOperations: Code commits only (Write role)

Usage:
    from bot_operations import BotOperations
    
    bot = BotOperations()
    bot.create_issue('agent-forge', 'Bug report', 'Description...')
"""

import os
import requests
from typing import Optional, List, Dict, Any
from engine.core.account_manager import get_bot_account, get_account_manager


class BotOperations:
    """Handle GitHub administrative operations via bot account."""
    
    def __init__(self, username: Optional[str] = None):
        """
        Initialize with bot credentials.
        
        Args:
            username: Optional specific account username (defaults to default bot account)
        """
        # Get account from centralized config
        manager = get_account_manager()
        
        if username:
            account = manager.get_account(username)
            if not account:
                raise ValueError(f"Account {username} not found in github_accounts.yaml")
        else:
            account = manager.get_default_bot_account()
            if not account:
                raise ValueError("No default bot account configured in github_accounts.yaml")
        
        self.username = account.username
        self.email = account.email
        self.token = account.token
        self.owner = manager.get_repository_owner()
        
        if not self.token:
            raise ValueError(
                f"No GitHub token found for {self.username}.\n"
                f"Set {account.token_env} in environment or create {account.token_file}"
            )
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
    
    def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new issue.
        
        Args:
            repo: Repository name (e.g., 'agent-forge')
            title: Issue title
            body: Issue description (markdown supported)
            labels: Optional list of label names
            assignees: Optional list of usernames to assign
            
        Returns:
            Issue data dict or None on error
        """
        url = f'https://api.github.com/repos/{self.owner}/{repo}/issues'
        
        payload = {
            'title': title,
            'body': body
        }
        
        if labels:
            payload['labels'] = labels
        if assignees:
            payload['assignees'] = assignees
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            issue = response.json()
            print(f"✅ Created issue #{issue['number']}: {title}")
            print(f"   URL: {issue['html_url']}")
            return issue
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create issue: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Response: {e.response.text}")
            return None
    
    def update_issue(
        self,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing issue.
        
        Args:
            repo: Repository name
            issue_number: Issue number
            title: New title (optional)
            body: New body (optional)
            state: 'open' or 'closed' (optional)
            labels: New labels list (optional)
            
        Returns:
            Updated issue data or None on error
        """
        url = f'https://api.github.com/repos/{self.owner}/{repo}/issues/{issue_number}'
        
        payload = {}
        if title:
            payload['title'] = title
        if body:
            payload['body'] = body
        if state:
            payload['state'] = state
        if labels:
            payload['labels'] = labels
        
        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            issue = response.json()
            print(f"✅ Updated issue #{issue_number}")
            return issue
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to update issue: {e}")
            return None
    
    def add_comment(
        self,
        repo: str,
        issue_number: int,
        comment: str
    ) -> Optional[Dict[str, Any]]:
        """
        Add comment to issue or PR.
        
        Args:
            repo: Repository name
            issue_number: Issue or PR number
            comment: Comment text (markdown supported)
            
        Returns:
            Comment data or None on error
        """
        url = f'https://api.github.com/repos/{self.owner}/{repo}/issues/{issue_number}/comments'
        
        payload = {'body': comment}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            comment_data = response.json()
            print(f"✅ Added comment to #{issue_number}")
            return comment_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to add comment: {e}")
            return None
    
    def list_issues(
        self,
        repo: str,
        state: str = 'open',
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        List issues in repository.
        
        Args:
            repo: Repository name
            state: 'open', 'closed', or 'all'
            labels: Filter by labels
            assignee: Filter by assignee username
            
        Returns:
            List of issue dicts or None on error
        """
        url = f'https://api.github.com/repos/{self.owner}/{repo}/issues'
        
        params = {'state': state}
        if labels:
            params['labels'] = ','.join(labels)
        if assignee:
            params['assignee'] = assignee
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            issues = response.json()
            print(f"✅ Found {len(issues)} issues ({state})")
            return issues
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to list issues: {e}")
            return None
    
    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = 'main'
    ) -> Optional[Dict[str, Any]]:
        """
        Create a pull request.
        
        Args:
            repo: Repository name
            title: PR title
            body: PR description
            head: Branch with changes
            base: Branch to merge into (default: main)
            
        Returns:
            PR data or None on error
        """
        url = f'https://api.github.com/repos/{self.owner}/{repo}/pulls'
        
        payload = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            pr = response.json()
            print(f"✅ Created PR #{pr['number']}: {title}")
            print(f"   URL: {pr['html_url']}")
            return pr
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create PR: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Response: {e.response.text}")
            return None
    
    def add_labels(
        self,
        repo: str,
        issue_number: int,
        labels: List[str]
    ) -> bool:
        """
        Add labels to issue or PR.
        
        Args:
            repo: Repository name
            issue_number: Issue or PR number
            labels: List of label names to add
            
        Returns:
            True on success, False on error
        """
        url = f'https://api.github.com/repos/{self.owner}/{repo}/issues/{issue_number}/labels'
        
        payload = {'labels': labels}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            print(f"✅ Added labels to #{issue_number}: {', '.join(labels)}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to add labels: {e}")
            return False
    
    def close_issue(self, repo: str, issue_number: int, comment: Optional[str] = None) -> bool:
        """
        Close an issue with optional comment.
        
        Args:
            repo: Repository name
            issue_number: Issue number
            comment: Optional closing comment
            
        Returns:
            True on success, False on error
        """
        if comment:
            self.add_comment(repo, issue_number, comment)
        
        result = self.update_issue(repo, issue_number, state='closed')
        if result:
            print(f"✅ Closed issue #{issue_number}")
            return True
        return False


if __name__ == '__main__':
    """Test bot operations."""
    import sys
    
    # Test configuration
    try:
        bot = BotOperations()
        print(f"✅ BotOperations initialized")
        print(f"   Username: {bot.username}")
        print(f"   Email: {bot.email}")
        print(f"   Token: {bot.token[:20]}... (hidden)")
        print(f"   Owner: {bot.owner}")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Test listing issues
    print(f"\n📋 Testing issue listing...")
    issues = bot.list_issues('agent-forge', state='all')
    if issues is not None:
        print(f"✅ API connection working")
        if issues:
            print(f"   Latest issue: #{issues[0]['number']} - {issues[0]['title']}")
    else:
        print(f"⚠️  Could not fetch issues (check token permissions)")
