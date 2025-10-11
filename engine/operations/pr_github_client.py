"""GitHub API operations for PR Review Agent.

Handles all GitHub API interactions including:
- PR details and file changes
- Comments and labels
- Reviewer assignments
- PR state management
"""

import logging
import time
from typing import Dict, List, Optional, Tuple

import requests


logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """Handles GitHub API requests with retry and rate limiting."""
    
    def __init__(self, github_token: str):
        """Initialize GitHub API client.
        
        Args:
            github_token: GitHub personal access token
        """
        self.github_token = github_token
        self.base_url = "https://api.github.com"
    
    def request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Tuple[int, Optional[Dict]]:
        """Make GitHub API request with rate limit handling.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Full API URL
            json_data: Optional JSON payload
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (status_code, response_data)
        """
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                if method.upper() == "GET":
                    resp = requests.get(url, headers=headers, timeout=30)
                elif method.upper() == "POST":
                    resp = requests.post(url, headers=headers, json=json_data, timeout=30)
                elif method.upper() == "PATCH":
                    resp = requests.patch(url, headers=headers, json=json_data, timeout=30)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return (400, None)
                
                # Handle rate limiting
                if resp.status_code == 403 and 'X-RateLimit-Remaining' in resp.headers:
                    if int(resp.headers['X-RateLimit-Remaining']) == 0:
                        reset_time = int(resp.headers.get('X-RateLimit-Reset', 0))
                        wait_time = max(reset_time - time.time(), 0) + 1
                        logger.warning(f"Rate limit exceeded. Waiting {wait_time}s")
                        time.sleep(wait_time)
                        retry_count += 1
                        continue
                
                # Retry on server errors
                if resp.status_code >= 500:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count
                        logger.warning(f"Server error {resp.status_code}. Retrying in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                
                # Parse response
                try:
                    data = resp.json() if resp.text else None
                except Exception:
                    data = None
                
                return (resp.status_code, data)
                
            except Exception as e:
                logger.error(f"Request failed: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)
                    continue
                return (500, None)
        
        return (500, None)
    
    def get_pr_details(self, repo: str, pr_number: int) -> Optional[Dict]:
        """Get PR details from GitHub.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            
        Returns:
            PR details dict or None if failed
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        status, data = self.request("GET", url)
        
        if status == 200:
            return data
        
        logger.error(f"Failed to get PR details: {status}")
        return None
    
    def get_changed_files(self, repo: str, pr_number: int) -> List[Dict]:
        """Get list of changed files in PR.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            
        Returns:
            List of file change dictionaries
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"
        status, data = self.request("GET", url)
        
        if status == 200 and isinstance(data, list):
            return data
        
        logger.error(f"Failed to get changed files: {status}")
        return []
    
    def add_comment(self, repo: str, pr_number: int, comment: str) -> bool:
        """Add comment to PR.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            comment: Comment text
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
        status, _ = self.request("POST", url, {"body": comment})
        
        if status == 201:
            logger.info(f"✅ Comment posted to PR #{pr_number}")
            return True
        
        logger.error(f"Failed to post comment: {status}")
        return False
    
    def add_labels(self, repo: str, pr_number: int, labels: List[str]) -> bool:
        """Add labels to PR.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            labels: List of label names
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/labels"
        status, _ = self.request("POST", url, {"labels": labels})
        
        if status == 200:
            logger.info(f"✅ Labels {labels} added to PR #{pr_number}")
            return True
        
        logger.error(f"Failed to add labels: {status}")
        return False
    
    def remove_label(self, repo: str, pr_number: int, label: str) -> bool:
        """Remove label from PR.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            label: Label name to remove
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/labels/{label}"
        status, _ = self.request("DELETE", url)
        
        if status in (200, 204):
            logger.info(f"✅ Label '{label}' removed from PR #{pr_number}")
            return True
        
        logger.error(f"Failed to remove label: {status}")
        return False
    
    def assign_reviewers(self, repo: str, pr_number: int, reviewers: List[str]) -> bool:
        """Request reviewers for PR.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            reviewers: List of GitHub usernames
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/requested_reviewers"
        status, _ = self.request("POST", url, {"reviewers": reviewers})
        
        if status == 201:
            logger.info(f"✅ Reviewers {reviewers} requested for PR #{pr_number}")
            return True
        
        logger.error(f"Failed to request reviewers: {status}")
        return False
    
    def update_assignees(self, repo: str, pr_number: int, assignees: List[str]) -> bool:
        """Update PR assignees.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            assignees: List of GitHub usernames
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}"
        status, _ = self.request("PATCH", url, {"assignees": assignees})
        
        if status == 200:
            logger.info(f"✅ Assignees updated for PR #{pr_number}")
            return True
        
        logger.error(f"Failed to update assignees: {status}")
        return False
    
    def convert_to_draft(self, repo: str, pr_number: int) -> bool:
        """Convert PR to draft status.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            
        Returns:
            True if successful
        """
        # Get PR node ID first
        pr_details = self.get_pr_details(repo, pr_number)
        if not pr_details or 'node_id' not in pr_details:
            logger.error("Failed to get PR node ID")
            return False
        
        # Use GraphQL API for draft conversion
        graphql_url = f"{self.base_url}/graphql"
        query = {
            "query": f"""
            mutation {{
              convertPullRequestToDraft(input: {{pullRequestId: "{pr_details['node_id']}"}}) {{
                pullRequest {{
                  isDraft
                }}
              }}
            }}
            """
        }
        
        status, data = self.request("POST", graphql_url, query)
        
        if status == 200:
            logger.info(f"✅ PR #{pr_number} converted to draft")
            return True
        
        logger.error(f"Failed to convert to draft: {status}")
        return False
    
    def mark_ready_for_review(self, repo: str, pr_number: int) -> bool:
        """Mark draft PR as ready for review.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            
        Returns:
            True if successful
        """
        # Get PR node ID first
        pr_details = self.get_pr_details(repo, pr_number)
        if not pr_details or 'node_id' not in pr_details:
            logger.error("Failed to get PR node ID")
            return False
        
        # Use GraphQL API
        graphql_url = f"{self.base_url}/graphql"
        query = {
            "query": f"""
            mutation {{
              markPullRequestReadyForReview(input: {{pullRequestId: "{pr_details['node_id']}"}}) {{
                pullRequest {{
                  isDraft
                }}
              }}
            }}
            """
        }
        
        status, data = self.request("POST", graphql_url, query)
        
        if status == 200:
            logger.info(f"✅ PR #{pr_number} marked ready for review")
            return True
        
        logger.error(f"Failed to mark ready: {status}")
        return False
    
    def merge_pull_request(
        self,
        repo: str,
        pr_number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        merge_method: str = "squash"
    ) -> bool:
        """Merge pull request.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            commit_title: Optional merge commit title
            commit_message: Optional merge commit message
            merge_method: Merge method (merge, squash, rebase)
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/merge"
        
        payload = {"merge_method": merge_method}
        if commit_title:
            payload["commit_title"] = commit_title
        if commit_message:
            payload["commit_message"] = commit_message
        
        status, data = self.request("PUT", url, payload)
        
        if status == 200:
            logger.info(f"✅ PR #{pr_number} merged successfully")
            return True
        
        logger.error(f"Failed to merge PR: {status}")
        if data and 'message' in data:
            logger.error(f"Error: {data['message']}")
        
        return False
    
    def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Optional[int]:
        """Create new issue.
        
        Args:
            repo: Repository in format "owner/repo"
            title: Issue title
            body: Issue body
            labels: Optional list of labels
            assignees: Optional list of assignees
            
        Returns:
            Issue number if successful, None otherwise
        """
        url = f"{self.base_url}/repos/{repo}/issues"
        
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        
        status, data = self.request("POST", url, payload)
        
        if status == 201 and data and 'number' in data:
            logger.info(f"✅ Issue #{data['number']} created")
            return data['number']
        
        logger.error(f"Failed to create issue: {status}")
        return None
