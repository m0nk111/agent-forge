"""
PR Review Agent - Automated code review for pull requests.

This module provides automated code review capabilities for PRs created by bot accounts.
It performs:
- Code quality analysis (static + optional LLM)
- Test coverage verification
- Style compliance checks
- Security scanning
- Detailed PR comments with actionable feedback

Review Modes:
- Static Analysis: Fast, deterministic, zero cost
- LLM-Powered: Deep insights, context-aware, uses Ollama
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from engine.utils.review_lock import ReviewLock
from engine.operations.pr_review_logic import ReviewLogic
from engine.operations.pr_github_client import GitHubAPIClient
from engine.operations.pr_workflow_orchestrator import WorkflowOrchestrator


logger = logging.getLogger(__name__)


class PRReviewAgent:
    """Automated code review agent for pull requests."""
    
    def __init__(
        self, 
        project_root: Optional[str] = None, 
        github_token: Optional[str] = None,
        use_llm: bool = False,
        llm_model: str = "qwen2.5-coder:7b",
        bot_account: str = "post"  # Default to 'post' - only account that exists
    ):
        """
        Initialize PR Review Agent.
        
        Args:
            project_root: Root directory of the project
            github_token: GitHub personal access token (optional, will try to load from secrets)
            use_llm: Enable LLM-powered code review via Ollama
            llm_model: LLM model to use (default: qwen2.5-coder:7b)
            bot_account: Bot account to use ('post', 'reviewer', 'coder1', etc.)
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path(__file__).parent.parent.parent
        
        self.bot_account = bot_account
        
        # GitHub authentication
        if github_token:
            self.github_token = github_token
        else:
            self.github_token = self._load_github_token()
        
        # Initialize GitHub API client
        self.github_client = GitHubAPIClient(
            github_token=self.github_token
        )
        
        # Initialize review logic
        self.review_logic = ReviewLogic(
            use_llm=use_llm,
            llm_model=llm_model,
            ollama_url="http://localhost:11434/api/generate"
        )
        
        # LLM configuration (keep for backwards compatibility)
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Review lock for preventing concurrent reviews
        self.review_lock = ReviewLock(
            lock_dir=str(self.project_root / "data" / "review_locks"),
            lock_timeout=300  # 5 minutes
        )
        
        # Initialize workflow orchestrator
        self.workflow_orchestrator = WorkflowOrchestrator(
            review_agent=self,
            github_client=self.github_client,
            review_lock=self.review_lock,
            bot_account=bot_account
        )
    
    def _load_github_token(self) -> str:
        """Load GitHub token from secrets."""
        # Handle 'admin' alias - use m0nk111.token for admin
        if self.bot_account == 'admin':
            token_path = self.project_root / 'secrets' / 'agents' / 'm0nk111.token'
        else:
            token_path = self.project_root / 'secrets' / 'agents' / f'm0nk111-{self.bot_account}.token'
        
        if not token_path.exists():
            raise FileNotFoundError(f"GitHub token not found: {token_path}")
        
        return token_path.read_text().strip()
    
    def _github_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Tuple[int, Optional[Dict]]:
        """
        Make GitHub API request with rate limit handling.
        
        Features:
        - Detects 403 (forbidden, often rate limit) and 429 (too many requests)
        - Respects X-RateLimit-Remaining and X-RateLimit-Reset headers
        - Implements exponential backoff for retries
        - Logs rate limit information for monitoring
        
        Args:
            method: HTTP method (GET, POST, PATCH, PUT, DELETE)
            url: API endpoint URL
            json_data: Optional JSON data for request body
            max_retries: Maximum retry attempts (default: 3)
        
        Returns:
            Tuple of (status_code, response_json)
        """
        import time
        
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        retry_count = 0
        base_wait = 5  # Base wait time in seconds
        
        while retry_count <= max_retries:
            try:
                # Make request
                if method == 'GET':
                    resp = requests.get(url, headers=headers)
                elif method == 'POST':
                    resp = requests.post(url, headers=headers, json=json_data)
                elif method == 'PATCH':
                    resp = requests.patch(url, headers=headers, json=json_data)
                elif method == 'PUT':
                    resp = requests.put(url, headers=headers, json=json_data)
                elif method == 'DELETE':
                    resp = requests.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                # Check rate limit headers
                rate_limit_remaining = resp.headers.get('X-RateLimit-Remaining')
                rate_limit_reset = resp.headers.get('X-RateLimit-Reset')
                
                # Log rate limit info if getting low
                if rate_limit_remaining:
                    remaining = int(rate_limit_remaining)
                    if remaining < 100:
                        logger.warning(f"⚠️  GitHub API rate limit low: {remaining} requests remaining")
                        if rate_limit_reset:
                            reset_time = int(rate_limit_reset)
                            wait_seconds = reset_time - int(time.time())
                            if wait_seconds > 0:
                                logger.warning(f"   Rate limit resets in {wait_seconds}s")
                
                # Handle rate limit responses
                if resp.status_code == 429:  # Too Many Requests
                    retry_after = int(resp.headers.get('Retry-After', 60))
                    logger.error(f"❌ GitHub API rate limited (429): Retry after {retry_after}s")
                    
                    if retry_count < max_retries:
                        logger.info(f"⏳ Waiting {retry_after}s before retry {retry_count + 1}/{max_retries}...")
                        time.sleep(retry_after)
                        retry_count += 1
                        continue
                    else:
                        logger.error("❌ Max retries reached, giving up")
                        return 429, None
                
                elif resp.status_code == 403:  # Forbidden (possibly rate limit)
                    # Check if it's rate limit related
                    if rate_limit_remaining and int(rate_limit_remaining) == 0:
                        if rate_limit_reset:
                            reset_time = int(rate_limit_reset)
                            wait_seconds = max(0, reset_time - int(time.time()))
                            logger.error(f"❌ GitHub API rate limit exceeded (403): Resets in {wait_seconds}s")
                            
                            if retry_count < max_retries:
                                # Wait until reset + small buffer
                                wait_time = wait_seconds + 5
                                logger.info(f"⏳ Waiting {wait_time}s for rate limit reset (retry {retry_count + 1}/{max_retries})...")
                                time.sleep(wait_time)
                                retry_count += 1
                                continue
                    
                    # Not rate limit related, don't retry
                    logger.error(f"❌ GitHub API forbidden (403): {url}")
                    return 403, None
                
                # Handle other errors with exponential backoff
                elif resp.status_code >= 500:  # Server errors
                    if retry_count < max_retries:
                        wait_time = base_wait * (2 ** retry_count)  # Exponential backoff
                        logger.warning(f"⚠️  GitHub API server error ({resp.status_code}): Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        retry_count += 1
                        continue
                    else:
                        logger.error(f"❌ Max retries reached for server error")
                        return resp.status_code, None
                
                # Success or client error (don't retry client errors like 404)
                if resp.status_code in [200, 201, 204]:
                    try:
                        return resp.status_code, resp.json() if resp.text else None
                    except:
                        return resp.status_code, None
                else:
                    return resp.status_code, None
            
            except requests.exceptions.RequestException as e:
                # Network errors - retry with exponential backoff
                if retry_count < max_retries:
                    wait_time = base_wait * (2 ** retry_count)
                    logger.warning(f"⚠️  Network error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    logger.error(f"❌ Network error after {max_retries} retries: {e}")
                    return 0, None
            
            except Exception as e:
                logger.error(f"❌ GitHub API error: {e}")
                return 0, None
    
    def review_pr(self, repo: str, pr_number: int) -> Dict:
        """
        Perform automated review of a pull request.
        
        Args:
            repo: Repository name (format: 'owner/repo')
            pr_number: Pull request number
        
        Returns:
            Dictionary with review results and summary
        """
        logger.info(f"🔍 Starting automated review for {repo}#{pr_number}")
        
        # Log review type
        if self.use_llm:
            logger.info(f"📊 Review Type: Hybrid (Static + LLM using {self.llm_model})")
            logger.info("🔍 Static Checks: File size, print statements, TODOs, exceptions, docstrings, tests")
            logger.info("🤖 LLM Checks: Logic, performance, security, design patterns, maintainability")
        else:
            logger.info("📊 Review Type: Static Code Analysis (No LLM)")
            logger.info("🔍 Checks: File size, print statements, TODOs, exceptions, docstrings, tests")
        
        review_result = {
            'pr': f"{repo}#{pr_number}",
            'approved': False,
            'issues': [],
            'suggestions': [],
            'summary': ''
        }
        
        try:
            # Get PR details
            pr_data = self._get_pr_details(repo, pr_number)
            if not pr_data:
                review_result['issues'].append("Failed to fetch PR details")
                return review_result
            
            # Get changed files
            files = self._get_changed_files(repo, pr_number)
            if not files:
                review_result['issues'].append("No files changed in PR")
                return review_result
            
            logger.info(f"📝 Reviewing {len(files)} changed file(s)")
            
            # Analyze each file
            for file_data in files:
                filename = file_data['filename']
                status = file_data['status']
                
                logger.info(f"   Analyzing: {filename} ({status})")
                
                # Skip deleted files
                if status == 'removed':
                    continue
                
                # Python files get full review
                if filename.endswith('.py'):
                    file_issues = self._review_python_file(repo, pr_number, file_data)
                    review_result['issues'].extend(file_issues)
            
            # Run tests if test files changed
            test_files = [f['filename'] for f in files if 'test' in f['filename']]
            if test_files:
                test_result = self._run_tests(test_files)
                if not test_result['passed']:
                    review_result['issues'].append(
                        f"Tests failed: {test_result['failed_count']} failures"
                    )
            
            # Determine approval
            critical_issues = [i for i in review_result['issues'] if 'CRITICAL' in i or 'ERROR' in i]
            
            if not review_result['issues']:
                review_result['approved'] = True
                review_result['summary'] = "✅ All checks passed! Code looks good."
            elif not critical_issues:
                review_result['approved'] = True  # Minor issues OK
                review_result['summary'] = f"⚠️ Approved with {len(review_result['issues'])} minor suggestion(s)"
            else:
                review_result['approved'] = False
                review_result['summary'] = f"❌ Changes requested: {len(critical_issues)} issue(s) need attention"
            
            logger.info(f"📊 Review complete: {review_result['summary']}")
            
        except Exception as e:
            logger.error(f"❌ Review failed: {e}", exc_info=True)
            review_result['issues'].append(f"Review error: {str(e)}")
        
        return review_result
    
    def _get_pr_details(self, repo: str, pr_number: int) -> Optional[Dict]:
        """Get PR details from GitHub API."""
        try:
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
            
            status, data = self._github_request('GET', url)
            
            if status == 200:
                return data
            else:
                logger.error(f"❌ Failed to get PR details: status {status}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Error getting PR details: {e}")
            return None
    
    def _get_changed_files(self, repo: str, pr_number: int) -> List[Dict]:
        """Get list of changed files in PR."""
        try:
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
            
            status, data = self._github_request('GET', url)
            
            if status == 200 and isinstance(data, list):
                return data
            else:
                logger.error(f"❌ Failed to get PR files: status {status}")
                return []
        
        except Exception as e:
            logger.error(f"❌ Error getting PR files: {e}")
            return []
    
    def _get_file_content(self, repo: str, pr_number: int, filename: str, patch: str) -> str:
        """
        Get full file content from patch or reconstruct from diff.
        
        Args:
            repo: Repository name
            pr_number: PR number
            filename: File path
            patch: Git diff patch
        
        Returns:
            Full file content (best effort reconstruction)
        """
        try:
            # Try to reconstruct content from patch
            lines = []
            for line in patch.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    lines.append(line[1:])  # Remove + prefix
                elif not line.startswith('-') and not line.startswith('@@'):
                    lines.append(line)
            
            return '\n'.join(lines)
        except Exception as e:
            logger.warning(f"⚠️ Could not reconstruct file content for {filename}: {e}")
            return patch  # Fallback to patch
    
    def _review_python_file(self, repo: str, pr_number: int, file_data: Dict) -> List[str]:
        """
        Review a Python file for code quality issues.
        
        Delegates to ReviewLogic module.
        
        Args:
            repo: Repository name
            pr_number: PR number
            file_data: File data from GitHub API
        
        Returns:
            List of issues found
        """
        filename = file_data['filename']
        patch = file_data.get('patch', '')
        
        if not patch:
            issues = []
            # Check for large files
            if file_data.get('changes', 0) > 500:
                issues.append(f"⚠️ Large file: {filename} has {file_data['changes']} changes. Consider splitting.")
            return issues
        
        # Detect if this is a new file
        is_new_file = file_data.get('status') == 'added'
        
        # Get full file content if available (for better analysis)
        file_content = self._get_file_content(repo, pr_number, filename, patch)
        
        # Delegate to review logic
        return self.review_logic.review_python_file(filename, patch, file_content, is_new_file)
    
    def _run_tests(self, test_files: List[str]) -> Dict:
        """
        Run tests for changed test files.
        
        Delegates to ReviewLogic module.
        
        Args:
            test_files: List of test file paths
        
        Returns:
            Dictionary with test results (keys: passed, failed, output)
        """
        result = self.review_logic.run_tests(test_files)
        
        # Log test results
        if result['passed']:
            logger.info(f"✅ Tests passed")
        else:
            logger.info(f"❌ Tests failed: {result['failed']} failure(s)")
        
        # Adapt result format for backwards compatibility
        return {
            'passed': result['passed'],
            'failed_count': result['failed'],
            'output': result['output']
        }
    
    def _llm_review_file(self, filename: str, patch: str, file_content: Optional[str] = None) -> List[str]:
        """
        Perform LLM-powered code review of a file.
        
        Delegates to ReviewLogic module.
        
        Args:
            filename: Name of the file being reviewed
            patch: Git diff patch
            file_content: Full file content (optional, for context)
        
        Returns:
            List of LLM-identified issues
        """
        return self.review_logic.llm_review_file(filename, patch, file_content)
    
    def assign_reviewers(self, repo: str, pr_number: int, reviewers: list) -> bool:
        """Assign reviewers to a PR.
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            reviewers: List of GitHub usernames to assign as reviewers
        
        Returns:
            True if reviewers assigned successfully
        """
        try:
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/requested_reviewers"
            data = {'reviewers': reviewers}
            
            status, response = self._github_request('POST', url, json_data=data)
            
            if status in [200, 201]:
                logger.info(f"✅ Assigned reviewers to {repo}#{pr_number}: {', '.join(reviewers)}")
                return True
            else:
                logger.warning(f"⚠️ Could not assign reviewers (status {status}): {response}")
                return False
        except Exception as e:
            logger.error(f"❌ Error assigning reviewers: {e}")
            return False
    
    def add_labels(self, repo: str, pr_number: int, labels: list) -> bool:
        """Add labels to a PR.
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            labels: List of label names to add
        
        Returns:
            True if labels added successfully
        """
        try:
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/labels"
            data = {'labels': labels}
            
            status, response = self._github_request('POST', url, json_data=data)
            
            if status in [200, 201]:
                logger.info(f"✅ Added labels to {repo}#{pr_number}: {', '.join(labels)}")
                return True
            else:
                logger.warning(f"⚠️ Could not add labels (status {status}): {response}")
                return False
        except Exception as e:
            logger.error(f"❌ Error adding labels: {e}")
            return False
    
    def update_pr_assignees(self, repo: str, pr_number: int, assignees: list) -> bool:
        """Assign users to a PR (different from reviewers).
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            assignees: List of GitHub usernames to assign to PR
        
        Returns:
            True if assignees updated successfully
        """
        try:
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/assignees"
            data = {'assignees': assignees}
            
            status, response = self._github_request('POST', url, json_data=data)
            
            if status in [200, 201]:
                logger.info(f"✅ Assigned PR to {repo}#{pr_number}: {', '.join(assignees)}")
                return True
            else:
                logger.warning(f"⚠️ Could not assign PR (status {status}): {response}")
                return False
        except Exception as e:
            logger.error(f"❌ Error assigning PR: {e}")
            return False
    
    def convert_to_draft(self, repo: str, pr_number: int, reason: str = "quality issues") -> bool:
        """Convert PR to draft status.
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            reason: Reason for conversion (for logging)
        
        Returns:
            True if converted successfully
        """
        try:
            owner, repo_name = repo.split('/')
            
            # GraphQL is required for draft conversion
            # First get the PR node_id
            pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
            pr_status, pr_data = self._github_request('GET', pr_url)
            
            if pr_status != 200 or not pr_data:
                logger.error(f"❌ Could not fetch PR #{pr_number} for draft conversion")
                return False
            
            node_id = pr_data.get('node_id')
            if not node_id:
                logger.error(f"❌ PR #{pr_number} missing node_id")
                return False
            
            # Convert to draft via GraphQL
            graphql_url = "https://api.github.com/graphql"
            query = """
            mutation($pullRequestId: ID!) {
              convertPullRequestToDraft(input: {pullRequestId: $pullRequestId}) {
                pullRequest {
                  isDraft
                }
              }
            }
            """
            variables = {"pullRequestId": node_id}
            graphql_data = {"query": query, "variables": variables}
            
            status, response = self._github_request('POST', graphql_url, json_data=graphql_data)
            
            if status == 200 and response and not response.get('errors'):
                logger.info(f"✅ Converted PR #{pr_number} to draft ({reason})")
                return True
            else:
                errors = response.get('errors', []) if response else []
                logger.warning(f"⚠️ Could not convert to draft (status {status}): {errors}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error converting to draft: {e}")
            return False
    
    def mark_ready_for_review(self, repo: str, pr_number: int, reason: str = "issues resolved") -> bool:
        """Mark draft PR as ready for review.
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            reason: Reason for marking ready (for logging)
        
        Returns:
            True if marked ready successfully
        """
        try:
            owner, repo_name = repo.split('/')
            
            # GraphQL is required for marking ready
            # First get the PR node_id
            pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
            pr_status, pr_data = self._github_request('GET', pr_url)
            
            if pr_status != 200 or not pr_data:
                logger.error(f"❌ Could not fetch PR #{pr_number} for ready conversion")
                return False
            
            # Check if already ready
            if not pr_data.get('draft', False):
                logger.info(f"ℹ️ PR #{pr_number} is already ready for review")
                return True
            
            node_id = pr_data.get('node_id')
            if not node_id:
                logger.error(f"❌ PR #{pr_number} missing node_id")
                return False
            
            # Mark ready via GraphQL
            graphql_url = "https://api.github.com/graphql"
            query = """
            mutation($pullRequestId: ID!) {
              markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
                pullRequest {
                  isDraft
                }
              }
            }
            """
            variables = {"pullRequestId": node_id}
            graphql_data = {"query": query, "variables": variables}
            
            status, response = self._github_request('POST', graphql_url, json_data=graphql_data)
            
            if status == 200 and response and not response.get('errors'):
                logger.info(f"✅ Marked PR #{pr_number} ready for review ({reason})")
                return True
            else:
                errors = response.get('errors', []) if response else []
                logger.warning(f"⚠️ Could not mark ready (status {status}): {errors}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error marking ready for review: {e}")
            return False
    
    def add_pr_comment(self, repo: str, pr_number: int, comment: str) -> bool:
        """Add a simple comment to a PR (not a review comment).
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            comment: Comment text
        
        Returns:
            True if comment added successfully
        """
        try:
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
            data = {'body': comment}
            
            status, response = self._github_request('POST', url, json_data=data)
            
            if status in [200, 201]:
                logger.info(f"✅ Added comment to {repo}#{pr_number}")
                return True
            else:
                logger.warning(f"⚠️ Could not add comment (status {status}): {response}")
                return False
        except Exception as e:
            logger.error(f"❌ Error adding comment: {e}")
            return False
    
    def create_followup_issue(self, repo: str, pr_number: int, review_result: Dict, merge_decision: Dict) -> Optional[int]:
        """Create a follow-up issue for PR suggestions and warnings.
        
        This creates a tech-debt tracking issue with all non-critical suggestions
        from the PR review, allowing the PR to be merged while still tracking
        improvements for future work.
        
        Args:
            repo: Repository in owner/name format
            pr_number: Merged PR number
            review_result: Review results from review_pr()
            merge_decision: Merge decision from evaluate_merge_decision()
        
        Returns:
            Issue number if created successfully, None otherwise
        """
        try:
            owner, repo_name = repo.split('/')
            
            # Extract non-critical issues
            warnings = []
            suggestions = []
            for issue in review_result.get('issues', []):
                if '⚠️' in issue or 'WARNING' in issue:
                    warnings.append(issue)
                elif 'ℹ️' in issue or 'INFO' in issue or 'SUGGESTION' in issue:
                    suggestions.append(issue)
            
            if not warnings and not suggestions:
                logger.debug("No warnings or suggestions to track - skipping follow-up issue")
                return None
            
            # Create issue title
            warning_count = merge_decision.get('warnings', 0)
            info_count = merge_decision.get('info_suggestions', 0)
            title = f"Tech Debt: Address {warning_count} warning(s) and {info_count} suggestion(s) from PR #{pr_number}"
            
            # Create issue body
            body = f"""**Automated Follow-up Issue from PR #{pr_number}**

This issue tracks non-critical warnings and suggestions from the automated review of PR #{pr_number}.
The PR was merged because it met quality standards, but these improvements should be addressed in a future PR.

---

"""
            
            if warnings:
                body += f"### ⚠️ Warnings ({len(warnings)})\n\n"
                for warning in warnings:
                    body += f"- {warning}\n"
                body += "\n"
            
            if suggestions:
                body += f"### ℹ️ Suggestions ({len(suggestions)})\n\n"
                for suggestion in suggestions:
                    body += f"- {suggestion}\n"
                body += "\n"
            
            body += f"""---

**Next Steps:**
1. Review each warning/suggestion
2. Determine which improvements are worth implementing
3. Create targeted PR(s) to address them
4. Close this issue when complete or mark as "won't fix" if not relevant

**Related PR:** #{pr_number}
**Created by:** Automated PR Review System
"""
            
            # Create issue via GitHub API
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
            data = {
                'title': title,
                'body': body,
                'labels': ['tech-debt', 'from-pr-review', f'from-pr-{pr_number}']
            }
            
            status, response = self._github_request('POST', url, json_data=data)
            
            if status == 201 and response:
                issue_number = response.get('number')
                logger.info(f"✅ Created follow-up issue #{issue_number} for PR #{pr_number}")
                return issue_number
            else:
                logger.warning(f"⚠️ Could not create follow-up issue (status {status}): {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating follow-up issue: {e}")
            return None
    
    def remove_label(self, repo: str, pr_number: int, label: str) -> bool:
        """Remove a label from a PR.
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            label: Label name to remove
        
        Returns:
            True if label removed successfully
        """
        try:
            owner, repo_name = repo.split('/')
            # URL encode the label name
            import urllib.parse
            encoded_label = urllib.parse.quote(label)
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/labels/{encoded_label}"
            
            status, response = self._github_request('DELETE', url)
            
            if status == 200:
                logger.info(f"✅ Removed label '{label}' from {repo}#{pr_number}")
                return True
            elif status == 404:
                logger.debug(f"ℹ️ Label '{label}' not found on {repo}#{pr_number}")
                return True  # Label already removed, consider success
            else:
                logger.warning(f"⚠️ Could not remove label (status {status}): {response}")
                return False
        except Exception as e:
            logger.error(f"❌ Error removing label: {e}")
            return False
    
    def post_review_comment(self, repo: str, pr_number: int, review_result: Dict, use_review_api: bool = True) -> bool:
        """
        Post review comment to PR.
        
        Args:
            repo: Repository name
            pr_number: PR number
            review_result: Review results from review_pr()
            use_review_api: Use GitHub PR Review API instead of simple comment (default: True)
        
        Returns:
            True if comment posted successfully
        """
        try:
            # Format review comment
            comment = self._format_review_comment(review_result)
            owner, repo_name = repo.split('/')
            
            if use_review_api:
                # Use official PR Review API - shows as actual review
                url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/reviews"
                
                # Determine review event based on approval status
                if review_result['approved']:
                    if review_result['issues']:
                        event = 'COMMENT'  # Approved with suggestions
                    else:
                        event = 'APPROVE'  # Fully approved
                else:
                    event = 'REQUEST_CHANGES'  # Changes needed
                
                data = {
                    'body': comment,
                    'event': event
                }
                
                status, _ = self._github_request('POST', url, json_data=data)
                
                if status in [200, 201]:
                    logger.info(f"✅ Posted PR review ({event}) to {repo}#{pr_number}")
                    return True
                else:
                    logger.error(f"❌ Failed to post review: status {status}")
                    # Fallback to regular comment
                    logger.info("   Trying fallback: regular comment...")
                    use_review_api = False
            
            if not use_review_api:
                # Fallback: Post as regular comment
                url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
                data = {'body': comment}
                status, _ = self._github_request('POST', url, json_data=data)
                
                if status in [200, 201]:
                    logger.info(f"✅ Posted review comment to {repo}#{pr_number}")
                    return True
                else:
                    logger.error(f"❌ Failed to post comment: status {status}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Error posting comment: {e}")
            return False
    
    def _format_review_comment(self, review_result: Dict) -> str:
        """Format review results as GitHub comment."""
        lines = [
            "## 🤖 Automated Code Review",
            ""
        ]
        
        # Add review method info
        if self.use_llm:
            lines.extend([
                f"**Review Method**: Hybrid Analysis (Static + LLM)",
                f"**LLM Model**: `{self.llm_model}`",
                "**Checks**: File size, print statements, TODOs, exceptions, docstrings, tests + deep code analysis",
                ""
            ])
        else:
            lines.extend([
                "**Review Method**: Static Code Analysis",
                "**Checks**: File size, print statements, TODOs, exceptions, docstrings, tests",
                ""
            ])
        
        lines.extend([
            f"**Status**: {review_result['summary']}",
            ""
        ])
        
        if review_result['issues']:
            lines.append("### Issues Found")
            for issue in review_result['issues']:
                lines.append(f"- {issue}")
            lines.append("")
        
        if review_result['suggestions']:
            lines.append("### Suggestions")
            for suggestion in review_result['suggestions']:
                lines.append(f"- {suggestion}")
            lines.append("")
        
        if review_result['approved']:
            lines.append("✅ **This PR is approved for merge**")
        else:
            lines.append("❌ **Changes requested** - Please address the issues above")
        
        lines.extend([
            "",
            "---",
            f"*Automated review by Agent-Forge PR Review Bot (m0nk111-{self.bot_account})*"
        ])
        
        return '\n'.join(lines)
    
    def complete_pr_review_workflow(self, repo: str, pr_number: int, 
                                     auto_assign_reviewers: bool = True,
                                     auto_label: bool = True,
                                     reviewers: Optional[list] = None,
                                     post_comment: bool = True) -> Dict:
        """Complete PR review workflow with review, assignment, and labeling.
        
        **DELEGATED TO ORCHESTRATOR** - This method now delegates to WorkflowOrchestrator.
        
        This method performs the full PR review process:
        1. Review the PR code
        2. Post review comment with status (APPROVE/REQUEST_CHANGES/COMMENT)
        3. Assign reviewers (if specified)
        4. Add appropriate labels based on review results
        5. Assign PR to relevant users
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            auto_assign_reviewers: Automatically assign admin as reviewer (default: True)
            auto_label: Automatically add labels based on review (default: True)
            reviewers: List of GitHub usernames to assign as reviewers (default: ['m0nk111'])
            post_comment: Post review comment (default: True)
        
        Returns:
            Dict with workflow results including review_result, assigned_reviewers, added_labels
        """
        return self.workflow_orchestrator.complete_review_workflow(
            repo=repo,
            pr_number=pr_number,
            auto_assign_reviewers=auto_assign_reviewers,
            auto_label=auto_label,
            reviewers=reviewers,
            post_comment=post_comment
        )
    
    def evaluate_merge_decision(self, review_result: Dict) -> Dict:
        """Evaluate whether PR should be merged based on review results.
        
        Decision logic:
        - APPROVED (no issues): Auto-merge recommended
        - APPROVED with minor suggestions: Merge with consideration
        - CHANGES_REQUESTED: Do NOT merge
        
        Args:
            review_result: Review results from review_pr()
        
        Returns:
            Dict with merge_recommendation, should_auto_merge, reasoning
        """
        critical_count = sum(1 for issue in review_result['issues'] if 'CRITICAL' in issue or '❌' in issue)
        warning_count = sum(1 for issue in review_result['issues'] if 'WARNING' in issue or '⚠️' in issue)
        info_count = len(review_result['issues']) - critical_count - warning_count
        
        decision = {
            'should_auto_merge': False,
            'merge_recommendation': 'DO_NOT_MERGE',
            'reasoning': [],
            'critical_issues': critical_count,
            'warnings': warning_count,
            'info_suggestions': info_count,
            'autonomous_action': None  # What action the system will take
        }
        
        if not review_result['approved']:
            # Changes requested - convert to draft for developer to fix
            decision['merge_recommendation'] = 'DO_NOT_MERGE'
            decision['autonomous_action'] = 'CONVERT_TO_DRAFT'
            decision['reasoning'].append(f"Changes requested: {critical_count} critical issue(s) found")
            decision['reasoning'].append("System will convert PR to draft and notify author")
        elif critical_count > 0:
            # Has critical issues - convert to draft even if approved
            decision['merge_recommendation'] = 'DO_NOT_MERGE'
            decision['autonomous_action'] = 'CONVERT_TO_DRAFT'
            decision['reasoning'].append(f"Critical issues present: {critical_count} issue(s) need attention")
            decision['reasoning'].append("System will convert PR to draft for fixes")
        elif warning_count > 5:
            # Many warnings - create follow-up issue and merge
            decision['should_auto_merge'] = True
            decision['merge_recommendation'] = 'AUTO_MERGE'
            decision['autonomous_action'] = 'MERGE_AND_CREATE_ISSUE'
            decision['reasoning'].append(f"Multiple warnings ({warning_count}) - will merge and track in follow-up issue")
            decision['reasoning'].append("System will create tech-debt issue for improvements")
        elif warning_count > 0 or info_count > 0:
            # Minor suggestions - merge and optionally create follow-up
            decision['should_auto_merge'] = True
            decision['merge_recommendation'] = 'AUTO_MERGE'
            decision['autonomous_action'] = 'MERGE_ONLY' if (warning_count + info_count) <= 2 else 'MERGE_AND_CREATE_ISSUE'
            decision['reasoning'].append(f"Approved with {warning_count} warning(s) and {info_count} suggestion(s)")
            if (warning_count + info_count) > 2:
                decision['reasoning'].append("System will merge and create follow-up issue for suggestions")
            else:
                decision['reasoning'].append("System will merge - suggestions are minor")
        else:
            # Fully approved, no issues
            decision['should_auto_merge'] = True
            decision['merge_recommendation'] = 'AUTO_MERGE'
            decision['autonomous_action'] = 'MERGE_ONLY'
            decision['reasoning'].append("Fully approved with no issues - safe to merge")
        
        return decision
    
    def merge_pull_request(self, repo: str, pr_number: int, 
                          merge_method: str = 'squash',
                          commit_title: Optional[str] = None,
                          commit_message: Optional[str] = None) -> bool:
        """Merge a pull request.
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            merge_method: Merge method: 'merge', 'squash', or 'rebase' (default: squash)
            commit_title: Custom commit title (optional)
            commit_message: Custom commit message (optional)
        
        Returns:
            True if merged successfully
        """
        try:
            owner, repo_name = repo.split('/')
            
            # First check if PR is mergeable
            pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
            pr_status, pr_data = self._github_request('GET', pr_url)
            
            if pr_status == 200 and pr_data:
                mergeable_state = pr_data.get('mergeable_state')
                is_draft = pr_data.get('draft', False)
                
                # Check for common blocking conditions
                if is_draft:
                    logger.error(f"❌ PR #{pr_number} is a DRAFT - cannot merge draft PRs")
                    logger.info("   Convert to ready-for-review first")
                    return False
                
                if mergeable_state == 'dirty':
                    logger.error(f"❌ PR #{pr_number} has CONFLICTS - resolve conflicts first")
                    return False
                
                if mergeable_state == 'blocked':
                    logger.error(f"❌ PR #{pr_number} is BLOCKED - check required status checks or branch protection")
                    return False
                
                if mergeable_state == 'behind':
                    logger.warning(f"⚠️  PR #{pr_number} is BEHIND base branch - updating branch may be needed")
                
                if mergeable_state == 'unstable':
                    logger.warning(f"⚠️  PR #{pr_number} has FAILING or PENDING checks")
            
            # Attempt merge
            merge_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/merge"
            
            data = {
                'merge_method': merge_method
            }
            
            if commit_title:
                data['commit_title'] = commit_title
            if commit_message:
                data['commit_message'] = commit_message
            
            status, response = self._github_request('PUT', merge_url, json_data=data)
            
            if status in [200, 201]:
                logger.info(f"✅ Successfully merged {repo}#{pr_number} using {merge_method}")
                return True
            elif status == 405:
                logger.error(f"❌ PR #{pr_number} is not mergeable")
                logger.error(f"   Possible reasons: conflicts, failing checks, branch protection, or not approved")
                return False
            elif status == 409:
                logger.error(f"❌ PR #{pr_number} head SHA has changed - PR was updated")
                logger.error(f"   Review the changes and try again")
                return False
            else:
                logger.error(f"❌ Failed to merge PR #{pr_number}: status {status}")
                if response:
                    logger.error(f"   Response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error merging PR: {e}")
            return False
    
    def complete_pr_review_and_merge_workflow(self, repo: str, pr_number: int,
                                              auto_merge_if_approved: bool = False,
                                              merge_with_suggestions: bool = False,
                                              merge_method: str = 'squash',
                                              auto_assign_reviewers: bool = True,
                                              auto_label: bool = True,
                                              reviewers: Optional[list] = None,
                                              post_comment: bool = True) -> Dict:
        """Complete workflow: review, assign, label, and optionally merge.
        
        **DELEGATED TO ORCHESTRATOR** - This method now delegates to WorkflowOrchestrator.
        
        This extends complete_pr_review_workflow() with intelligent merge decision.
        
        Merge Logic:
        - AUTO_MERGE: Fully approved, no issues → merge if auto_merge_if_approved=True
        - MERGE_WITH_CONSIDERATION: Approved with suggestions → merge if merge_with_suggestions=True
        - MANUAL_REVIEW: Critical issues or many warnings → never auto-merge
        - DO_NOT_MERGE: Changes requested → never merge
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            auto_merge_if_approved: Auto-merge if fully approved (no issues) (default: False)
            merge_with_suggestions: Merge even if suggestions present (default: False)
            merge_method: Merge method: 'merge', 'squash', 'rebase' (default: squash)
            auto_assign_reviewers: Assign reviewers (default: True)
            auto_label: Add labels (default: True)
            reviewers: List of reviewers (default: ['m0nk111'])
            post_comment: Post review comment (default: True)
        
        Returns:
            Dict with workflow results including merge decision and status
        """
        return self.workflow_orchestrator.complete_review_and_merge_workflow(
            repo=repo,
            pr_number=pr_number,
            auto_merge_if_approved=auto_merge_if_approved,
            merge_with_suggestions=merge_with_suggestions,
            merge_method=merge_method,
            auto_assign_reviewers=auto_assign_reviewers,
            auto_label=auto_label,
            reviewers=reviewers,
            post_comment=post_comment
        )

if __name__ == '__main__':
    import sys
    sys.exit(main())
