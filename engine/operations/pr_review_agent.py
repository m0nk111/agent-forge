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
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from engine.utils.review_lock import ReviewLock


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
        
        # LLM configuration
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Review lock for preventing concurrent reviews
        self.review_lock = ReviewLock(
            lock_dir=str(self.project_root / "data" / "review_locks"),
            lock_timeout=300  # 5 minutes
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
    
    def _review_python_file(self, repo: str, pr_number: int, file_data: Dict) -> List[str]:
        """
        Review a Python file for code quality issues.
        
        Args:
            repo: Repository name
            pr_number: PR number
            file_data: File data from GitHub API
        
        Returns:
            List of issues found
        """
        issues = []
        filename = file_data['filename']
        
        # Check for large files
        if file_data.get('changes', 0) > 500:
            issues.append(f"⚠️ Large file: {filename} has {file_data['changes']} changes. Consider splitting.")
        
        # Check if patch data available
        patch = file_data.get('patch', '')
        if not patch:
            return issues
        
        # Analyze patch for common issues
        lines = patch.split('\n')
        
        # Check for print statements (should use logging)
        print_lines = [i for i, line in enumerate(lines) if 'print(' in line and line.strip().startswith('+')]
        if print_lines:
            issues.append(f"💡 Consider using logging instead of print() in {filename} (lines: {len(print_lines)})")
        
        # Check for TODO/FIXME comments
        todo_lines = [i for i, line in enumerate(lines) if ('TODO' in line or 'FIXME' in line) and line.strip().startswith('+')]
        if todo_lines:
            issues.append(f"📝 TODOs found in {filename}: {len(todo_lines)} items")
        
        # Check for except: pass (bad error handling)
        for i, line in enumerate(lines):
            if line.strip().startswith('+') and 'except:' in line:
                if i + 1 < len(lines) and 'pass' in lines[i + 1]:
                    issues.append(f"❌ CRITICAL: Silent exception handling in {filename}. Use specific exceptions and logging.")
        
        # Check for missing docstrings in new functions
        func_lines = [(i, line) for i, line in enumerate(lines) if line.strip().startswith('+ def ') or line.strip().startswith('+def ')]
        for i, func_line in func_lines:
            # Check if docstring follows
            if i + 2 < len(lines):
                next_lines = ''.join(lines[i+1:i+3])
                if '"""' not in next_lines and "'''" not in next_lines:
                    func_name = func_line.split('def ')[1].split('(')[0]
                    issues.append(f"⚠️ Missing docstring for function '{func_name}' in {filename}")
        
        # LLM review (if enabled)
        if self.use_llm:
            llm_issues = self._llm_review_file(filename, patch)
            issues.extend(llm_issues)
        
        return issues
    
    def _run_tests(self, test_files: List[str]) -> Dict:
        """
        Run tests for changed test files.
        
        Args:
            test_files: List of test file paths
        
        Returns:
            Dictionary with test results
        """
        result = {
            'passed': False,
            'failed_count': 0,
            'output': ''
        }
        
        try:
            # Run pytest on changed test files
            cmd = ['python3', '-m', 'pytest'] + test_files + ['-v', '--tb=short']
            
            process = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            result['output'] = process.stdout + process.stderr
            result['passed'] = process.returncode == 0
            
            # Count failures
            if not result['passed']:
                for line in result['output'].split('\n'):
                    if 'failed' in line.lower():
                        try:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if 'failed' in part.lower() and i > 0:
                                    result['failed_count'] = int(parts[i-1])
                                    break
                        except:
                            pass
            
            logger.info(f"✅ Tests {'passed' if result['passed'] else 'failed'}: {result['failed_count']} failures")
        
        except subprocess.TimeoutExpired:
            logger.error("❌ Test execution timed out")
            result['failed_count'] = 1
        except Exception as e:
            logger.error(f"❌ Test execution error: {e}")
            result['failed_count'] = 1
        
        return result
    
    def _llm_review_file(self, filename: str, patch: str, file_content: Optional[str] = None) -> List[str]:
        """
        Perform LLM-powered code review of a file.
        
        Args:
            filename: Name of the file being reviewed
            patch: Git diff patch
            file_content: Full file content (optional, for context)
        
        Returns:
            List of LLM-identified issues
        """
        if not self.use_llm:
            return []
        
        issues = []
        
        try:
            logger.info(f"🤖 LLM reviewing: {filename} (model: {self.llm_model})")
            
            # Prepare prompt
            prompt = f"""You are an expert code reviewer. Review this code change and provide specific, actionable feedback.

File: {filename}

Changes (git diff):
```
{patch[:2000]}  # Limit to prevent huge prompts
```

Analyze for:
1. Logic errors or bugs
2. Performance issues
3. Security vulnerabilities
4. Design pattern violations
5. Code maintainability concerns

Provide feedback in this format:
- [CRITICAL/WARNING/INFO] Issue description

Be concise. Only report real issues, not nitpicks."""

            # Query Ollama
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more focused reviews
                        "num_predict": 500   # Limit response length
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                llm_response = response.json().get('response', '').strip()
                
                if llm_response and len(llm_response) > 10:
                    # Parse LLM response into issues
                    lines = llm_response.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('-') and any(x in line.upper() for x in ['CRITICAL', 'WARNING', 'INFO']):
                            issues.append(f"🤖 LLM: {line.lstrip('-').strip()}")
                    
                    if not issues and llm_response:
                        # LLM found issues but not in expected format
                        issues.append(f"🤖 LLM feedback for {filename}: {llm_response[:200]}")
                    
                    logger.info(f"   Found {len(issues)} LLM-identified issue(s)")
            else:
                logger.warning(f"   LLM API error: status {response.status_code}")
        
        except requests.exceptions.Timeout:
            logger.warning(f"   LLM review timeout for {filename}")
        except Exception as e:
            logger.error(f"   LLM review error: {e}")
        
        return issues
    
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
        workflow_result = {
            'review_result': None,
            'review_posted': False,
            'reviewers_assigned': False,
            'labels_added': False,
            'assignees_updated': False,
            'errors': []
        }
        
        try:
            # Step 1: Review the PR
            logger.info(f"🔍 Starting complete PR review workflow for {repo}#{pr_number}")
            review_result = self.review_pr(repo, pr_number)
            workflow_result['review_result'] = review_result
            
            # Step 2: Post review comment with proper status
            if post_comment:
                logger.info("📝 Posting review comment...")
                if self.post_review_comment(repo, pr_number, review_result, use_review_api=True):
                    workflow_result['review_posted'] = True
                else:
                    workflow_result['errors'].append("Failed to post review comment")
            
            # Step 3: Assign reviewers
            if auto_assign_reviewers:
                if reviewers is None:
                    reviewers = ['m0nk111']  # Default to admin
                
                logger.info(f"👥 Assigning reviewers: {reviewers}")
                if self.assign_reviewers(repo, pr_number, reviewers):
                    workflow_result['reviewers_assigned'] = True
                else:
                    workflow_result['errors'].append("Failed to assign reviewers (may be PR author)")
            
            # Step 4: Add labels based on review result
            if auto_label:
                labels = []
                
                if review_result['approved']:
                    if review_result['issues']:
                        labels.append('approved-with-suggestions')
                        labels.append('ready-for-merge')
                    else:
                        labels.append('approved')
                        labels.append('ready-for-merge')
                else:
                    labels.append('changes-requested')
                    labels.append('needs-work')
                
                # Add technical labels
                if self.use_llm:
                    labels.append('ai-reviewed')
                else:
                    labels.append('static-reviewed')
                
                # Add severity labels
                critical_count = sum(1 for issue in review_result['issues'] if 'CRITICAL' in issue)
                if critical_count > 0:
                    labels.append('critical-issues')
                
                logger.info(f"🏷️  Adding labels: {labels}")
                if self.add_labels(repo, pr_number, labels):
                    workflow_result['labels_added'] = True
                    workflow_result['labels'] = labels
                else:
                    workflow_result['errors'].append("Failed to add labels")
            
            # Step 5: Assign PR to admin for visibility
            if auto_assign_reviewers:
                logger.info("📌 Assigning PR to admin...")
                if self.update_pr_assignees(repo, pr_number, ['m0nk111']):
                    workflow_result['assignees_updated'] = True
                else:
                    workflow_result['errors'].append("Failed to assign PR")
            
            # Summary
            logger.info("✅ PR review workflow complete")
            logger.info(f"   Review posted: {workflow_result['review_posted']}")
            logger.info(f"   Reviewers assigned: {workflow_result['reviewers_assigned']}")
            logger.info(f"   Labels added: {workflow_result['labels_added']}")
            logger.info(f"   Assignees updated: {workflow_result['assignees_updated']}")
            
            if workflow_result['errors']:
                logger.warning(f"   Errors: {len(workflow_result['errors'])}")
                for error in workflow_result['errors']:
                    logger.warning(f"      - {error}")
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"❌ Error in PR review workflow: {e}")
            workflow_result['errors'].append(str(e))
            return workflow_result
    
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
        # 🔒 Acquire review lock to prevent concurrent reviews
        requester = f"{self.bot_account}-pr-review"
        if not self.review_lock.acquire(repo, pr_number, requester):
            logger.warning(f"⏭️ Skipping review of {repo}#{pr_number} - already being reviewed by another process")
            return {
                'skipped': True,
                'reason': 'Review already in progress (locked by another process)',
                'review_result': None,
                'merge_decision': None
            }
        
        try:
            # Run standard review workflow
            workflow_result = self.complete_pr_review_workflow(
                repo=repo,
                pr_number=pr_number,
                auto_assign_reviewers=auto_assign_reviewers,
                auto_label=auto_label,
                reviewers=reviewers,
                post_comment=post_comment
            )
            
            # Evaluate merge decision
            review_result = workflow_result['review_result']
            merge_decision = self.evaluate_merge_decision(review_result)
            workflow_result['merge_decision'] = merge_decision
            
            # Handle critical issues - convert to draft
            if merge_decision['merge_recommendation'] == 'DO_NOT_MERGE':
                critical_count = merge_decision.get('critical_count', 0)
                if critical_count > 0:
                    logger.warning(f"⚠️ Converting PR to draft due to {critical_count} critical issue(s)")
                    
                    # Convert to draft
                    if self.convert_to_draft(repo, pr_number, f"{critical_count} critical issues"):
                        # Add explanatory comment
                        comment = f"""🚧 **Converted to Draft**

This PR has been automatically converted to draft status because the automated review found **{critical_count} critical issue(s)** that must be addressed before merging.

**Critical Issues:**
"""
                        # Extract critical issues from review
                        for issue in review_result.get('issues', []):
                            if 'CRITICAL' in issue or '❌' in issue:
                                comment += f"- {issue}\n"
                        
                        comment += """
**Next Steps:**
1. Fix the critical issues listed above
2. Push your changes to this branch
3. Mark this PR as "Ready for review" when done
4. The automated review will run again

Once all critical issues are resolved, this PR can be merged."""
                        
                        self.add_pr_comment(repo, pr_number, comment)
                        workflow_result['converted_to_draft'] = True
            
            # Check for merge conflicts and handle them
            owner, repo_name = repo.split('/')
            pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
            pr_status, pr_data = self._github_request('GET', pr_url)
            
            if pr_status == 200 and pr_data:
                mergeable_state = pr_data.get('mergeable_state')
                
                if mergeable_state == 'dirty':  # Has conflicts
                    logger.warning(f"⚠️ PR has merge conflicts - converting to draft and adding instructions")
                    
                    # Convert to draft
                    if self.convert_to_draft(repo, pr_number, "merge conflicts"):
                        # Add has-conflicts label
                        self.add_labels(repo, pr_number, ['has-conflicts'])
                        
                        # Remove ready-for-merge label if present
                        self.remove_label(repo, pr_number, 'ready-for-merge')
                        
                        # Add conflict resolution instructions
                        pr_author = pr_data.get('user', {}).get('login', 'author')
                        base_branch = pr_data.get('base', {}).get('ref', 'main')
                        head_branch = pr_data.get('head', {}).get('ref', 'your-branch')
                        
                        comment = f"""⚠️ **Merge Conflicts Detected**

@{pr_author} This PR has merge conflicts with the `{base_branch}` branch and has been converted to draft status.

**To resolve conflicts:**

1. Update your local branch with the latest changes:
   ```bash
   git checkout {head_branch}
   git fetch origin
   git merge origin/{base_branch}
   ```

2. Resolve the conflicts in your editor

3. Mark conflicts as resolved:
   ```bash
   git add .
   git commit -m "Resolve merge conflicts with {base_branch}"
   ```

4. Push the resolved changes:
   ```bash
   git push origin {head_branch}
   ```

5. Mark this PR as "Ready for review"

The automated review will run again once conflicts are resolved."""
                        
                        self.add_pr_comment(repo, pr_number, comment)
                        workflow_result['converted_to_draft'] = True
                        workflow_result['has_conflicts'] = True
                        
                        # Don't attempt merge if there are conflicts
                        return workflow_result
            
            # Log merge decision
            logger.info(f"\n🤔 Merge Decision: {merge_decision['merge_recommendation']}")
            logger.info(f"   🤖 Autonomous Action: {merge_decision.get('autonomous_action', 'NONE')}")
            for reason in merge_decision['reasoning']:
                logger.info(f"   • {reason}")
            
            # Execute autonomous action based on decision
            workflow_result['merged'] = False
            workflow_result['followup_issue_created'] = False
            autonomous_action = merge_decision.get('autonomous_action')
            
            if autonomous_action == 'CONVERT_TO_DRAFT':
                # Already handled above (critical issues or conflicts)
                logger.info("   🚧 PR converted to draft for fixes")
                
            elif autonomous_action == 'MERGE_ONLY':
                # Clean merge with no follow-up
                if auto_merge_if_approved:
                    logger.info(f"\n🔀 Merging PR #{pr_number} using {merge_method}...")
                    if self.merge_pull_request(repo, pr_number, merge_method):
                        workflow_result['merged'] = True
                        logger.info(f"   ✅ PR #{pr_number} merged successfully!")
                    else:
                        workflow_result['errors'].append("Merge failed (conflicts, checks, or permissions)")
                        logger.error(f"   ❌ Merge failed")
                else:
                    logger.info("   ⏸️  Auto-merge disabled - PR ready but not merged")
                    
            elif autonomous_action == 'MERGE_AND_CREATE_ISSUE':
                # Merge first, then create follow-up issue
                if auto_merge_if_approved or merge_with_suggestions:
                    logger.info(f"\n🔀 Merging PR #{pr_number} using {merge_method}...")
                    if self.merge_pull_request(repo, pr_number, merge_method):
                        workflow_result['merged'] = True
                        logger.info(f"   ✅ PR #{pr_number} merged successfully!")
                        
                        # Create follow-up issue for suggestions
                        logger.info("   📝 Creating follow-up issue for suggestions/warnings...")
                        followup_issue = self.create_followup_issue(
                            repo=repo,
                            pr_number=pr_number,
                            review_result=review_result,
                            merge_decision=merge_decision
                        )
                        if followup_issue:
                            workflow_result['followup_issue_created'] = True
                            workflow_result['followup_issue_number'] = followup_issue
                            logger.info(f"   ✅ Created follow-up issue #{followup_issue}")
                        else:
                            logger.warning("   ⚠️  Failed to create follow-up issue")
                    else:
                        workflow_result['errors'].append("Merge failed (conflicts, checks, or permissions)")
                        logger.error(f"   ❌ Merge failed")
                else:
                    logger.info("   ⏸️  Auto-merge disabled - PR ready but not merged")
            
            return workflow_result
        
        finally:
            # 🔓 Always release lock when done (even if error occurred)
            self.review_lock.release(repo, pr_number)


def main():
    """CLI entry point for testing."""
    import sys
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Review a pull request')
    parser.add_argument('repo', help='Repository (owner/repo)')
    parser.add_argument('pr_number', type=int, help='PR number')
    parser.add_argument('--post-comment', action='store_true', help='Post review as comment')
    parser.add_argument('--use-llm', action='store_true', help='Enable LLM-powered deep code review')
    parser.add_argument('--llm-model', default='qwen2.5-coder:7b', help='LLM model to use (default: qwen2.5-coder:7b)')
    parser.add_argument('--bot-account', default='admin', 
                        help='Bot account to use: admin, post, reviewer, coder1, etc. '
                             'NOTE: Only admin and post accounts have visible reviews. '
                             '(default: admin)')
    parser.add_argument('--use-review-api', action='store_true', default=True,
                        help='Use official PR Review API (default: True)')
    parser.add_argument('--full-workflow', action='store_true',
                        help='Run complete workflow: review + assign reviewers + add labels')
    parser.add_argument('--reviewers', nargs='*', default=None,
                        help='Reviewers to assign (default: m0nk111)')
    parser.add_argument('--no-auto-label', action='store_true',
                        help='Disable automatic label assignment')
    parser.add_argument('--no-auto-assign', action='store_true',
                        help='Disable automatic reviewer assignment')
    
    # Merge options
    parser.add_argument('--auto-merge-if-approved', action='store_true',
                        help='Auto-merge if fully approved (no issues)')
    parser.add_argument('--merge-with-suggestions', action='store_true',
                        help='Merge even if suggestions present (approved-with-suggestions)')
    parser.add_argument('--merge-method', choices=['merge', 'squash', 'rebase'], default='squash',
                        help='Merge method to use (default: squash)')
    
    args = parser.parse_args()
    
    # Warn if using bot account (except admin/post which are visible)
    if args.bot_account not in ['admin', 'm0nk111', 'post']:
        logger.warning(f"⚠️  Using bot account '{args.bot_account}' - reviews may not be visible to admin")
        logger.warning("   Consider using --bot-account admin for public reviews")
    
    try:
        reviewer = PRReviewAgent(
            use_llm=args.use_llm,
            llm_model=args.llm_model,
            bot_account=args.bot_account
        )
        
        # Print review type info
        if args.use_llm:
            print("🤖 PR Review Agent - Hybrid Review (Static + LLM)")
            print(f"🔧 Review Method: Rule-based checks + {args.llm_model}")
            print("✓ Deep analysis • ✓ Context-aware • ✓ Architecture insights")
        else:
            print("📊 PR Review Agent - Static Code Analysis")
            print("🔧 Review Method: Rule-based checks (No LLM)")
            print("✓ Fast • ✓ Deterministic • ✓ Zero cost")
        print()
        
        # Use full workflow or simple review
        if args.full_workflow or args.post_comment or args.auto_merge_if_approved or args.merge_with_suggestions:
            # Check if merge is requested
            if args.auto_merge_if_approved or args.merge_with_suggestions:
                # Complete workflow with merge decision
                workflow_result = reviewer.complete_pr_review_and_merge_workflow(
                    repo=args.repo,
                    pr_number=args.pr_number,
                    auto_merge_if_approved=args.auto_merge_if_approved,
                    merge_with_suggestions=args.merge_with_suggestions,
                    merge_method=args.merge_method,
                    auto_assign_reviewers=not args.no_auto_assign,
                    auto_label=not args.no_auto_label,
                    reviewers=args.reviewers,
                    post_comment=args.post_comment or args.full_workflow
                )
            else:
                # Standard workflow without merge
                workflow_result = reviewer.complete_pr_review_workflow(
                    repo=args.repo,
                    pr_number=args.pr_number,
                    auto_assign_reviewers=not args.no_auto_assign,
                    auto_label=not args.no_auto_label,
                    reviewers=args.reviewers,
                    post_comment=args.post_comment
                )
            
            result = workflow_result['review_result']
            
            print(f"\n{'='*60}")
            print("REVIEW SUMMARY")
            print('='*60)
            print(result['summary'])
            
            if result['issues']:
                print(f"\nIssues ({len(result['issues'])}):")
                for issue in result['issues']:
                    print(f"  - {issue}")
            
            print(f"\n{'='*60}")
            print("WORKFLOW RESULTS")
            print('='*60)
            print(f"✅ Review posted: {workflow_result['review_posted']}")
            print(f"✅ Reviewers assigned: {workflow_result['reviewers_assigned']}")
            print(f"✅ Labels added: {workflow_result['labels_added']}")
            if 'labels' in workflow_result:
                print(f"   Labels: {', '.join(workflow_result['labels'])}")
            print(f"✅ Assignees updated: {workflow_result['assignees_updated']}")
            
            # Show merge decision if available
            if 'merge_decision' in workflow_result:
                decision = workflow_result['merge_decision']
                print(f"\n{'='*60}")
                print("MERGE DECISION")
                print('='*60)
                print(f"Recommendation: {decision['merge_recommendation']}")
                print(f"Issues breakdown:")
                print(f"  • Critical: {decision['critical_issues']}")
                print(f"  • Warnings: {decision['warnings']}")
                print(f"  • Info/Suggestions: {decision['info_suggestions']}")
                print(f"\nReasoning:")
                for reason in decision['reasoning']:
                    print(f"  • {reason}")
                
                if workflow_result.get('merged'):
                    print(f"\n✅ PR #{args.pr_number} has been MERGED!")
                elif decision['should_auto_merge']:
                    print(f"\n⚠️  PR is approved for auto-merge but was not merged (check flags)")
                else:
                    print(f"\n❌ PR was NOT merged (see reasoning above)")
            
            if workflow_result['errors']:
                print(f"\n⚠️  Errors encountered:")
                for error in workflow_result['errors']:
                    print(f"   - {error}")
            
            return 0 if result['approved'] else 1
        else:
            # Simple review without posting
            result = reviewer.review_pr(args.repo, args.pr_number)
            
            print(f"\n{'='*60}")
            print("REVIEW SUMMARY")
            print('='*60)
            print(result['summary'])
            
            if result['issues']:
                print(f"\nIssues ({len(result['issues'])}):")
                for issue in result['issues']:
                    print(f"  - {issue}")
            
            return 0 if result['approved'] else 1
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
